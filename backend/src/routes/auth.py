from fastapi import APIRouter,Depends
from src.config.database import session
from src.schemas.auth import LoginInput
from src.controllers.auth_controller import login
router=APIRouter(prefix='/auth',tags=['auth'])
@router.post('/login')
def sign_in(data:LoginInput,db=Depends(session)): return login(db,data)
