from typing import Optional, Dict, List
from logging import getLogger
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# vLLM は高速推論エンジン。GPU が無い場合は自動的に transformers にフォールバックします。
try:
    from vllm import LLM, SamplingParams
    _VLLM_AVAILABLE = True
except ImportError:
    _VLLM_AVAILABLE = False  # ランタイムに vllm が入っていない場合も考慮

logger = getLogger(__name__)


class GPUModelManager:
    """vLLM + bitsandbytes を用いた GPU 最適化モデル管理クラス（シングルトン）"""

    _instances: Dict[str, "GPUModelManager"] = {}

    def __new__(cls, model_name: str):
        if model_name not in cls._instances:
            cls._instances[model_name] = super().__new__(cls)
        return cls._instances[model_name]

    def __init__(self, model_name: str):
        # すでに __init__ が完了している場合は何もしない
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # vLLM 用
        self.llm: Optional["LLM"] = None

        # transformers 用
        self.model: Optional["AutoModelForCausalLM"] = None
        self.tokenizer: Optional["AutoTokenizer"] = None

        self._initialized: bool = False

    # ------------------------------------------------------
    # モデルロード
    # ------------------------------------------------------
    def load_model(
        self,
        gpu_memory_utilization: float = 0.6,
        dtype: torch.dtype = torch.bfloat16,
        quantization: Optional[str] = "bitsandbytes",  # "awq" 等も指定可 (vllm>=0.4)
        use_double_quant: bool = True,
    ) -> bool:
        """モデルをロードする。

        * CUDA が利用可能 & vLLM 単体が import 出来る場合 → vLLM 経由でロード
        * それ以外 → transformers + bitsandbytes で CPU フォールバック
        """
        if self._initialized:
            logger.info(f"Model {self.model_name} already loaded; skip reloading")
            return True

        try:
            # ---------------- GPU / vLLM ----------------
            if self.device == "cuda" and _VLLM_AVAILABLE:
                logger.info(
                    f"Loading {self.model_name} with vLLM (quantization={quantization}, dtype={dtype})"
                )
                # vLLM が bitsandbytes 4bit 量子化を直接サポート
                self.llm = LLM(
                    model=self.model_name,
                    tokenizer=self.model_name,
                    dtype=dtype,
                    gpu_memory_utilization=gpu_memory_utilization,
                    quantization=quantization,
                    trust_remote_code=True,
                )
                self.tokenizer = self.llm.get_tokenizer()

            # -------------- CPU / transformers --------------
            else:
                logger.info(
                    f"Loading {self.model_name} on {self.device} via transformers (float32)"
                )

                quant_config = BitsAndBytesConfig(
                   load_in_4bit=True,
                   bnb_4bit_quant_type="nf4",
                   bnb_4bit_compute_dtype=torch.bfloat16,
                   bnb_4bit_use_double_quant=use_double_quant,
                )

                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    local_files_only=True,
                    device_map="auto",
                    torch_dtype=torch.float32,
                    quantization_config=quant_config,
                    low_cpu_mem_usage=True,
                )
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, local_files_only=True
                )

            self._initialized = True
            logger.info(f"Model {self.model_name} loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            return False

    # ------------------------------------------------------
    # 推論
    # ------------------------------------------------------
    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.95,
    ) -> str:
        """テキスト生成（GPU: vLLM, CPU: transformers）"""
        if not self._initialized:
            raise RuntimeError("Model not loaded; call load_model() first")

        # ----------- vLLM パス (GPU) -----------
        if self.llm is not None:
            sampling_params = SamplingParams(
                max_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=None,
            )
            outputs = self.llm.generate([prompt], sampling_params=sampling_params)
            # vLLM は List[vllm.outputs.Batch] を返す → 1番目の出力を返す
            return outputs[0].outputs[0].text

        # ----------- transformers パス (CPU) -----------
        assert self.model is not None and self.tokenizer is not None, "CPU fallback should have model/tokenizer"

        inputs = self.tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            generated = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        prompt_len = inputs["input_ids"].shape[-1]
        new_tokens = generated[0][prompt_len:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=False)
