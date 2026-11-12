from datetime import datetime
from typing import Optional
from sqlalchemy import String,ForeignKey,Double,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class DirectionRun(Base):
    __tablename__='direction_runs'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(160),unique=True)
    survey_id:Mapped[int]=mapped_column(ForeignKey('direction_surveys.id'))
    mooring_a_id:Mapped[int]=mapped_column(ForeignKey('moorings.id'))
    mooring_b_id:Mapped[int]=mapped_column(ForeignKey('moorings.id'))
    permutations:Mapped[int]=mapped_column(default=499)
    seed:Mapped[int]=mapped_column(default=157)
    status:Mapped[str]=mapped_column(String(20),default='queued')
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(String(700),default='')
    # 受理时固化的原始采样与参数；中断恢复与重复执行均以此为准，后补采样不回溯
    input_snapshot:Mapped[Optional[dict]]=mapped_column(JSON,nullable=True,default=None)
    # 执行租约：原子认领后写入，旧执行者迟归的写回按 claimed_by 条件拒绝
    claimed_by:Mapped[Optional[str]]=mapped_column(String(64),nullable=True,default=None)
    claimed_at:Mapped[Optional[datetime]]=mapped_column(DateTime,nullable=True,default=None)
    created_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
