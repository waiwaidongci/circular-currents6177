import logging,time
from datetime import datetime,timedelta
from sqlalchemy import select,update
from fastapi import HTTPException
from src.models import DirectionRun,DirectionSurvey,Mooring,BearingReading
from src.config.queue import queue
from src.constants.enums import RunStatus
from src.utils.audit import record
from src.utils.serializers import serialize
from src.services.analysis_algorithm import analyze
QUEUE='currents:runs'
# 租约时长：超过此时长仍处于 running 的执行视为中断，可被重新接手
LEASE_SECONDS=120
# 入队宽限：queued 且早于该时长才判定为入队丢失，避免与刚提交的任务竞争
ENQUEUE_GRACE_SECONDS=10
# 恢复协调节流，多个执行者并发运行时共享同一个节流窗
REAP_INTERVAL_SECONDS=5
_REAP_KEY='currents:runs:reap-at'
# 内部列：执行租约与受理快照不进入既有对外结果格式
_INTERNAL_COLUMNS={'input_snapshot','claimed_by','claimed_at'}
log=logging.getLogger('src.run_service')
def _public(row):
    return {key:value for key,value in serialize(row).items() if key not in _INTERNAL_COLUMNS}
def listing(db):return [_public(x) for x in db.scalars(select(DirectionRun).order_by(DirectionRun.id.desc()))]
def detail(db,id):
    row=db.get(DirectionRun,id)
    if not row:return None
    return _public(row)
def _config(run):
    return {'survey_id':run.survey_id,'mooring_a_id':run.mooring_a_id,'mooring_b_id':run.mooring_b_id,'permutations':run.permutations,'seed':run.seed}
def build_snapshot(db,survey_id,mooring_a_id,mooring_b_id):
    '''受理时固化两组采样，之后补录采样不会改写既有研究。'''
    groups=[]
    for mooring_id in [mooring_a_id,mooring_b_id]:
        items=db.scalars(select(BearingReading).where(BearingReading.survey_id==survey_id,BearingReading.mooring_id==mooring_id).order_by(BearingReading.code)).all()
        groups.append([{'code':x.code,'bearing':x.bearing,'observed_at':x.observed_at} for x in items])
    return {'a':groups[0],'b':groups[1]}
def enqueue(run_id):
    '''投递队列；失败不丢任务，恢复协调会依据 DB 状态重新入队。'''
    try:queue.rpush(QUEUE,str(run_id))
    except Exception:log.exception('enqueue failed; run %s awaits reconciliation',run_id)
def create(db,data,user):
    if not db.get(DirectionSurvey,data.survey_id) or not db.get(Mooring,data.mooring_a_id) or not db.get(Mooring,data.mooring_b_id):raise HTTPException(404,'调查或浮标不存在')
    if db.scalar(select(DirectionRun).where(DirectionRun.name==data.name)):raise HTTPException(409,'研究名称重复')
    row=DirectionRun(**data.model_dump(),created_by=user.id,status=RunStatus.QUEUED,input_snapshot=build_snapshot(db,data.survey_id,data.mooring_a_id,data.mooring_b_id))
    db.add(row);db.flush();record(db,user,'run.queued',row.id);db.commit()
    # 先持久化受理状态再投递：投递失败也由恢复流程兜底，研究不会卡住
    enqueue(row.id)
    return _public(row)
def claim(db,id,worker_id):
    '''原子认领：仅 queued 可被接手；重复投递或并发执行者只有一个成功。'''
    result=db.execute(update(DirectionRun).where(DirectionRun.id==id,DirectionRun.status==RunStatus.QUEUED).values(status=RunStatus.RUNNING,claimed_by=worker_id,claimed_at=datetime.utcnow(),error=''))
    db.commit()
    return result.rowcount==1
def publish_completed(db,id,worker_id,result):
    '''带认领者条件发布完整结果，旧执行者迟归的写回被拒绝。'''
    result_=db.execute(update(DirectionRun).where(DirectionRun.id==id,DirectionRun.status==RunStatus.RUNNING,DirectionRun.claimed_by==worker_id).values(status=RunStatus.COMPLETED,result=result,error=''))
    db.commit()
    return result_.rowcount==1
def publish_failed(db,id,worker_id,message):
    result=db.execute(update(DirectionRun).where(DirectionRun.id==id,DirectionRun.status==RunStatus.RUNNING,DirectionRun.claimed_by==worker_id).values(status=RunStatus.FAILED,error=message[:500]))
    db.commit()
    return result.rowcount==1
def compute(db,id,worker_id='inline'):
    run=db.get(DirectionRun,id)
    if not run or run.status not in [RunStatus.QUEUED,RunStatus.RUNNING]:return
    if run.status==RunStatus.QUEUED:
        if not claim(db,id,worker_id):return
        db.refresh(run)
    elif run.claimed_by!=worker_id:
        # 已有其他执行者持有租约，避免重复计算
        return
    snapshot=run.input_snapshot
    if snapshot is None:
        # 兼容升级前的遗留行：首次执行时补建并固化快照，此后重试同样不受补录影响
        snapshot=build_snapshot(db,run.survey_id,run.mooring_a_id,run.mooring_b_id)
        run.input_snapshot=snapshot;db.commit()
    try:
        result=analyze(snapshot['a'],snapshot['b'],_config(run))
    except Exception as exc:
        db.rollback()
        # 确定性计算失败保留明确 failed 任务；进程中断（无异常提交）则由恢复流程重排队
        if not publish_failed(db,id,worker_id,str(exc)):
            log.warning('stale worker %s failure discarded for run %s',worker_id,id)
        return
    if not publish_completed(db,id,worker_id,result):
        log.warning('stale worker %s result discarded for run %s',worker_id,id);return
    db.refresh(run);return _public(run)
def reconcile(db,now=None):
    '''恢复协调：入队丢失的 queued 重新投递；租约过期的 running 重置后重排队。

    沿用原研究编号、受理快照与参数；全部为条件更新，可被多个执行者并发调用。
    返回本轮重新入队的研究编号列表。
    '''
    now=now or datetime.utcnow()
    requeued=[]
    stale_queued=db.scalars(select(DirectionRun.id).where(DirectionRun.status==RunStatus.QUEUED,DirectionRun.created_at<=now-timedelta(seconds=ENQUEUE_GRACE_SECONDS))).all()
    if stale_queued:
        try:queued_ids={int(x) for x in queue.lrange(QUEUE,0,-1)}
        except Exception:log.exception('queue unreachable during reconciliation');queued_ids=None
        if queued_ids is not None:
            for run_id in stale_queued:
                if run_id not in queued_ids:
                    enqueue(run_id);requeued.append(run_id)
    expired_cutoff=now-timedelta(seconds=LEASE_SECONDS)
    expired_ids=db.scalars(select(DirectionRun.id).where(DirectionRun.status==RunStatus.RUNNING,DirectionRun.claimed_at.isnot(None),DirectionRun.claimed_at<=expired_cutoff)).all()
    if expired_ids:
        db.execute(update(DirectionRun).where(DirectionRun.id.in_(expired_ids),DirectionRun.status==RunStatus.RUNNING).values(status=RunStatus.QUEUED,claimed_by=None,claimed_at=None,error=''))
        db.commit()
        for run_id in expired_ids:
            enqueue(run_id);requeued.append(run_id)
    return requeued
def maybe_reconcile(db):
    '''按 Redis 节流窗触发恢复协调，避免每个执行者都全量扫描。'''
    try:
        if queue.set(_REAP_KEY,str(time.time()),nx=True,ex=REAP_INTERVAL_SECONDS):
            return reconcile(db)
    except Exception:log.exception('reconciliation skipped')
    return []
