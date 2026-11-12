from datetime import datetime,timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fakeredis import FakeStrictRedis
from src.config.database import Base
from src.config import queue as queue_config
from src.config import database as db_config
from src.main import app
from src.models import DirectionRun
from src.services import run_service as svc
from conftest import _seed_base
PUBLIC_COLUMNS={'id','name','survey_id','mooring_a_id','mooring_b_id','permutations','seed','status','result','error','created_by','created_at'}
@pytest.fixture
def client(monkeypatch):
    engine=create_engine('sqlite+pysqlite:///:memory:',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine,expire_on_commit=False)
    fake=FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(queue_config,'queue',fake)
    monkeypatch.setattr(svc,'queue',fake)
    from src.middlewares import request_guard
    monkeypatch.setattr(request_guard,'queue',fake)
    monkeypatch.setattr(db_config,'SessionLocal',Session)
    seed=Session();user,survey,ma,mb=_seed_base(seed)
    from src.middlewares.auth import current_user
    app.dependency_overrides[current_user]=lambda:user
    def override_session():
        s=Session()
        try:yield s
        finally:s.close()
    from src.config.database import session as session_dep
    app.dependency_overrides[session_dep]=override_session
    yield TestClient(app),Session,fake,(user,survey,ma,mb)
    app.dependency_overrides.clear();engine.dispose()
def _payload(world,name='API研究-001'):
    user,survey,ma,mb=world
    return {'name':name,'survey_id':survey.id,'mooring_a_id':ma.id,'mooring_b_id':mb.id,'permutations':99,'seed':157}
def test_api_create_shape_and_recovery_flow(client):
    http,Session,fake,world=client
    resp=http.post('/runs',json=_payload(world))
    assert resp.status_code==202
    body=resp.json()
    assert set(body.keys())==PUBLIC_COLUMNS
    assert body['status']=='queued' and body['result']=={} and body['error']==''
    rid=body['id']
    # 模拟 worker 崩溃：running 且租约过期
    with Session() as db:
        assert svc.claim(db,rid,'crashed')
        run=db.get(DirectionRun,rid);run.claimed_at=datetime.utcnow()-timedelta(seconds=999);db.commit()
    with Session() as db:svc.maybe_reconcile(db)
    assert fake.lrange(svc.QUEUE,0,-1)[-1]==str(rid)
    with Session() as db:svc.compute(db,rid,'worker-B')
    detail=http.get(f'/runs/{rid}').json()
    assert set(detail.keys())==PUBLIC_COLUMNS
    assert detail['status']=='completed' and detail['id']==rid
    assert set(detail['result'].keys())=={'a','b','energy','input_snapshot','fingerprint','interpretation'}
    assert detail['result']['a']['n']==4 and detail['result']['energy']['seed']==157
def test_api_duplicate_name_conflict(client):
    http,Session,fake,world=client
    assert http.post('/runs',json=_payload(world)).status_code==202
    second=http.post('/runs',json=_payload(world))
    assert second.status_code==409
def test_api_404_detail(client):
    http,_,_,_=client
    assert http.get('/runs/9999').status_code==404
