from pydantic import BaseModel,Field,field_validator
class BearingInput(BaseModel):
    code:str=Field(min_length=2,max_length=60)
    bearing:float=Field(ge=0,lt=360,allow_inf_nan=False,strict=True)
    observed_at:str=Field(min_length=2,max_length=40)
class BearingImport(BaseModel):
    survey_id:int=Field(gt=0)
    mooring_id:int=Field(gt=0)
    readings:list[BearingInput]=Field(min_length=1,max_length=250)
    @field_validator('readings')
    @classmethod
    def unique(cls,rows):
        if len({r.code for r in rows})!=len(rows):raise ValueError('采样编号重复')
        return rows
