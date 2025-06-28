from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import asyncio

# from main import judge_and_make_report
from .main import judge_and_make_report
from . import utils
from logging import getLogger

logger = getLogger(__name__)

app = FastAPI(
    title="judge and make report API",
    description="Gemma/Geminiを使って性格診断とレポートの生成を行うAPI",
    version="1.0.0",
)


class ReportRequest(BaseModel):
    data_path: str = Field(..., description="GCS上のデータパス")


class StreamResponse(BaseModel):
    element: str
    report: str
    gemma_judge: str
    gemma_success: bool


@app.post("/generate-report-stream-batch")
async def judge_and_make_report_app(request: ReportRequest):
    async def stream_generator():
        phase_df = utils.read_csv_from_gcs(request.data_path, encoding="utf-8")
        messages_list = utils.make_judge_input_list(phase_df)
        element_list = ["energy", "mind", "nature", "tactics"]

        # ---------- ターン 1: Processor を全部作る ----------
        processors = [
            judge_and_make_report(
                messages=messages_list[i],
                element=el,
                config_path="config.yaml",
            )
            for i, el in enumerate(element_list)
        ]

        # ---------- ターン 2: Gemma をバッチ推論 ----------
        try:
            gemma_success_flags = judge_and_make_report.gemma_judge_batch(processors)
        except Exception as e:
            logger.error(f"Batch Gemma failed: {e}")
            gemma_success_flags = [False] * len(processors)

        # ---------- ターン 3: Gemini フォールバック → レポート生成 ----------
        for proc, ok in zip(processors, gemma_success_flags):
            try:
                # フォールバック
                if not ok:
                    proc.gemini_judge()
                # レポート
                report = proc.make_report()

                response_chunk = StreamResponse(
                    element=proc.element_name,
                    report=report,
                    gemma_judge=proc.judge,
                    gemma_success=ok,
                ).model_dump_json()

                yield response_chunk + "\n"
                await asyncio.sleep(0)

            except Exception as e:
                logger.error(f"Error on {proc.element_name}: {e}")
                yield '{"error": "処理中に問題が発生しました"}'

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@app.post("/generate-report-stream")
async def judge_and_make_report_app(request: ReportRequest):
    """
    会話履歴から診断とレポートの作成を行う
    """

    async def stream_generator():
        load_dotenv(override=True)
        if not os.getenv("GEMINI_API_KEY"):
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEYが設定されていません。.envファイルを確認してください。",
            )

        phase_df = utils.read_csv_from_gcs(request.data_path, encoding="utf-8")
        messages_list = utils.make_judge_input_list(phase_df)

        element_list = ["energy", "mind", "nature", "tactics"]
        report_list = []
        pred_labels = []

        for i, element in enumerate(element_list):
            try:
                processor = judge_and_make_report(
                    messages=messages_list[i],
                    element=element,
                    config_path="config.yaml",
                )
                # 1. judge by gemma
                try:
                    print("Attempting judgment with Gemma...")
                    is_success_gemma_judge = processor.gemma_judge()
                except Exception as e:
                    logger.error(f"Gemma judgment failed for {element}: {e}")
                    is_success_gemma_judge = False

                # 2. judge by gemma (if gemma judge return error)
                if is_success_gemma_judge:
                    print("Executing Gemini fallback judgment if needed...")
                    processor.gemini_judge()

                # 3. make report
                print("Generating final report...")
                report, pred_label = processor.make_report()
                report_list.append(report)
                pred_labels.append(pred_label)
                print(report, pred_label)

                # return the resonse
                response_chunk = StreamResponse(
                    element=element,
                    report=report,
                    pred_label=pred_label,
                    gemma_judge=processor.judge,
                    gemma_success=is_success_gemma_judge,
                ).model_dump_json()

                yield response_chunk + "\n"
                await asyncio.sleep(0)

            except Exception as e:
                logger.error(f"Error processing element {element}: {e}")
                error_json_string = '{"error": "処理中に問題が発生しました"}'
                yield error_json_string

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
