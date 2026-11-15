from types import SimpleNamespace
from unittest.mock import patch
from fastapi.testclient import TestClient
from checksum_jobs.app import app
from checksum_jobs.worker import transform,celery
client=TestClient(app);headers={'Authorization':'Bearer synthetic-unit-token'}
def test_transformation_and_namespace():
    result=transform('unit-one',"é")
    assert result["byte_length"]==2;assert len(result["sha256"])==64
    assert celery.conf.broker_transport_options['global_keyprefix']=='synthetic-unit:'
    assert celery.conf.result_backend_transport_options['global_keyprefix']=='synthetic-unit:'
def test_http_with_simulated_queue():
    job='3af6507c-5ed0-4913-91af-f570b07352e1'
    with patch('checksum_jobs.app.process.apply_async',return_value=SimpleNamespace(id=job)):
        assert client.post('/jobs',json={'reference':'unit-one','text':'one'},headers=headers).status_code==202
    with patch('checksum_jobs.app.celery.AsyncResult',return_value=SimpleNamespace(state='SUCCESS',result=transform('unit-one','one'))):
        assert client.get('/jobs/'+job,headers=headers).json()['result']['reference']=='unit-one'
    assert client.post("/jobs",json={"reference":"unit-one","text":"one"}).status_code==401
