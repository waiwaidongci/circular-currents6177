import threading
from datetime import datetime,timedelta
import pytest
from sqlalchemy import create_engine,select
from sqlalchemy.orm import sessionmaker
from fakeredis import FakeStrictRedis
from src.config.database import Base
from src.config import queue as queue_config
from src.services import run_service as svc
from src.models import DirectionRun
from src.constants.enums import RunStatus
from conftest import _seed_base,_run_input
@pytest.fixture
def concurrency_world(tmp_path):
    # 文件型 SQLite：每个会话独立连接，带忙等待，贴近生产多连接并发语义
    engine=create_engine(f'sqlite+pysqlite:///{tmp_path}/concurrency.db',connect_args={'timeout':30,'check_same_thread':False})
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine,expire_on_commit=False)
    fake=FakeStrictRedis(decode_responses=True)
    queue_config.queue=fake;svc.queue=fake
    seed=Session();user,survey,ma,mb=_seed_base(seed)
    yield Session,fake,(user,survey,ma,mb)
    seed.close();engine.dispose()
def test_concurrent_workers_single_completion_per_run(concurrency_world):
    Session,fake,world=concurrency_world
    user,survey,ma,mb=world
    with Session() as seed:
        run_ids=[]
        for i in range(6):
            row=svc.create(seed,_run_input(survey,ma,mb,f'并发研究-{i:02d}',permutations=99),user)
            run_ids.append(row['id'])
    # 重复投递：每个 ID 额外入队 2 次
    for rid in run_ids:
        for _ in range(2):fake.rpush(svc.QUEUE,str(rid))
    errors=[]
    def worker(wid):
        try:
            for _ in range(30):
                item=fake.blpop(svc.QUEUE,timeout=1)
                if not item:return
                with Session() as db:svc.compute(db,int(item[1]),wid)
        except Exception as exc:errors.append((wid,repr(exc)))
    threads=[threading.Thread(target=worker,args=(f'w{i}',)) for i in range(4)]
    for t in threads:t.start()
    for t in threads:t.join(timeout=60)
    assert not errors,errors
    with Session() as db:
        for rid in run_ids:
            run=db.get(DirectionRun,rid)
            assert run.status==RunStatus.COMPLETED,(rid,run.status)
            assert run.result['fingerprint']
            assert run.claimed_by in {f'w{i}' for i in range(4)}
        assert len(db.scalars(select(DirectionRun)).all())==6
def test_interrupted_then_concurrent_recovery_publishes_once(concurrency_world):
    Session,fake,world=concurrency_world
    user,survey,ma,mb=world
    with Session() as seed:
        row=svc.create(seed,_run_input(survey,ma,mb,'中断恢复研究'),user);rid=row['id']
        assert svc.claim(seed,rid,'dead-worker')
        run=seed.get(DirectionRun,rid);run.claimed_at=datetime.utcnow()-timedelta(seconds=999);seed.commit()
    # 两个执行者同时跑恢复协调（条件更新保证只重置一次）
    def reap():
        with Session() as db:svc.reconcile(db)
    ts=[threading.Thread(target=reap) for _ in range(2)]
    for t in ts:t.start()
    for t in ts:t.join(timeout=30)
    with Session() as db:
        assert db.get(DirectionRun,rid).status==RunStatus.QUEUED
    # 两个 worker 抢同一恢复消息
    outcomes=[]
    def grab(wid):
        with Session() as db:outcomes.append(svc.claim(db,rid,wid))
    ts=[threading.Thread(target=grab,args=(f'g{i}',)) for i in range(2)]
    for t in ts:t.start()
    for t in ts:t.join(timeout=30)
    assert sorted(outcomes)==[False,True]
    with Session() as db:
        svc.compute(db,rid,db.get(DirectionRun,rid).claimed_by)
        final=db.get(DirectionRun,rid)
        assert final.status==RunStatus.COMPLETED
        assert final.result['a']['n']==4
