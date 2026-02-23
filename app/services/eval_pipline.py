from app.rag.evaluation.eval_pipline import EvalPipeline
from pathlib import Path
from app.celery.celery_config import celery_app
import mlflow
from datetime import datetime
from mlflow.tracking import MlflowClient

@celery_app.task(bind=True,
                 auto_retry_for=(Exception,),
                 retry_kwargs={'max_retries': 3, 'countdown': 30},
                 retry_backoff=True,
                 retry_jitter=True,
                 name="app.services.eval_rag_service.evaluate_task"
                )
def evaluate_task(self, tenant_id: str, path: str, runs: int = 2, run_id: str = None):
    # متغير نتتبعه إذا كنا بنحاول retry
    retry_count = getattr(self, 'request', {}).get('retries', 0)
    
    try:
        if run_id:
            # في حالة retry، نستخدم run_id ولكن بدون تسجيل parameters مكررة
            with mlflow.start_run(run_id=run_id):
                
                # نسجل start_time مرة واحدة فقط (لو مش موجود)
                client = MlflowClient()
                run = client.get_run(run_id)
                
                # التحقق من إن الـ parameters مش مسجلة قبل كده
                if "start_time" not in run.data.params:
                    start_time = datetime.utcnow().isoformat()
                    mlflow.log_param("start_time", start_time)
                else:
                    # لو موجود، نستخدمه أو نسجله كـ tag
                    start_time = run.data.params["start_time"]
                    mlflow.set_tag("retry_start_time", datetime.utcnow().isoformat())
                
                # نسجل محاولة retry
                if retry_count > 0:
                    mlflow.set_tag(f"retry_{retry_count}_attempt", datetime.utcnow().isoformat())
                
                mlflow.set_tag("status", "Evaluation in progress")
                
                pipeline = EvalPipeline(path=Path(path), tenant_id=tenant_id)
                results = pipeline.evaluate(runs=runs)
                
                end_time = datetime.utcnow().isoformat()
                
                # حساب الوقت المستغرق
                start_dt = datetime.fromisoformat(start_time)
                end_dt = datetime.fromisoformat(end_time)
                total_seconds = (end_dt - start_dt).total_seconds()
                
                # نسجل parameters جديدة (مش مكررة)
                if "end_time" not in run.data.params:
                    mlflow.log_param("end_time", end_time)
                else:
                    mlflow.set_tag("retry_end_time", end_time)
                
                if "total_time_seconds" not in run.data.params:
                    mlflow.log_param("total_time_seconds", total_seconds)
                else:
                    mlflow.set_tag(f"retry_{retry_count}_total_time", total_seconds)
                
                mlflow.log_dict(results, artifact_file="results.json")
                mlflow.set_tag("status", "Evaluation completed")
                mlflow.set_tag("success", "true")
                
                return results
                
    except Exception as e:
        try:
            # نسجل الخطأ باستخدام tags مش parameters
            with mlflow.start_run(run_id=run_id):
                mlflow.set_tag("status", "Evaluation failed")
                mlflow.set_tag(f"error_{retry_count}", str(e))
                mlflow.set_tag(f"error_time_{retry_count}", datetime.utcnow().isoformat())
                
                # نسجل أن في retry
                if retry_count < 3:  # max_retries من الإعدادات
                    mlflow.set_tag("will_retry", "true")
                    mlflow.set_tag(f"retry_reason_{retry_count}", str(e)[:100])  # مختصر
        except:
            # لو فشل تسجيل الخطأ، نكمل عادي
            pass
        
        # إعادة المحاولة
        self.retry(exc=e)