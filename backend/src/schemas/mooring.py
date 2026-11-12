from pydantic import BaseModel,Field
class MooringPatch(BaseModel):
    description:str=Field(max_length=800)
