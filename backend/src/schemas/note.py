from pydantic import BaseModel,Field
from typing import Literal
class NoteInput(BaseModel):
    title:str=Field(min_length=3,max_length=160)
    run_id:int=Field(gt=0)
    interpretation:str=Field(min_length=8,max_length=2000)
    action:str=Field(min_length=5,max_length=1200)
class NoteReview(BaseModel):
    decision:Literal['approved','rejected']
    comment:str=Field(min_length=5,max_length=1200)
