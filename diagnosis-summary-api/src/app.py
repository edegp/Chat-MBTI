from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import json
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
    pred_label: str
    gemma_judge: str
    gemma_success: bool


@app.post("/generate-report-stream-batch")
async def generate_report_stream(request: ReportRequest):
    async def stream_generator():
        # --- 0) 前処理 ---
        phase_df = utils.read_csv_from_gcs(request.data_path, encoding="utf-8")
        element_list = ["energy", "mind", "nature", "tactics"]
        messages_list = utils.make_judge_input_list(phase_df)

        # --- 1) Processor 生成（4 個固定） ---
        processors = [
            judge_and_make_report(
                messages=messages_list[i],
                element=element,
                config_path="config.yaml",
            )
            for i, element in enumerate(element_list)
        ]

        # --- 2) Gemma を 1 バッチ推論（非同期オフロード）---
        gemma_flags = await judge_and_make_report.gemma_judge_batch_async(processors)
        # gemma_flags[i] == True ならフォーマット OK

        # --- 3) Gemini フォールバック + レポートを並列実行 ---
        async def post_process(proc, ok):
            if not ok:
                await proc.gemini_judge_async()
            report, pred = await proc.make_report_async()
            return dict(
                element=proc.element_name,
                report=report,
                pred_label=pred,
                gemma_judge=proc.judge,
                gemma_success=ok,
            )

        tasks = [
            asyncio.create_task(post_process(p, ok))
            for p, ok in zip(processors, gemma_flags)
        ]

        # --- 4) ストリーム送信 ---
        for coro in asyncio.as_completed(tasks):  # ← 終わった順に送る
            try:
                result = await coro
                yield json.dumps(result, ensure_ascii=False) + "\n"
            except Exception as e:
                logger.error(f"item failed: {e}")
                yield json.dumps({"error": "処理中に問題が発生しました"}) + "\n"

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
                    judge, is_success_gemma_judge = processor.gemma_judge()
                except Exception as e:
                    logger.error(f"Gemma judgment failed for {element}: {e}")
                    is_success_gemma_judge = False

                # 2. judge by gemma (if gemma judge return error)
                if not is_success_gemma_judge:
                    print("Executing Gemini fallback judgment if needed...")
                    judge = processor.gemini_judge()

                # 3. make report
                print("Generating final report...")
                report, pred_label = processor.make_report(
                    judge, is_success_gemma_judge
                )
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
