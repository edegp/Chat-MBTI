from . import utils

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import gc

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch
from logging import getLogger

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

        self.gemma_judge_success_flag = True

        # load gemini
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
        prompt = utils.preprocess(
            self.messages,
            self.element_name,
            self.element_description,
            self.label,
            message_max_length,
        )
        model = None
        tokenizer = None

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            # NOTE: gemmaのパラメータ保管場所が確定したら、そこから読み込む形式に変更
            # load model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
            )

            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.bfloat16,
                quantization_config=quantization_config,
                device_map="cuda",
            )

            # make llm input
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

            # generate response
            generated_tokens_0 = model.generate(
                input_ids=inputs["input_ids"], max_new_tokens=512, temperature=0.1
            )

            # decode
            prompt_len = inputs["input_ids"].shape[-1]
            new_tokens = generated_tokens_0[0][prompt_len:]
            response = tokenizer.decode(new_tokens)
            response = utils.remove_special_token(response)

            self.gemma_judge = response

            # judge response
            follow_format, format_error = utils.judge_response_follow_format(
                response, true_labels=self.true_labels
            )

            if not follow_format:
                print(f"Response does not follow format: {format_error}")
                self.gemma_judge_success_flag = False

        except Exception as e:
            print(f"[gemma_judge] Error during model inference: {e}")
            self.gemma_judge_success_flag = False

        # clean memory
        finally:
            if model is not None:
                del model
            if tokenizer is not None:
                del tokenizer

            gc.collect()

            # clear cuda cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def gemini_judge(self, message_max_length=2000):
        prompt = utils.preprocess(
            self.messages,
            self.element_name,
            self.element_description,
            self.label,
            message_max_length,
        )

        if self.gemma_judge_success_flag == True:
            pass
        else:
            judge = self.llm.invoke(prompt)
            self.gemini_judge = judge.content

    def make_report(self):
        if self.gemma_judge_success_flag == True:
            judge = self.gemma_judge
        else:
            judge = self.gemini_judge

        prompt = utils.make_report_prompt(self.element_name, self.messages, judge)
        report = self.llm.invoke(prompt)

        self.report = report.content
        return self.report
