import asyncio
import functools
import torch
import traceback
from typing import Optional, Dict
from logging import getLogger
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from concurrent.futures import ThreadPoolExecutor
import transformers
from vllm import LLM, SamplingParams

logger = getLogger(__name__)

transformers.utils.logging.set_verbosity_debug()


class GPUModelManager:
    """GPU最適化されたモデル管理クラス（シングルトンパターン）"""

    _instances: Dict[str, "GPUModelManager"] = {}
    _executor = ThreadPoolExecutor(max_workers=4)  # ★共有スレッドプール
    _semaphore: asyncio.Semaphore | None = None
    _locks: Dict[str, asyncio.Lock] = {}  # モデルごとにロック

    @classmethod
    def _get_semaphore(cls, parallel=4) -> asyncio.Semaphore:
        if cls._semaphore is None:
            cls._semaphore = asyncio.Semaphore(parallel)
        return cls._semaphore

    def __new__(cls, model_name: str):
        return cls._instances.setdefault(model_name, super().__new__(cls))

    @classmethod
    def _get_lock(cls, model_name: str) -> asyncio.Lock:
        if model_name not in cls._locks:
            cls._locks[model_name] = asyncio.Lock()
        return cls._locks[model_name]

    def __init__(self, model_name: str):
        if getattr(self, "initialized", False):
            return  # すでに初期化済み

        self.model_name = model_name
        self.model: Optional[AutoModelForCausalLM] = None
        self.tokenizer: Optional[AutoTokenizer] = None
        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "mps"
            if torch.backends.mps.is_available()
            else "cpu"
        )
        self.initialized = False

    # ---------- 同期メソッド：実際のロード ----------

    def _load_sync(self, use_double_quant: bool = True) -> bool:
        try:
            logger.info(f"[{self.model_name}] loading on {self.device}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            if self.device == "cuda":
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.bfloat16,
                    quantization_config=BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_compute_dtype=torch.bfloat16,
                        bnb_4bit_use_double_quant=use_double_quant,
                    ),
                    device_map={"": "cuda:0"},
                    low_cpu_mem_usage=True,
                )
            elif self.device == "mps":
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.bfloat16,
                    device_map={"": "mps"},
                    low_cpu_mem_usage=True,
                )
            else:  # CPU fallback
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    device_map="auto",
                    cache_dir="/workspace",
                    local_files_only=True,
                )

            self.model.eval()
            self.initialized = True
            logger.info(f"[{self.model_name}] loaded successfully")
            return True

        except Exception as e:
            logger.error(f"[{self.model_name}] load failed: {e}")
            traceback.print_exc()
            return False

    # -----------------------------------------------

    # ---------- 非同期 API：呼び出し口 ----------

    async def load_model(self, use_double_quant: bool = True) -> bool:
        # 既にロード済みなら即返す
        if self.initialized:
            return True

        # ★ 同時ロード本数を全体で制限
        async with self._get_semaphore():
            lock = self._get_lock(self.model_name)
            async with lock:
                if self.initialized:  # ← ダブルチェック
                    return True

                loop = asyncio.get_running_loop()
                fn = functools.partial(self._load_sync, use_double_quant)
                return await loop.run_in_executor(self._executor, fn)

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

    # def _load_sync(
    #     self,
    #     tensor_parallel_size: int = 1,
    #     dtype: str = "bfloat16",
    #     gpu_memory_utilization: float = 0.80,
    #     quantization: Optional[str] = "bitsandbytes",
    # ) -> bool:
    #     """
    #     vLLM の LLM クラスを初期化してモデルをロードする。

    #     Args:
    #         tensor_parallel_size: マルチ GPU 使用時の並列数
    #         dtype: "bfloat16" / "float16" / "float32" など
    #         gpu_memory_utilization: GPU メモリ使用率の上限（0.0–1.0）
    #         quantization: "gptq" / "awq" などを指定すると量子化モデルをロード
    #     """
    #     try:
    #         logger.info(f"[{self.model_name}] loading with vLLM…")
    #         self.llm = LLM(
    #             model=self.model_name,
    #             dtype=dtype,
    #             tensor_parallel_size=tensor_parallel_size,
    #             gpu_memory_utilization=gpu_memory_utilization,
    #             quantization=quantization,
    #             task="generate",
    #             swap_space=4,
    #             # trust_remote_code=True,  # HF repo 側の独自コードに対応
    #         )
    #         # tokenizer は llm 内部で管理される
    #         self.initialized = True
    #         logger.info(f"[{self.model_name}] loaded successfully")
    #         return True

    #     except Exception as e:
    #         logger.exception(f"[{self.model_name}] load failed: {e}")
    #         return False

    # def _generate_sync(
    #     self,
    #     prompt: str,
    #     max_new_tokens: int = 512,
    #     temperature: float = 0.1,
    #     top_p: float = 0.95,
    # ) -> str:
    #     """
    #     ブロッキングな推論メソッド。内部使用。
    #     """
    #     if not self.initialized or self.llm is None:
    #         raise RuntimeError("Model not loaded")

    #     params = SamplingParams(
    #         temperature=temperature,
    #         top_p=top_p,
    #         max_tokens=max_new_tokens,
    #     )

    #     outputs = self.llm.generate(prompt, params)
    #     return outputs[0].outputs[0].text  # 1 prompt 想定

    # async def generate_async(
    #     self,
    #     prompt: str,
    #     max_new_tokens: int = 512,
    #     temperature: float = 0.1,
    #     top_p: float = 0.95,
    # ) -> str:
    #     """
    #     非同期推論メソッド。

    #     Example:
    #         manager = GPUModelManagerVLLM("meta-llama/Meta-Llama-3-8B-Instruct")
    #         await manager.load_model()
    #         result = await manager.generate_async("こんにちは！")
    #     """
    #     if not self.initialized:
    #         raise RuntimeError("Model not loaded. Call load_model() first.")

    #     async with self._get_semaphore():
    #         loop = asyncio.get_running_loop()
    #         fn = functools.partial(
    #             self._generate_sync,
    #             prompt,
    #             max_new_tokens,
    #             temperature,
    #             top_p,
    #         )
    #         return await loop.run_in_executor(self._executor, fn)
