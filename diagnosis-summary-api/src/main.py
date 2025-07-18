import re
from typing import Tuple
import asyncio
from . import utils

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
from logging import getLogger
from .gpu_model_manager_vllm import GPUModelManager

logger = getLogger(__name__)


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

    def build_gemma_prompt(self, message_max_length=2000) -> str:
        """Gemma 用プロンプトだけ返す（推論はしない）"""
        return utils.preprocess(
            self.messages,
            self.element_name,
            self.element_description,
            self.label,
            message_max_length,
        )

    async def gemma_judge_async(self) -> Tuple[str, bool]:
        # 2) 推論
        raw = await self.model_manager.generate_async(self.build_gemma_prompt())

        # 3) 後処理
        cleaned = utils.remove_special_token(raw)
        self.judge = cleaned
        ok, err = utils.judge_response_follow_format(cleaned, self.true_labels)
        if not ok:
            logger.warning("%s: format error: %s", self.element_name, err)
        return cleaned, ok

    async def gemma_judge(self, message_max_length=2000):
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
            if not await self.model_manager.load_model():
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
                return None, False
            return response, True
        except Exception as e:
            logger.error(f"[gemma_judge] Error during model inference: {e}")
            return None, False

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
            return self.judge
        except Exception as e:
            logger.error(f"[gemini_judge] Error during API call: {e}")
            raise

    async def gemini_judge_async(self, message_max_length=2000):
        """Gemini推論（フォールバック）"""

        prompt = utils.preprocess(
            self.messages,
            self.element_name,
            self.element_description,
            self.label,
            message_max_length,
        )

        try:
            judge = await self.llm.ainvoke(prompt)
            self.judge = judge.content
            return self.judge
        except Exception as e:
            logger.error(f"[gemini_judge] Error during API call: {e}")
            raise

    def make_report(self, judge: str, is_success_gemma_judge: bool = True) -> str:
        """レポート生成"""

        prompt = utils.make_report_prompt(self.element_name, self.messages, judge)

        try:
            report = self.llm.invoke(prompt)
            report = report.content
            judge_pattern = re.compile(r"(?<=\[judge\])([A-Za-z])")

            # geminiの判定が正しいフォーマットに従っている場合
            try:
                m = judge_pattern.search(judge)
                pred_label = m.group(1)

            # geminiの判定が正しいフォーマットに従っていない場合
            except Exception:
                pred_label = self.true_labels[0]  # デフォルトの予測ラベルを設定
                first_match = len(judge) + 1

                for label in self.true_labels:
                    match = judge.find(label)
                    if match != -1 and match < first_match:
                        first_match = match
                        pred_label = label

            return report, pred_label
        except Exception as e:
            logger.error(f"[make_report] Error during report generation: {e}")
            raise

    async def make_report_async(
        self, judge: str, is_success_gemma_judge: bool = True
    ) -> tuple[str, str]:
        """レポート生成"""

        prompt = utils.make_report_prompt(self.element_name, self.messages, judge)

        try:
            report = await self.llm.ainvoke(prompt)
            report = report.content
            judge_pattern = re.compile(r"(?<=\[judge\])([A-Za-z])")

            # geminiの判定が正しいフォーマットに従っている場合
            try:
                m = judge_pattern.search(judge)
                pred_label = m.group(1)

            # geminiの判定が正しいフォーマットに従っていない場合
            except Exception:
                pred_label = self.true_labels[0]  # デフォルトの予測ラベルを設定
                first_match = len(judge) + 1

                for label in self.true_labels:
                    match = judge.find(label)
                    if match != -1 and match < first_match:
                        first_match = match
                        pred_label = label

            return report, pred_label
        except Exception as e:
            logger.error(f"[make_report] Error during report generation: {e}")
            raise
