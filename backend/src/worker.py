import time,logging
from pathlib import Path
from src.config.database import SessionLocal
from src.config.queue import queue
from src.models import DirectionRun
from src.services.run_service import compute,QUEUE
logging.basicConfig(level=logging.INFO)
while True:
    Path('/tmp/heartbeat').touch()
    try:
        item=queue.blpop(QUEUE,timeout=4)
        if not item:continue
        with SessionLocal() as db:
            try:compute(db,int(item[1]))
            except Exception as exc:
                db.rollback();run=db.get(DirectionRun,int(item[1]))
                if run:run.status='failed';run.error=str(exc)[:500];db.commit()
                logging.exception('direction research failed')
    except Exception:logging.exception('worker loop');time.sleep(2)
