from pydantic import BaseModel,Field
class SurveyInput(BaseModel):
    code:str=Field(min_length=2,max_length=40,pattern=r'^[a-z0-9-]+$')
    name:str=Field(min_length=3,max_length=120)
    period:str=Field(min_length=2,max_length=60)
    description:str=Field(default='',max_length=1200)
class SurveyPatch(BaseModel):
    description:str=Field(max_length=1200)
