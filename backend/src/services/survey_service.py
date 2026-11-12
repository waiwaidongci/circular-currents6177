from sqlalchemy import select
from fastapi import HTTPException
from src.models import DirectionSurvey
from src.utils.audit import record
from src.utils.serializers import serialize
def listing(db):return [serialize(x) for x in db.scalars(select(DirectionSurvey).order_by(DirectionSurvey.id))]
def create(db,data,user):
    if db.scalar(select(DirectionSurvey).where(DirectionSurvey.code==data.code)):raise HTTPException(409,'调查编号已存在')
    row=DirectionSurvey(**data.model_dump());db.add(row);db.flush();record(db,user,'survey.created',row.id);db.commit();return serialize(row)
def patch(db,id,data,user):
    row=db.get(DirectionSurvey,id)
    if not row:raise HTTPException(404,'调查不存在')
    row.description=data.description;record(db,user,'survey.edited',id);db.commit();return serialize(row)
