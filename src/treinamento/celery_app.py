from celery import Celery
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "training_service",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# garante que as tasks sejam registradas
celery_app.conf.update(
    task_routes={
        "treinamento.tasks.*": {"queue": "training_queue"},
    }
)

import treinamento.tasks
