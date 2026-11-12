import numpy as np,json
from sqlalchemy import select,func
from src.config.database import Base,engine,SessionLocal
from src.models import User,DirectionSurvey,Mooring,BearingReading,DirectionRun,ObservationNote
from src.utils.security import hash_password
from src.services.run_service import compute
def seed():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for role,name in [('admin','沈岬 · 观测负责人'),('analyst','林霁 · 圆周研究员'),('viewer','许帆 · 研究阅读者')]:
            if not db.scalar(select(User).where(User.email==role+'@jijia.demo')):db.add(User(email=role+'@jijia.demo',name=name,role=role,password_hash=hash_password('Jijia2026!')))
        for code,name in [('JJ-A','岬口A浮标'),('JJ-B','外礁B浮标')]:
            if not db.scalar(select(Mooring).where(Mooring.code==code)):db.add(Mooring(code=code,name=name,description='固定合成采样点；角度约定0北、顺时针。'))
        db.commit();moorings=db.scalars(select(Mooring).order_by(Mooring.code)).all()
        for j,(code,name) in enumerate([('cross-zero','跨零流向研究'),('opposite-modes','相反双峰研究'),('spread-change','同向集中度研究')]):
            survey=db.scalar(select(DirectionSurvey).where(DirectionSurvey.code==code))
            if not survey:survey=DirectionSurvey(code=code,name=name,period=f'2026-11-{j+1:02d}',description='合成独立角度样本，用于说明圆周口径；不用于航行。');db.add(survey);db.flush()
            rng=np.random.default_rng(157+j)
            for k,m in enumerate(moorings):
                if j==0:angles=np.rad2deg(rng.vonmises(np.deg2rad(350 if k==0 else 10),12,120))%360
                elif j==1:
                    half=np.rad2deg(rng.vonmises(np.deg2rad(25 if k==0 else 90),15,60))%360;angles=np.r_[half,(half+180)%360]
                else:angles=np.rad2deg(rng.vonmises(np.deg2rad(45),2 if k==0 else 15,120))%360
                existing=set(db.scalars(select(BearingReading.code).where(BearingReading.survey_id==survey.id,BearingReading.mooring_id==m.id)))
                for i,angle in enumerate(angles):
                    sample=f'{code}-{m.code}-{i+1:03d}'
                    if sample not in existing:db.add(BearingReading(survey_id=survey.id,mooring_id=m.id,code=sample,bearing=float(angle),observed_at=f'{survey.period}T{(i//6)%24:02d}:{i%6*10:02d}'))
        db.commit();run=db.scalar(select(DirectionRun).where(DirectionRun.name=='跨零流向 · 初始研究'))
        if not run:
            survey=db.scalar(select(DirectionSurvey).where(DirectionSurvey.code=='cross-zero'));user=db.scalar(select(User).where(User.role=='admin'))
            run=DirectionRun(name='跨零流向 · 初始研究',survey_id=survey.id,mooring_a_id=moorings[0].id,mooring_b_id=moorings[1].id,permutations=499,seed=157,created_by=user.id);db.add(run);db.commit();compute(db,run.id)
            db.add(ObservationNote(title='跨零采样 · 观察口径',run_id=run.id,interpretation='两组均跨过0度附近，圆周差异需与采样独立性一起阅读。',action='保持协议补采独立时段，复核传感器方向标定。',status='approved',approved_by=user.email,review_comment='只作合成统计口径示范，待现场复核。',created_by=user.id));db.commit()
        counts={name:db.scalar(select(func.count()).select_from(model)) for name,model in [('users',User),('surveys',DirectionSurvey),('moorings',Mooring),('readings',BearingReading),('runs',DirectionRun),('notes',ObservationNote)]};print(json.dumps(counts));return counts
if __name__=='__main__':seed()
