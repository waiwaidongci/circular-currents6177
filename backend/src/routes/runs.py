from src.constants.enums import Role
from fastapi import APIRouter,Depends,HTTPException
from src.config.database import session
from src.middlewares.auth import require
from src.schemas.run import RunInput
from src.controllers.run_controller import listing,create
from src.models import DirectionRun
from src.utils.serializers import serialize
router=APIRouter(prefix='/runs')
@router.get('')
def index(db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db)
@router.get('/{id}')
def detail(id:int,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):
    run=db.get(DirectionRun,id)
    if not run:raise HTTPException(404,'研究不存在')
    return serialize(run)
@router.post('',status_code=202)
def add(data:RunInput,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return create(db,data,u)
