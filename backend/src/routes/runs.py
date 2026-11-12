from fastapi import APIRouter,Depends,HTTPException
from src.config.database import session
from src.middlewares.auth import require
from src.constants.enums import Role
from src.schemas.run import RunInput
from src.controllers.run_controller import listing,create
from src.services import run_service as service
router=APIRouter(prefix='/runs')
@router.get('')
def index(db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db)
@router.get('/{id}')
def detail(id:int,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):
    row=service.detail(db,id)
    if not row:raise HTTPException(404,'研究不存在')
    return row
@router.post('',status_code=202)
def add(data:RunInput,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return create(db,data,u)
