from fastapi import HTTPException
from sqlalchemy import select
from src.models import User
from src.utils.security import check_password,token_for
from src.utils.audit import record

def login(db,data):
    user=db.scalar(select(User).where(User.email==data.email))
    if not user or not check_password(data.password,user.password_hash): raise HTTPException(401,'账号或密码错误')
    record(db,user,'login','session'); db.commit()
    return {'access_token':token_for(user),'user':{'id':user.id,'name':user.name,'email':user.email,'role':user.role}}
