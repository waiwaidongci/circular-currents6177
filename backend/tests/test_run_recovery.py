import time,threading
from datetime import datetime,timedelta
from src.models import DirectionRun,BearingReading,Mooring
from src.constants.enums import RunStatus
from src.services import run_service as svc
from conftest import _run_input,_seed_base
PUBLIC_COLUMNS={'id','name','survey_id','mooring_a_id','mooring_b_id','permutations','seed','status','result','error','created_by','created_at'}
RESULT_KEYS={'a','b','energy','input_snapshot','fingerprint','interpretation'}
def _make(session,base_world,name='研究-001',**overrides):
    user,survey,ma,mb=base_world
    return svc.create(session,_run_input(survey,ma,mb,name,**overrides),user)
def _get(session,run_id):return session.get(DirectionRun,run_id)
# 1. 受理时固化采样与参数；对外字段维持既有格式
def test_create_persists_snapshot_and_keeps_public_shape(db_session,base_world):
    session,redis_=db_session
    payload=_make(session,base_world)
    run=_get(session,payload['id'])
    assert run.status==RunStatus.QUEUED
    assert run.input_snapshot is not None
    assert len(run.input_snapshot['a'])==4 and len(run.input_snapshot['b'])==4
    assert redis_.lrange(svc.QUEUE,0,-1)==[str(run.id)]
    assert set(payload.keys())==PUBLIC_COLUMNS
    assert 'input_snapshot' not in payload and 'claimed_by' not in payload and 'claimed_at' not in payload
    assert set(svc.detail(session,run.id).keys())==PUBLIC_COLUMNS
    assert set(x for x in svc.listing(session)[0].keys())==PUBLIC_COLUMNS
# 2. 补录采样不影响已受理研究，只影响之后新建的研究
def test_later_readings_do_not_rewrite_accepted_run(db_session,base_world):
    session,redis_=db_session
    user,survey,ma,mb=base_world
    first=_make(session,base_world,'研究-既有')
    for i in range(4,6):
        session.add(BearingReading(survey_id=survey.id,mooring_id=ma.id,code=f'JJ-A-{i:03d}',bearing=float(i),observed_at='2026-11-02T00:00'))
    session.commit()
    svc.compute(session,first['id'],'w1')
    done=_get(session,first['id'])
    assert done.status==RunStatus.COMPLETED
    assert done.result['a']['n']==4 and done.result['b']['n']==4
    assert set(done.result.keys())==RESULT_KEYS
    assert len(done.result['input_snapshot']['a'])==4
    second=_make(session,base_world,'研究-新建')
    svc.compute(session,second['id'],'w1')
    assert _get(session,second['id']).result['a']['n']==6
# 3. 重复投递：每份研究只发布一个完整结果（队列中的重复条目是死信，不产生重复结果）
def test_duplicate_delivery_publishes_single_result(db_session,base_world):
    session,redis_=db_session
    created=_make(session,base_world)
    redis_.rpush(svc.QUEUE,str(created['id']));redis_.rpush(svc.QUEUE,str(created['id']))
    first=svc.compute(session,created['id'],'w1')
    second=svc.compute(session,created['id'],'w2')
    run=_get(session,created['id'])
    assert first is not None and second is None
    assert run.status==RunStatus.COMPLETED and run.claimed_by=='w1'
    # 死信条目再次被取出时，原子认领直接拒绝，状态与结果不变
    assert svc.claim(session,created['id'],'w3') is False
    assert _get(session,created['id']).status==RunStatus.COMPLETED
    assert _get(session,created['id']).result['fingerprint']==run.result['fingerprint']
# 4. 多个执行者并发接手：原子认领只有一个成功
def test_concurrent_claim_single_winner(db_session,base_world):
    session,redis_=db_session
    created=_make(session,base_world)
    assert svc.claim(session,created['id'],'w1') is True
    assert svc.claim(session,created['id'],'w2') is False
    run=_get(session,created['id'])
    assert run.status==RunStatus.RUNNING and run.claimed_by=='w1' and run.claimed_at is not None
    # 非持有者不能驱动计算
    assert svc.compute(session,created['id'],'w2') is None
    assert _get(session,created['id']).claimed_by=='w1'
# 5. 旧执行者迟归不能覆盖新执行者发布的完整结果
def test_stale_worker_cannot_overwrite(db_session,base_world):
    session,redis_=db_session
    created=_make(session,base_world);rid=created['id']
    assert svc.claim(session,rid,'worker-A')
    run=_get(session,rid);run.claimed_at=datetime.utcnow()-timedelta(seconds=300);session.commit()
    requeued=svc.reconcile(session)
    assert rid in requeued and _get(session,rid).status==RunStatus.QUEUED
    assert redis_.lrange(svc.QUEUE,0,-1)[-1]==str(rid)
    svc.compute(session,rid,'worker-B')
    winner=_get(session,rid)
    assert winner.status==RunStatus.COMPLETED and winner.claimed_by=='worker-B'
    winner_fingerprint=winner.result['fingerprint']
    stale_result={'a':{},'b':{},'energy':{},'input_snapshot':{},'fingerprint':'stale','interpretation':''}
    assert svc.publish_completed(session,rid,'worker-A',stale_result) is False
    assert svc.publish_failed(session,rid,'worker-A','late failure') is False
    final=_get(session,rid)
    assert final.status==RunStatus.COMPLETED
    assert final.result['fingerprint']==winner_fingerprint
# 6. 入队失败后自动恢复，沿用原编号
def test_enqueue_failure_is_reconciled(db_session,base_world,monkeypatch):
    session,redis_=db_session
    state={'down':True}
    real_rpush=redis_.rpush
    def maybe_down(*a,**k):
        if state['down']:raise RuntimeError('redis down')
        return real_rpush(*a,**k)
    monkeypatch.setattr(svc.queue,'rpush',maybe_down)
    created=_make(session,base_world)
    assert redis_.llen(svc.QUEUE)==0
    assert _get(session,created['id']).status==RunStatus.QUEUED
    state['down']=False
    requeued=svc.reconcile(session,now=datetime.utcnow()+timedelta(seconds=30))
    assert requeued==[created['id']]
    assert redis_.lrange(svc.QUEUE,0,-1)==[str(created['id'])]
    svc.compute(session,created['id'],'w1')
    assert _get(session,created['id']).status==RunStatus.COMPLETED
# 7. 计算中断（running 租约过期）后自动恢复，仍用受理快照与参数
def test_interrupted_running_is_requeued_with_snapshot(db_session,base_world):
    session,redis_=db_session
    created=_make(session,base_world);rid=created['id']
    svc.claim(session,rid,'crashed')
    session.add(BearingReading(survey_id=created['survey_id'],mooring_id=created['mooring_a_id'],code='JJ-A-999',bearing=5.0,observed_at='2026-11-03T00:00'))
    session.commit()
    run=_get(session,rid);run.claimed_at=datetime.utcnow()-timedelta(seconds=999);session.commit()
    requeued=svc.reconcile(session)
    assert requeued==[rid]
    run=_get(session,rid)
    assert run.status==RunStatus.QUEUED and run.claimed_by is None and run.claimed_at is None
    assert len(run.input_snapshot['a'])==4
    svc.compute(session,rid,'replacement')
    done=_get(session,rid)
    assert done.id==rid and done.status==RunStatus.COMPLETED and done.claimed_by=='replacement'
    assert done.result['a']['n']==4 and set(done.result.keys())==RESULT_KEYS
# 8. 确定性计算失败保留明确 failed，不会被恢复流程反复重排队
def test_deterministic_failure_stays_failed(db_session,base_world):
    session,redis_=db_session
    user,survey,ma,mb=base_world
    empty=Mooring(code='JJ-C',name='空浮标',description='');session.add(empty);session.commit()
    created=svc.create(session,_run_input(survey,ma,empty,'研究-空组'),user)
    svc.compute(session,created['id'],'w1')
    run=_get(session,created['id'])
    assert run.status==RunStatus.FAILED and run.error
    assert svc.reconcile(session,now=datetime.utcnow()+timedelta(seconds=300))==[]
    assert _get(session,created['id']).status==RunStatus.FAILED
# 8b. 升级前遗留行（无快照）：首次执行补建快照并固化，结果格式不变
def test_legacy_row_without_snapshot_is_backfilled(db_session,base_world):
    session,redis_=db_session
    user,survey,ma,mb=base_world
    legacy=DirectionRun(name='遗留研究',survey_id=survey.id,mooring_a_id=ma.id,mooring_b_id=mb.id,permutations=99,seed=157,created_by=user.id,status=RunStatus.QUEUED,input_snapshot=None)
    session.add(legacy);session.commit()
    rid=legacy.id
    svc.compute(session,rid,'w1')
    run=_get(session,rid)
    assert run.status==RunStatus.COMPLETED
    assert run.input_snapshot is not None and len(run.input_snapshot['a'])==4
    assert set(run.result.keys())==RESULT_KEYS
# 9. 宽限期内不重复入队；节流窗内只协调一次
def test_grace_and_throttle(db_session,base_world):
    session,redis_=db_session
    created=_make(session,base_world)
    assert svc.reconcile(session,now=datetime.utcnow()+timedelta(seconds=5))==[]
    assert redis_.lrange(svc.QUEUE,0,-1)==[str(created['id'])]
    assert svc.maybe_reconcile(session)==[]  # 队列健康，无重投
    assert svc.maybe_reconcile(session)==[]  # 节流：第二次不执行协调
    assert redis_.get('currents:runs:reap-at') is not None
# 10. worker 端到端：中断任务经真实 worker 主循环恢复并完成
def test_worker_loop_recovers_interrupted_run(db_session,base_world,monkeypatch,tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.config.database import Base
    from src.config import queue as queue_config
    engine=create_engine(f'sqlite+pysqlite:///{tmp_path}/worker_e2e.db')
    Base.metadata.create_all(engine)
    Session=sessionmaker(bind=engine,expire_on_commit=False)
    seed_session=Session()
    user,survey,ma,mb=_seed_base(seed_session)
    created=svc.create(seed_session,_run_input(survey,ma,mb,'研究-worker恢复'),user)
    rid=created['id']
    svc.claim(seed_session,rid,'crashed')
    run=seed_session.get(DirectionRun,rid);run.claimed_at=datetime.utcnow()-timedelta(seconds=999);seed_session.commit()
    seed_session.close()
    import src.config.database as db_config
    import src.worker as worker_module
    monkeypatch.setattr(db_config,'SessionLocal',Session)
    monkeypatch.setattr(worker_module,'queue',queue_config.queue)
    t=threading.Thread(target=worker_module.main,daemon=True);t.start()
    deadline=time.time()+15
    while time.time()<deadline:
        with Session() as check:
            if check.get(DirectionRun,rid).status==RunStatus.COMPLETED:break
        time.sleep(0.2)
    worker_module.stop_event.set()
    t.join(timeout=5)
    with Session() as check:
        final=check.get(DirectionRun,rid)
        assert final.status==RunStatus.COMPLETED
        assert final.claimed_by==worker_module.WORKER_ID
        assert final.result['a']['n']==4
    engine.dispose()
