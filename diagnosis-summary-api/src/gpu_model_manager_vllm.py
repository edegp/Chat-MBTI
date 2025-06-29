import asyncio
import torch
import traceback
from typing import Optional, Dict
from logging import getLogger
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from concurrent.futures import ThreadPoolExecutor
from transformers.integrations.bitsandbytes import validate_bnb_backend_availability
import transformers

logger = getLogger(__name__)

validate_bnb_backend_availability(raise_exception=True)
transformers.utils.logging.set_verbosity_debug()


class GPUModelManager:
    """GPU最適化されたモデル管理クラス（シングルトンパターン）"""

    _instances: Dict[str, "GPUModelManager"] = {}
    _executor = ThreadPoolExecutor(max_workers=4)  # ★共有スレッドプール
    _semaphore: asyncio.Semaphore | None = None

    @classmethod
    def _get_semaphore(cls, parallel=4) -> asyncio.Semaphore:
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(parallel)
        return cls._semaphore

    def __new__(cls, model_name: str):
        if model_name not in cls._instances:
            cls._instances[model_name] = super().__new__(cls)
        return cls._instances[model_name]

    def __init__(self, model_name: str):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.model_name = model_name
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False

    def load_model(self, use_double_quant: bool = True) -> bool:
        """GPU最適化されたモデル読み込み"""
        if self.model is not None and self.tokenizer is not None:
            logger.info(f"Model {self.model_name} already loaded")
            return True

        try:
            logger.info(f"Loading model {self.model_name} on device: {self.device}")

            # トークナイザーの読み込み
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            if self.device == "cuda":
                # GPU用量子化設定
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.bfloat16,
                    quantization_config=BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_use_double_quant=use_double_quant,  # 設定可能
                    ),
                    device_map={"": "cuda:0"},
                    low_cpu_mem_usage=True,
                )
            else:
                # CPU フォールバック
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    cache_dir="/workspace",
                    local_files_only=True,
                )

            self.model.eval()
            self.initialized = True
            logger.info(f"Model {self.model_name} loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            traceback.print_exc()
            return False

    async def load_model_async(self):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.load_model)

    def generate(
        self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.1
    ) -> str:
        """最適化された推論実行"""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")

        inputs = self.tokenizer(prompt, return_tensors="pt")

        if self.device == "cuda":
            inputs = inputs.to("cuda")

        with torch.no_grad():
            generated_tokens = self.model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
                use_cache=True,
            )

        prompt_len = inputs["input_ids"].shape[-1]
        new_tokens = generated_tokens[0][prompt_len:]
        response = self.tokenizer.decode(new_tokens, skip_special_tokens=False)

        return response

    def _generate_sync(
        self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.1
    ) -> str:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model not loaded")

        with torch.inference_mode():
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True,
            )
            resp = self.tokenizer.decode(
                outputs[0, inputs["input_ids"].shape[-1] :], skip_special_tokens=True
            )
        return resp

    # ★★ 非同期ラッパ ★★
    async def generate_async(
        self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.1
    ) -> str:
        async with self._get_semaphore():
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self._executor,
                self._generate_sync,
                prompt,
                max_new_tokens,
                temperature,
            )
