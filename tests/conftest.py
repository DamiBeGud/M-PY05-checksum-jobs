import os
os.environ['CELERY_BROKER_URL']='redis://127.0.0.1:9/0'
os.environ['CELERY_RESULT_BACKEND']='redis://127.0.0.1:9/1'
os.environ['QUEUE_NAMESPACE']='synthetic-unit'
os.environ['API_TOKEN']='synthetic-unit-token'
