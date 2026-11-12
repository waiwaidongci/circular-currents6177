from src.constants.enums import Role
from fastapi import APIRouter,Depends
from src.config.database import session
from src.middlewares.auth import require
from src.schemas.mooring import MooringPatch
from src.controllers.mooring_controller import listing,patch
router=APIRouter(prefix='/moorings')
@router.get('')
def index(db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db)
@router.patch('/{id}')
def edit(id:int,data:MooringPatch,db=Depends(session),u=Depends(require(Role.ADMIN))):return patch(db,id,data,u)
