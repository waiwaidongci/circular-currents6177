from src.constants.enums import Role
from fastapi import APIRouter,Depends
from src.config.database import session
from src.middlewares.auth import require
from src.schemas.survey import SurveyInput,SurveyPatch
from src.controllers.survey_controller import listing,create,patch
router=APIRouter(prefix='/surveys')
@router.get('')
def index(db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db)
@router.post('',status_code=201)
def add(data:SurveyInput,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return create(db,data,u)
@router.patch('/{id}')
def edit(id:int,data:SurveyPatch,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return patch(db,id,data,u)
