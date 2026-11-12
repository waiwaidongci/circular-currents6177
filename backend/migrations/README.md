# Schema v1

首次由SQLAlchemy metadata建立users、audits、direction_surveys、moorings、bearing_readings、direction_runs、observation_notes。调查/浮标/采样code唯一，角度为MySQL DOUBLE，运行和说明通过外键关联。

本合成数据项目没有生产增量迁移；schema变更应另建正式迁移，一次性重置可down -v后重建。
