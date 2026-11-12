from sqlalchemy.inspection import inspect
def serialize(obj):
    result={}
    for col in inspect(obj).mapper.column_attrs:
        value=getattr(obj,col.key)
        result[col.key]=value.isoformat() if hasattr(value,'isoformat') else value
    return result
