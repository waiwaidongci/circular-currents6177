import os,logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from src.config.database import Base,engine
from src.config.queue import queue
from src import models
from src.routes import auth,surveys,moorings,bearings,runs,notes,audits
from src.middlewares.request_guard import RequestGuard
from src.middlewares.error_handler import ErrorHandler
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    if os.getenv('SEED_DEMO','true').lower()=='true':
        try:
            from scripts.seed_demo import seed
            seed()
        except Exception:logging.exception('seed failed; API remains available')
    yield
app=FastAPI(title='霁岬浮标流向研究册',lifespan=lifespan)
app.add_middleware(RequestGuard);app.add_middleware(ErrorHandler)
for module in [auth,surveys,moorings,bearings,runs,notes,audits]:app.include_router(module.router)
@app.get('/health')
def health():
    with engine.connect() as db:db.execute(text('SELECT 1'))
    queue.ping();return {'status':'healthy'}

@app.exception_handler(RequestValidationError)
async def validation_error(request,exc):
    detail='；'.join('.'.join(map(str,e['loc'][1:]))+': '+e['msg'] for e in exc.errors())
    return JSONResponse(status_code=422,content={'detail':'输入校验失败：'+detail[:500]})
