import traceback
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
from fastapi.middleware.cors import CORSMiddleware

logger = getLogger(__name__)

app = FastAPI(
    title="judge and make report API",
    description="Gemma/Geminiを使って性格診断とレポートの生成を行うAPI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


class StartUpRequest(BaseModel):
    element_id: int = Field(
        ...,
        description="Element ID to initialize (0: energy, 1: mind, 2: nature, 3: tactics)",
    )


@app.post("/summary/startup")
async def startup_event(request: StartUpRequest):
    async with generate_report_semaphore:
        preprocessor = judge_and_make_report(
            messages=[],
            element=element_list[request.element_id],
            config_path="config.yaml",
        )
        if not preprocessor.model_manager.initialized:
            if not await preprocessor.model_manager.load_model():
                logger.error("Failed to load model during startup")
                return JSONResponse(
                    status_code=500,
                    content={"error": "モデルの初期化に失敗しました"},
                )
        logger.info(
            f"Startup completed for element: {element_list[request.element_id]}"
        )
        if request.element_id != 3:
            await asyncio.sleep(15)  # Allow other tasks to run
        return JSONResponse(
            status_code=200,
            content={"message": "Startup completed successfully"},
        )


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
                    return JSONResponse(
                        status_code=400, content={"error": "Invalid message format"}
                    )
            processor = judge_and_make_report(
                messages=request.messages,
                element=element_list[request.element_id],
                config_path="config.yaml",
            )

            if not processor:
                logger.error("No processors created. Check your input data.")
                return JSONResponse(
                    status_code=400, content={"error": "No valid processors available"}
                )

            # if not processor.model_manager.initialized:
            #     if not await processor.model_manager.load_model():
            #         logger.error("Failed to load model")

            # judge, is_success_gemma_judge = await processor.gemma_judge_async()
            # if not is_success_gemma_judge:
            judge = await processor.gemini_judge_async()

            if judge is None:
                logger.error("Gemma/Gemini judgment failed")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Gemma/Gemini judgment failed"},
                )
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
            traceback.print_exc()
            logger.error(f"Error generating report: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "レポートの生成中にエラーが発生しました"},
            )
