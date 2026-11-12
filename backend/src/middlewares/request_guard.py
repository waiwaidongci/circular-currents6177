import time,uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from redis.exceptions import RedisError
from src.config.queue import queue
class RequestGuard(BaseHTTPMiddleware):
    async def dispatch(self,request,call_next):
        request_id=uuid.uuid4().hex[:12]
        if request.url.path!='/health':
            try:
                key=f'currents:rate:{request.client.host}:{int(time.time()//60)}'
                count=queue.incr(key)
                if count==1: queue.expire(key,65)
                if count>360: return JSONResponse({'detail':'请求频繁，一分钟后可重试'},status_code=429)
            except RedisError:
                return JSONResponse({'detail':'任务服务暂不可用，请稍后重试'},status_code=503)
        response=await call_next(request)
        response.headers['X-Request-ID']=request_id
        return response
