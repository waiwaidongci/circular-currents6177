import logging,threading,uuid
from pathlib import Path
from src.config import database as db_config
from src.config.queue import queue
from src.services.run_service import compute,maybe_reconcile,QUEUE
logging.basicConfig(level=logging.INFO)
log=logging.getLogger('src.worker')
WORKER_ID='worker-'+uuid.uuid4().hex[:12]
# 测试与优雅停机可置位，正常运行不触发
stop_event=threading.Event()
def main():
    while not stop_event.is_set():
        Path('/tmp/heartbeat').touch()
        try:
            with db_config.SessionLocal() as db:
                maybe_reconcile(db)
            item=queue.blpop(QUEUE,timeout=4)
            if not item:continue
            with db_config.SessionLocal() as db:
                # compute 内部原子认领、条件发布；重复投递与中断恢复均不会产生重复结果
                compute(db,int(item[1]),WORKER_ID)
        except Exception:
            log.exception('worker loop')
if __name__=='__main__':
    main()
