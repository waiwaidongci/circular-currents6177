from datetime import datetime
from sqlalchemy import String,ForeignKey,Double,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class DirectionSurvey(Base):
    __tablename__='direction_surveys'
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(40),unique=True)
    name:Mapped[str]=mapped_column(String(120))
    period:Mapped[str]=mapped_column(String(60))
    description:Mapped[str]=mapped_column(String(1200),default='')
