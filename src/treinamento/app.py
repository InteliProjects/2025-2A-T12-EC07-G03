from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid
import datetime
from datetime import date

from .database import SessionLocal, engine
from .models import Base, TrainingJob, ProcessedData

from .tasks import run_training_task

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Training API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- MODELS ----
class TrainRequest(BaseModel):
    indicator: str ## "status" ou "health"
    machine_name: str
    start_date: date | None = None
    end_date: date | None = None
    ## Talvez outros campos necessários:
    ## use_all_data 
    ## user_email
    ## user_name

# ---- ROUTES ----
@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow()}


@app.post("/train")
def start_training(req: TrainRequest, db: Session = Depends(get_db)):
    if req.indicator not in ["status", "health"]:
        raise HTTPException(status_code=400, detail="Invalid indicator. Must be 'status' or 'health'.")
    
    if req.start_date and req.end_date and req.start_date > req.end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date.")
    
    available_machines = db.query(ProcessedData.motor_pump).distinct().all()
    available_machines = [m[0] for m in available_machines]
    if req.machine_name not in available_machines:
        raise HTTPException(status_code=400, detail=f"Machine '{req.machine_name}' not found in processed data.")
        
    job = TrainingJob(
        machine_name=req.machine_name,
        indicator=req.indicator,
        status="pending",
        start_date=req.start_date, ## 01/06/2025
        end_date=req.end_date, ## 02/06/2025
        bucket_address=None
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_training_task.apply_async(
        args=[str(job.id)],
        queue="training_queue"
    )

    return {"process_id": str(job.id), "status": job.status}

@app.get("/status/{process_id}")
def get_status(process_id: str, db: Session = Depends(get_db)):
    job = db.query(TrainingJob).filter(TrainingJob.id == process_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "process_id": str(job.id),
        "indicator": job.indicator,
        "machine_name": job.machine_name,
        "status": job.status,
        "error_message": job.error_message,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "finished_at": job.finished_at,
        "bucket_address": job.bucket_address if job.bucket_address else None
    }
