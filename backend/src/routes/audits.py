from src.constants.enums import Role
from fastapi import APIRouter,Depends
from sqlalchemy import select
from src.config.database import session
from src.middlewares.auth import require
from src.models import Audit
from src.utils.serializers import serialize
router=APIRouter(prefix='/audits',tags=['audit'])
@router.get('')
def listing(db=Depends(session),user=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return [serialize(x) for x in db.scalars(select(Audit).order_by(Audit.id.desc()).limit(100))]
