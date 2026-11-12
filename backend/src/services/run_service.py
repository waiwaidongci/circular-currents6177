from sqlalchemy import select
from fastapi import HTTPException
from src.models import DirectionRun,DirectionSurvey,Mooring,BearingReading
from src.config.queue import queue
from src.constants.enums import RunStatus
from src.utils.audit import record
from src.utils.serializers import serialize
from src.services.analysis_algorithm import analyze
QUEUE='currents:runs'
def listing(db):return [serialize(x) for x in db.scalars(select(DirectionRun).order_by(DirectionRun.id.desc()))]
def create(db,data,user):
    if not db.get(DirectionSurvey,data.survey_id) or not db.get(Mooring,data.mooring_a_id) or not db.get(Mooring,data.mooring_b_id):raise HTTPException(404,'调查或浮标不存在')
    if db.scalar(select(DirectionRun).where(DirectionRun.name==data.name)):raise HTTPException(409,'研究名称重复')
    row=DirectionRun(**data.model_dump(),created_by=user.id,status=RunStatus.QUEUED);db.add(row);db.flush();record(db,user,'run.queued',row.id);db.commit();queue.rpush(QUEUE,str(row.id));return serialize(row)
def compute(db,id):
    run=db.get(DirectionRun,id)
    if not run or run.status not in ['queued','running']:return
    run.status=RunStatus.RUNNING;db.commit()
    rows=[]
    for mooring_id in [run.mooring_a_id,run.mooring_b_id]:
        items=db.scalars(select(BearingReading).where(BearingReading.survey_id==run.survey_id,BearingReading.mooring_id==mooring_id).order_by(BearingReading.code)).all()
        rows.append([{'code':x.code,'bearing':x.bearing,'observed_at':x.observed_at} for x in items])
    run.result=analyze(*rows,{'survey_id':run.survey_id,'mooring_a_id':run.mooring_a_id,'mooring_b_id':run.mooring_b_id,'permutations':run.permutations,'seed':run.seed});run.status=RunStatus.COMPLETED;run.error='';db.commit();return serialize(run)
