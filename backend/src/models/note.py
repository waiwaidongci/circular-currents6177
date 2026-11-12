from datetime import datetime
from sqlalchemy import String,ForeignKey,Double,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class ObservationNote(Base):
    __tablename__='observation_notes'
    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(160),unique=True)
    run_id:Mapped[int]=mapped_column(ForeignKey('direction_runs.id'))
    interpretation:Mapped[str]=mapped_column(String(2000))
    action:Mapped[str]=mapped_column(String(1200))
    status:Mapped[str]=mapped_column(String(20),default='draft')
    approved_by:Mapped[str]=mapped_column(String(100),default='')
    review_comment:Mapped[str]=mapped_column(String(1200),default='')
    created_by:Mapped[int]=mapped_column(ForeignKey('users.id'))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
