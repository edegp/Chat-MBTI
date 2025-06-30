from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os
import json
import asyncio
import time

# from main import judge_and_make_report
from .main import judge_and_make_report
from . import utils
from logging import getLogger
from .gpu_model_manager_vllm import GPUModelManager
from fastapi.middleware.cors import CORSMiddleware

logger = getLogger(__name__)

app = FastAPI(
    title="judge and make report API",
    description="Gemma/Geminiを使って性格診断とレポートの生成を行うAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # ローカル開発
        "https://mbti-diagnosis-api-47665095629.asia-northeast1.run.app",  # 本番 (必要に応じて追加)
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)


class Message(BaseModel):
    role: str = Field(
        ..., description="Role of the message (e.g., 'user', 'assistant')"
    )
    content: str = Field(..., description="Content of the message")


class ReportRequest(BaseModel):
    element_id: int = Field(
        ...,
        description="Element ID (0: energy, 1: mind, 2: nature, 3: tactics)",
    )
    messages: list[Message] = Field(
        ...,
        description="List of messages in the conversation history",
    )


class ReportStreamRequest(BaseModel):
    data_path: str = Field(
        ...,
        description="Path to the CSV file containing conversation history",
    )


class StreamResponse(BaseModel):
    element: str
    report: str
    pred_label: str
    gemma_judge: str
    gemma_success: bool


element_list = ["energy", "mind", "nature", "tactics"]

generate_report_semaphore = asyncio.Semaphore(4)


async def acquire_report_slot():
    async with generate_report_semaphore:
        yield


@app.post("/summary/generate-report", dependencies=[Depends(acquire_report_slot)])
async def generate_report(request: ReportRequest):
    async with generate_report_semaphore:
        try:
            logger.info("Received request to generate report")
            logger.debug(f"Request data: {request.json()}")

            for message in request.messages:
                if not isinstance(message, Message):
                    logger.error("Invalid message format: %s", message)
                    return json.dumps({"error": "Invalid message format"}) + "\n"

            processor = judge_and_make_report(
                messages=request.messages,
                element=element_list[request.element_id],
                config_path="config.yaml",
            )

            if not processor:
                logger.error("No processors created. Check your input data.")
                return json.dumps({"error": "No valid processors available"}) + "\n"

            if not processor.model_manager.initialized:
                if not await processor.model_manager.load_model():
                    logger.error("Failed to load model")
                    return (
                        json.dumps({"error": "モデルの読み込みに失敗しました"}) + "\n"
                    )

            judge, is_success_gemma_judge = await processor.gemma_judge_async()
            if not is_success_gemma_judge:
                await processor.gemini_judge_async()
            report, pred = await processor.make_report_async(
                judge, is_success_gemma_judge
            )

            return json.dumps(
                {
                    "element": processor.element_name,
                    "report": report,
                    "pred_label": pred,
                    "gemma_judge": processor.judge,
                    "gemma_success": is_success_gemma_judge,
                },
                ensure_ascii=False,
            )
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return json.dumps({"error": "処理中に問題が発生しました"}) + "\n"


@app.post("/summary/generate-report-stream-batch")
async def generate_report_stream(request: ReportStreamRequest):
    async def stream_generator():
        # --- 0) 前処理 ---
        phase_df = utils.read_csv_from_gcs(request.data_path, encoding="utf-8")
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

        sem = asyncio.Semaphore(2)

        async def load_with_limit(p):
            async with sem:  # ★ ここで個々のタスクが acquire
                return await p.model_manager.load_model_async()

        # gather に渡すのは “セマフォ付きラッパ” タスク
        await asyncio.gather(*(load_with_limit(p) for p in processors))

        # --- 2) Gemma を 1 バッチ推論（非同期オフロード）---
        judges, gemma_flags = await judge_and_make_report.gemma_judge_async(processors)

        # --- 3) Gemini フォールバック + レポートを並列実行 ---
        async def post_process(proc, judge, ok):
            if not ok:
                await proc.gemini_judge_async()
            report, pred = await proc.make_report_async(judge, ok)
            return dict(
                element=proc.element_name,
                report=report,
                pred_label=pred,
                gemma_judge=proc.judge,
                gemma_success=ok,
            )

        tasks = [
            asyncio.create_task(post_process(p, judge, ok))
            for p, judge, ok in zip(processors, judges, gemma_flags)
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


@app.post("/summary/generate-report-stream")
async def judge_and_make_report_app(request: ReportStreamRequest):
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
                    judge, is_success_gemma_judge = await processor.gemma_judge()
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
