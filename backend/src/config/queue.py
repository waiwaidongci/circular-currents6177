import redis
from .settings import REDIS_URL
queue=redis.Redis.from_url(REDIS_URL,decode_responses=True)
QUEUE_NAME='currents:calibration'
