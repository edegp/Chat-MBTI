from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import asyncio

# from main import judge_and_make_report
from . import main
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
    gemma_judge: str | None
    gemma_success: bool


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

        for i, element in enumerate(element_list):
            try:
                processor = main.judge_and_make_report(
                    messages=messages_list[i],
                    element=element,
                    config_path="config.yaml",
                )
                # 1. judge by gemma
                print("Attempting judgment with Gemma...")
                is_success_gemma_judge = processor.gemma_judge()

                # 2. judge by gemma (if gemma judge return error)
                if is_success_gemma_judge:
                    print("Executing Gemini fallback judgment if needed...")
                    processor.gemini_judge()

                # 3. make report
                print("Generating final report...")
                report = processor.make_report()
                report_list.append(report)
                print(report)

                # return the resonse
                response_chunk = StreamResponse(
                    element=element,
                    report=report,
                    gemma_judge=getattr(processor, "gemma_judge", None),
                    gemma_success=processor.gemma_judge_success_flag,
                ).model_dump_json()

                yield response_chunk + "\n"
                await asyncio.sleep(0)

            except Exception as e:
                logger.error(f"Error processing element {element}: {e}")
                error_json_string = '{"error": "処理中に問題が発生しました"}'
                yield error_json_string

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
