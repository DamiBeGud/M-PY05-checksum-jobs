from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict, StrictInt

import os,hmac,hashlib
from uuid import UUID
from fastapi import Header,Depends
from .worker import celery,process
class Job(BaseModel):
    reference:str=Field(min_length=1,max_length=64,pattern=r'^[A-Za-z0-9-]+$')
    text:str=Field(min_length=1,max_length=10000)
def authenticate(authorization:str|None=Header(default=None)):
    expected=os.environ.get("API_TOKEN")
    if not expected:raise HTTPException(503,"token_unconfigured")
    if not authorization or not authorization.startswith("Bearer ") or not hmac.compare_digest(hashlib.sha256(authorization[7:].encode()).digest(),hashlib.sha256(expected.encode()).digest()):raise HTTPException(401,"unauthorized")
def create_app():
    app=FastAPI(title='checksum-jobs')
    @app.get('/health/live')
    def live():return {'status':'ok'}
    @app.get('/health/ready')
    @app.get('/ready')
    def ready():
        from redis import Redis
        try:
            for key in ['CELERY_BROKER_URL','CELERY_RESULT_BACKEND']:
                with Redis.from_url(os.environ[key],socket_connect_timeout=0.5,socket_timeout=0.5) as client:
                    if client.ping() is not True:raise ValueError()
        except Exception:raise HTTPException(503,'dependency_unavailable') from None
        return {'status':'ready'}
    @app.post('/jobs',status_code=202,dependencies=[Depends(authenticate)])
    def submit(p:Job):
        try:task=process.apply_async(args=[p.reference,p.text])
        except Exception:raise HTTPException(503,'queue_unavailable') from None
        return {'job_id':task.id}
    @app.get('/jobs/{job_id}',dependencies=[Depends(authenticate)])
    def result(job_id:UUID):
        try:
            task=celery.AsyncResult(str(job_id));state=task.state
            result=task.result if state=='SUCCESS' else None
        except Exception:raise HTTPException(503,'backend_unavailable') from None
        return {'job_id':str(job_id),'state':state,'result':result}
    return app
app=create_app()
