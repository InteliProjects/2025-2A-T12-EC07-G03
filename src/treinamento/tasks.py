import os
import time
from .celery_app import celery_app
from .database import SessionLocal
from .models import TrainingJob, ProcessedData
from .ModelFactory import ModelFactory
from sqlalchemy import create_engine

@celery_app.task
def run_training_task(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(TrainingJob).filter(TrainingJob.id == job_id).first()
        if not job:
            return
        
        machines_available = db.query(ProcessedData.motor_pump).distinct().all()
        machines_available = [m[0] for m in machines_available]
        if job.machine_name not in machines_available:
            job.status = "failed"
            job.error_message = f"Machine '{job.machine_name}' not found in processed data."
            db.commit()
            return

        # atualiza status para running
        job.status = "running"
        db.commit()

        # executa o treinamento
        minio_config = {
            "endpoint": os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            "access_key": os.getenv("MINIO_ACCESS_KEY", "NMNDA6VENQ11BZYLX7PY"),
            "secret_key": os.getenv("MINIO_SECRET_KEY", "CkF5MX19EDcqDiXqMAgO8VL2KLTKSo1v7mPe+B+X")
        }

        engine = create_engine(os.getenv("DATABASE_URL", "postgresql+psycopg2://admin:admin123@localhost:5432/SyncTelemetry"))

        factory = ModelFactory(minio_config, engine)
        if job.indicator == "status":
            result = factory.train_model('xgboost', job.machine_name, job.start_date, job.end_date)

        elif job.indicator == "health":
            result = factory.train_model('gru', job.machine_name, job.start_date, job.end_date)
        
        # finaliza com sucesso
        job.status = "finished"
        job.bucket_address = result["bucket_address"]
        job.finished_at = job.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        db.commit()
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()
