from sqlalchemy import select
from fastapi import HTTPException
from src.models import Mooring
from src.utils.audit import record
from src.utils.serializers import serialize
def listing(db):return [serialize(x) for x in db.scalars(select(Mooring).order_by(Mooring.id))]
def patch(db,id,data,user):
    row=db.get(Mooring,id)
    if not row:raise HTTPException(404,'浮标不存在')
    row.description=data.description;record(db,user,'mooring.edited',id);db.commit();return serialize(row)
