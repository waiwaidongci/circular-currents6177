from src.constants.enums import Role
from fastapi import APIRouter,Depends
from fastapi.responses import Response
from src.config.database import session
from src.middlewares.auth import require
from src.schemas.note import NoteInput,NoteReview
from src.controllers.note_controller import listing,create,review,export
router=APIRouter(prefix='/notes')
@router.get('')
def index(db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return listing(db)
@router.post('',status_code=201)
def add(data:NoteInput,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST))):return create(db,data,u)
@router.patch('/{id}/review')
def approve(id:int,data:NoteReview,db=Depends(session),u=Depends(require(Role.ADMIN))):return review(db,id,data,u)
@router.get('/{id}/export')
def csv(id:int,db=Depends(session),u=Depends(require(Role.ADMIN,Role.ANALYST,Role.VIEWER))):return Response(export(db,id,u),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename=jijia-observation-{id}.csv'})
