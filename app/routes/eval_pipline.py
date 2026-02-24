from app.services.rag_services.eval_pipline import evaluate_task

import mlflow
import os

from fastapi import APIRouter, UploadFile, File, Form
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from app.schema.query_request import QueryRequest
from app.rag.retrivel_data_pipline import RetrievalPipeline # تأكد من مسار الكلاس بتاعك


router = APIRouter(
    prefix="/eval",
)

# Endpoint to start the evaluation task
@router.post("/evaluate")
async def evaluate(
    tenant_id: str = Form(...),
    file: UploadFile = File(...),
    runs: int = Form(2)
):
    mlflow.set_experiment("RAG_Evaluation")
    
    # open run context to log parameters and artifacts before starting the async task
    with mlflow.start_run(run_name=f"eval_run_{tenant_id}") as active_run:
        run_id = active_run.info.run_id
        
        mlflow.log_param("tenant_id", tenant_id)
        mlflow.log_param("runs", runs)

        upload_dir = Path("/atlas-ai/app/files/eval_files")
        upload_dir.mkdir(parents=True, exist_ok=True)

        temp_file_path = upload_dir / file.filename
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        mlflow.log_artifact(temp_file_path, artifact_path="evaluation_dataset")

        # send the task to Celery with the run_id for tracking
        task = evaluate_task.delay(
            tenant_id=tenant_id, 
            path=str(temp_file_path), 
            runs=runs, 
            run_id=run_id 
        )

        return {"task_id": task.id, "run_id": run_id, "status": "Evaluation started"}
    

# Endpoint to check the status of the evaluation task
@router.get("/status/{task_id}")
async def get_status(task_id: str):
    from app.celery.celery_config import celery_app
    task_result = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status}


@router.post("/ask")
async def ask_question(request: QueryRequest):
    '''
    Endpoints that returns the answer with streaming
    '''

    try :
        pipeline = RetrievalPipeline(tenant_id="1234") # HardCoded For now
        answer = pipeline.ask_stream(query=request.query)
        
        return StreamingResponse(answer, media_type="text/plain")
    
    except Exception as e :
         raise HTTPException(status_code=500, detail=str(e))