import csv,io
from sqlalchemy import select
from fastapi import HTTPException
from src.models import ObservationNote,DirectionRun
from src.constants.enums import NoteStatus
from src.utils.audit import record
from src.utils.serializers import serialize
def listing(db):return [serialize(x) for x in db.scalars(select(ObservationNote).order_by(ObservationNote.id.desc()))]
def create(db,data,user):
    run=db.get(DirectionRun,data.run_id)
    if not run:raise HTTPException(404,'研究不存在')
    if run.status!='completed':raise HTTPException(409,'仅已完成研究可形成观察说明')
    if db.scalar(select(ObservationNote).where(ObservationNote.title==data.title)):raise HTTPException(409,'说明名称重复')
    note=ObservationNote(**data.model_dump(),created_by=user.id);db.add(note);db.flush();record(db,user,'note.created',note.id);db.commit();return serialize(note)
def review(db,id,data,user):
    note=db.get(ObservationNote,id)
    if not note:raise HTTPException(404,'观察说明不存在')
    if note.status!=NoteStatus.DRAFT:raise HTTPException(409,'观察说明已审阅')
    note.status=NoteStatus(data.decision);note.review_comment=data.comment;note.approved_by=user.email;record(db,user,'note.'+data.decision,id);db.commit();return serialize(note)
def export(db,id,user):
    note=db.get(ObservationNote,id)
    if not note:raise HTTPException(404,'观察说明不存在')
    if note.status!=NoteStatus.APPROVED:raise HTTPException(403,'仅已批准说明可导出')
    run=db.get(DirectionRun,note.run_id);r=run.result;out=io.StringIO();writer=csv.writer(out);writer.writerow(['note','survey_id','group_a_n','group_b_n','mean_a_degrees','mean_b_degrees','energy','permutation_p','fingerprint','interpretation','action','boundary']);writer.writerow([note.title,run.survey_id,r['a']['n'],r['b']['n'],r['a']['mean_bearing'],r['b']['mean_bearing'],r['energy']['statistic'],r['energy']['p_value'],r['fingerprint'],note.interpretation,note.action,r['interpretation']]);record(db,user,'note.exported',id);db.commit();return out.getvalue()
