from celery import Celery

# Configure Celery to use Redis as the broker
celery = Celery(
    "lab_results", 
    broker="redis://redis:6379/0",  # Redis connection URL
    backend="redis://redis:6379/0"
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)
