import jwt
from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from src.config.database import session
from src.config.settings import JWT_SECRET
from src.models import User
bearer=HTTPBearer(auto_error=False)
def current_user(credential:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(session)):
    try:
        data=jwt.decode(credential.credentials,JWT_SECRET,algorithms=['HS256'])
        user=db.get(User,int(data['sub']))
        if not user: raise ValueError('unknown user')
        return user
    except (AttributeError,ValueError,KeyError,jwt.InvalidTokenError):
        raise HTTPException(401,'登录已失效，请重新登录')
def require(*roles):
    def dependency(user:User=Depends(current_user)):
        if user.role not in roles: raise HTTPException(403,'当前角色没有此操作权限')
        return user
    return dependency
