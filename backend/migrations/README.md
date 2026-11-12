# Schema

## Schema v2（当前）

首次由SQLAlchemy metadata建立users、audits、direction_surveys、moorings、bearing_readings、direction_runs、observation_notes。调查/浮标/采样code唯一，角度为MySQL DOUBLE，运行和说明通过外键关联。

direction_runs在v1基础上新增三列支撑中断恢复与幂等执行：

- `input_snapshot` JSON NULL：受理时固化的两组采样（a/b，含code、bearing、observed_at），计算与恢复只读取该快照，补录采样不回溯旧研究。
- `claimed_by` VARCHAR(64) NULL / `claimed_at` DATETIME NULL：执行租约。worker以条件UPDATE原子认领queued任务；恢复协调将租约过期（默认120秒）的running重置为queued并重新入队。完成/失败写回均带claimed_by条件，旧执行者迟归无法覆盖。

三列均为内部状态，不进入对外序列化，既有研究结果JSON格式不变。

## 升级约定

本合成数据项目没有生产增量迁移；从v1升级可重建表，或对既有direction_runs执行等价的 `ALTER TABLE ... ADD COLUMN input_snapshot JSON NULL, ADD COLUMN claimed_by VARCHAR(64) NULL, ADD COLUMN claimed_at DATETIME NULL`（既有行快照为空时，compute会回退按受理参数即时取数一次）。一次性重置可down -v后重建。
