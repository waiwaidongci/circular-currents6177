from pydantic import BaseModel,Field,model_validator
class RunInput(BaseModel):
    name:str=Field(min_length=3,max_length=160)
    survey_id:int=Field(gt=0)
    mooring_a_id:int=Field(gt=0)
    mooring_b_id:int=Field(gt=0)
    permutations:int=Field(default=499,ge=99,le=999)
    seed:int=Field(default=157,ge=0,le=2147483647)
    @model_validator(mode='after')
    def distinct(self):
        if self.mooring_a_id==self.mooring_b_id:raise ValueError('两组浮标必须不同')
        return self
