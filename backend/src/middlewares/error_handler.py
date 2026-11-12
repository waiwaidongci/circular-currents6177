import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
class ErrorHandler(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        try: return await call_next(request)
        except Exception:
            logging.exception('unhandled request failure')
            return JSONResponse({'detail':'服务暂时无法完成操作，请重试'},status_code=500)
