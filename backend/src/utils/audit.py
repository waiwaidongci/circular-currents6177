from src.models import Audit
def record(db,user,action,target):
    db.add(Audit(actor=user.email,action=action,target=str(target)))
