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
        # --- 前処理 ---
        phase_df = utils.read_csv_from_gcs(request.data_path, encoding="utf-8")
        messages_list = utils.make_judge_input_list(phase_df)
        element_list = ["energy", "mind", "nature", "tactics"]

        # --- 個別処理を 1 タスクにまとめる ---
        async def process_one(idx: int, element: str):
            """
            i)   Gemma judge
            ii)  Gemini fallback（必要なとき）
            iii) Report 生成
            戻り値: dict を返し、エラーなら raise
            """
            proc = judge_and_make_report(
                messages=messages_list[idx],
                element=element,
                config_path="config.yaml",
            )

            # 1) Gemma 判定（同期コード → スレッドオフロード）
            judge, ok = await proc.gemma_judge_batch_async()

            # 2) Gemini フォールバック
            if not ok:
                judge = await proc.gemini_judge_async()

            if judge is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Gemini judge failed for element: {element}",
                )

            report, pred_label = await proc.make_report_async(judge, ok)

            return {
                "element": proc.element_name,
                "report": report,
                "pred_label": pred_label,
                "gemma_judge": proc.judge,
                "gemma_success": ok,
            }

        # --- タスクを起動 ---
        tasks = [
            asyncio.create_task(process_one(i, el)) for i, el in enumerate(element_list)
        ]

        # --- 完了した順にストリーム送信 ---
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                yield json.dumps(result, ensure_ascii=False) + "\n"
            except Exception as e:
                logger.error(f"stream item failed: {e}")
                err = {"error": "処理中に問題が発生しました"}
                yield json.dumps(err, ensure_ascii=False) + "\n"

    # text/event-stream でも可。ここでは NDJSON を維持
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
