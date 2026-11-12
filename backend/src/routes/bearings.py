from src.constants.enums import Role
from fastapi import APIRouter,Depends,Query
from src.config.database import session
from src.middlewares.auth import require
from src.schemas.bearing import BearingImport
from src.controllers.bearing_controller import listing,import_rows
router=APIRouter(prefix='/bearings')
@router.get('')
def index(survey_id:int,mooring_id:int=0,offset:int=Query(0,ge=0),limit:int=Query(24,ge=1,le=250),db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db,survey_id,mooring_id,offset,limit)
@router.post('',status_code=201)
def add(data:BearingImport,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return import_rows(db,data,u)
