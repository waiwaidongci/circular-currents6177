from datetime import datetime
from sqlalchemy import String,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class Audit(Base):
    __tablename__='audits'
    id:Mapped[int]=mapped_column(primary_key=True)
    actor:Mapped[str]=mapped_column(String(100))
    action:Mapped[str]=mapped_column(String(80))
    target:Mapped[str]=mapped_column(String(100))
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
