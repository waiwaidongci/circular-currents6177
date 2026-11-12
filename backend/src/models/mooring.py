from datetime import datetime
from sqlalchemy import String,ForeignKey,Double,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class Mooring(Base):
    __tablename__='moorings'
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    name:Mapped[str]=mapped_column(String(100))
    description:Mapped[str]=mapped_column(String(800),default='')
