import os,re,hashlib
from collections import Counter
from celery import Celery
namespace=os.environ['QUEUE_NAMESPACE']
if not re.fullmatch(r'[a-z][a-z0-9-]{0,62}',namespace):raise ValueError('invalid_QUEUE_NAMESPACE')
celery=Celery('checksum_jobs',broker=os.environ['CELERY_BROKER_URL'],backend=os.environ['CELERY_RESULT_BACKEND'])
celery.conf.update(task_serializer='json',result_serializer='json',accept_content=['json'],
    task_default_queue=namespace+'.jobs',task_default_exchange=namespace+'.jobs',task_default_routing_key=namespace+'.jobs',
    broker_transport_options={'global_keyprefix':namespace+':','socket_connect_timeout':1,'socket_timeout':1},
    result_backend_transport_options={'global_keyprefix':namespace+':','retry_policy':{'timeout':2}},
    broker_connection_retry_on_startup=False,task_publish_retry=False,result_expires=3600)
def transform(reference,text):
    return {"reference":reference,"sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),"byte_length":len(text.encode("utf-8"))}
@celery.task(name='checksum_jobs.process')
def process(reference,text):return transform(reference,text)
