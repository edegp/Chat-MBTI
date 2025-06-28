from . import utils

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from typing import Optional, Dict

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from logging import getLogger
from transformers.integrations.bitsandbytes import validate_bnb_backend_availability

logger = getLogger(__name__)

validate_bnb_backend_availability(raise_exception=True)


class GPUModelManager:
    """GPU最適化されたモデル管理クラス（シングルトンパターン）"""

    _instances: Dict[str, "GPUModelManager"] = {}

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
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                local_files_only=True,
            )

            if self.device == "cuda":
                # GPU用量子化設定
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=use_double_quant,  # 設定可能
                )

                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.bfloat16,
                    quantization_config=quantization_config,
                    device_map="auto",
                    local_files_only=True,
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
            return False

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


class judge_and_make_report:
    def __init__(self, messages, element, config_path):
        self.config = utils.load_config(config_path)
        self.model_name = self.config[element]["model_name"]
        self.element_name = self.config[element]["element_name"]
        self.element_description = self.config[element]["element_description"]
        self.label = self.config[element]["label"]
        self.true_labels = self.config[element]["true_labels"]

        self.messages = messages

        # シングルトンパターンでモデル管理
        self.model_manager = GPUModelManager(self.model_name)

        # Gemini初期化
        load_dotenv(override=True)
        api_key = os.getenv("GEMINI_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=1,
            max_tokens=2024,
            timeout=None,
            max_retries=2,
            api_key=api_key,
        )

    def gemma_judge(self, message_max_length=2000):
        """GPU最適化されたGemma推論"""
        prompt = utils.preprocess(
            self.messages,
            self.element_name,
            self.element_description,
            self.label,
            message_max_length,
        )

        try:
            # モデル読み込み（既にロード済みなら即座に返す）
            if not self.model_manager.load_model(use_double_quant=True):
                raise RuntimeError("Failed to load model")

            # 推論実行
            response = self.model_manager.generate(prompt)
            response = utils.remove_special_token(response)

            self.judge = response

            # フォーマット検証
            follow_format, format_error = utils.judge_response_follow_format(
                response, true_labels=self.true_labels
            )

            if not follow_format:
                logger.warning(f"Response does not follow format: {format_error}")
                return False
            return True
        except Exception as e:
            logger.error(f"[gemma_judge] Error during model inference: {e}")
            return False

    def gemini_judge(self, message_max_length=2000):
        """Gemini推論（フォールバック）"""

        prompt = utils.preprocess(
            self.messages,
            self.element_name,
            self.element_description,
            self.label,
            message_max_length,
        )

        try:
            judge = self.llm.invoke(prompt)
            self.judge = judge.content
        except Exception as e:
            logger.error(f"[gemini_judge] Error during API call: {e}")
            raise

    def make_report(self):
        """レポート生成"""

        prompt = utils.make_report_prompt(self.element_name, self.messages, self.judge)

        try:
            report = self.llm.invoke(prompt)
            self.report = report.content
            return self.report
        except Exception as e:
            logger.error(f"[make_report] Error during report generation: {e}")
            raise
