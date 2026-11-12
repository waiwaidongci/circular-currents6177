from datetime import datetime
from sqlalchemy import String,ForeignKey,Double,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class BearingReading(Base):
    __tablename__='bearing_readings'
    id:Mapped[int]=mapped_column(primary_key=True)
    survey_id:Mapped[int]=mapped_column(ForeignKey('direction_surveys.id'))
    mooring_id:Mapped[int]=mapped_column(ForeignKey('moorings.id'))
    code:Mapped[str]=mapped_column(String(60),unique=True)
    bearing:Mapped[float]=mapped_column(Double)
    observed_at:Mapped[str]=mapped_column(String(40))
