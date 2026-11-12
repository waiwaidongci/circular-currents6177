import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fakeredis import FakeStrictRedis
BACKEND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
from src.config.database import Base
from src.config import queue as queue_config
from src.models import User,DirectionSurvey,Mooring,BearingReading
from src.schemas.run import RunInput
@pytest.fixture
def db_session(monkeypatch):
    engine=create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine,expire_on_commit=False)
    fake_redis=FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(queue_config,'queue',fake_redis)
    import src.services.run_service as run_service
    monkeypatch.setattr(run_service,'queue',fake_redis)
    session=Session()
    yield session,fake_redis
    session.close();engine.dispose()
def _seed_base(session,readings_per_group=4):
    user=User(email='analyst@jijia.demo',name='林霁',role='analyst',password_hash='x')
    survey=DirectionSurvey(code='s1',name='调查一',period='2026-11-01',description='d')
    ma=Mooring(code='JJ-A',name='A浮标',description='');mb=Mooring(code='JJ-B',name='B浮标',description='')
    session.add_all([user,survey,ma,mb]);session.flush()
    for mooring,base in [(ma,0.0),(mb,90.0)]:
        for i in range(readings_per_group):
            session.add(BearingReading(survey_id=survey.id,mooring_id=mooring.id,code=f'{mooring.code}-{i:03d}',bearing=(base+i)%360,observed_at='2026-11-01T00:00'))
    session.commit()
    return user,survey,ma,mb
def _run_input(survey,ma,mb,name='研究-001',**overrides):
    payload=dict(name=name,survey_id=survey.id,mooring_a_id=ma.id,mooring_b_id=mb.id,permutations=99,seed=157)
    payload.update(overrides)
    return RunInput(**payload)
@pytest.fixture
def base_world(db_session):
    session,_=db_session
    return _seed_base(session)