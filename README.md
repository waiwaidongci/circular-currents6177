# 霁岬浮标流向研究册

将跨零流向、双峰和集中度放回圆周上，比较两座浮标的整体分布，再记录独立补测建议。

霁岬海洋观测组有14位研究人员。过去用表格直接平均角度：350°和10°被算成180°，相反双峰被均值掩盖，连续观测的自相关被忽略。这里承接机构级合成角度，替代圆周描述、分布比较和审阅交付；下游按另行约定的独立采样协议补测。全部是合成研究数据，不是实时航行或天气服务。

## 启动

```sh
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose exec -T backend python -m scripts.seed_demo
```

[前端](http://localhost:18229)、[API](http://localhost:19229)、[API文档](http://localhost:19229/docs)。Nginx将/api剥除后代理给backend，直连后端不带/api。结束时`docker compose down -v --remove-orphans`删除本题演示数据与卷。全批最多同时运行3题。

| 账号 | 权限 | 典型动作 |
|---|---|---|
| admin@jijia.demo | 六页、写入、审阅 | 编辑浮标说明、批准/退回观察说明 |
| analyst@jijia.demo | 六页、研究、起草 | 导入角度、排队计算、补测说明，不能审阅 |
| viewer@jijia.demo | 六页只读、获批导出 | 阅读结果/审计，下载获批CSV |

共用密码`Jijia2026!`；随机salt的PBKDF2-SHA256和8小时JWT。演示密钥与账号仅供本地使用。

## 一天的研究

1. 09:00 林霁核对`backend/scripts/seed_demo.py`生成的调查口径：0°北、顺时针、角度范围[0,360)。
2. 09:10 选择“跨零流向研究”，查看岬口A/外礁B各120条合成独立观测。
3. 09:20 预先选499次标签置换、seed157，提交worker计算并保存两组原始输入快照。
4. 09:25 阅读圆周均值、R、R₂、κ和12扇区比例；0–30°与330–360°在图上相邻。
5. 09:30 对“同向集中度研究”再比较整体分布：实测均值39.40°/45.52°，κ2.015/16.063。
6. 09:40 对“相反双峰研究”运行：一阶合向量近零，均值不定义，图不画均值线与无方向的单峰模型。
7. 10:00 起草补测说明，记录独立时段和方向标定复核，不将p解释为成因。
8. 10:10 沈岬以admin审阅，许帆以viewer下载含输入SHA256的CSV。

## 实体、页面与代码

DirectionSurvey、Mooring、BearingReading、DirectionRun、ObservationNote分别贯穿model/schema/service/controller/route和前端API/store/页面。调查/浮标/采样code唯一；角度使用MySQL DOUBLE。每期每浮标最多250条，可新增调查、导入JSON角度、编辑调查备注；浮标说明仅admin可编辑。

六页：研究首页、浮标与采样、圆周研究、方向与差异、观察说明、研究留痕。PolarPlot在首页和结果页复用；RunSelect/PageHeading/StatusBadge/ErrorNotice共享；useTask/usePolling管理恢复与刷新。JWT角色、Redis按来源分钟配额、全局错误处理和审计组成横切模块。

后端共享枚举`src/constants/enums.py`的Role用于routes，RunStatus用于run_service，NoteStatus用于note_service；前端`src/constants/enums.ts`的roles/states/fitStates用于App/StatusBadge/Results。auth和research为响应式store。目录按工程基线分为routes/controllers/services/models/schemas/middlewares/utils/constants/config及前端api/stores/types/components/common/hooks/pages/router/utils/constants。

## 圆周与集中度

C=mean(cosθ)，S=mean(sinθ)，R=sqrt(C²+S²)；方向atan2(S,C)归一到[0,360)。[350°,10°]得到0°和R=cos10°。R₂=|mean(exp(2iθ))|用于描述相反双峰，不是拟合优度检验。

R<1e−8时均值方向为空、单峰集中度MLE为0；1−R<1e−8时集中度退化，κ为空。其余κ解I1e(κ)/I0e(κ)=R，scaled Bessel避免大κ溢出。12扇区模型概率由von Mises CDF差得到，观测比例和模型概率分列；不保证单峰模型能拟合双峰。极坐标连接扇区中点，不是时间轨迹；均值线按R相对缩放，与概率径向刻度不同。

参考[SciPy circmean](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.circmean.html)和[vonmises](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.vonmises.html)。本项目数值零合向量主动返回null，避免任意角度。

## Energy与置换

单位圆弦距d(x,y)=2|sin((x−y)/2)|。V统计量为：

`E=2*sum cross d/(n*m)−sum within A d/n²−sum within B d/m²`

组内包含对角零，与去对角U统计不同；微小负浮点误差截为0。拼接观测后随机交换标签，固定两组大小，保存全部置换值；上尾p=(1+达到或超过观测次数)/(B+1)，比较含1e−12容差。输入按采样code稳定排序，固定seed和参数可完整复算。+1口径参考[SciPy permutation_test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html)。

[0,0]对[180,180]的E=4，六种固定大小分组中两种达到该极端，精确随机化参考p=1/3；随机999次近似此值。[0,180]对[0,180]的E=0且p=1。

每组2–250有限角度、99–999置换；同浮标不得同时引用。360、NaN、Inf、bool等非法角度返回422；空组保留明确failed任务。研究保存原始输入快照、配置、零分布和SHA256，新增采样不会改写旧结果。

## 技术与配置

| 层 | 实现 |
|---|---|
| 前端 | Vue3.5.45 / TypeScript / Vue Router / Vite6.4.6 / Nginx1.27 |
| 后端 | Python3.11 / FastAPI0.115.6 / SQLAlchemy2 / PyMySQL / PyJWT |
| 计算 | NumPy2.1.3 / SciPy1.14.1 |
| 异步 | Redis7 AOF，单Python消费者，DB任务状态 |
| 数据库 | MySQL8.0，连续数值DOUBLE |

五服务恰好frontend/backend/worker/db/redis，均有健康检查；backend/worker依赖db/redis healthy，frontend依赖backend healthy。数据库、Redis和共享artifacts命名卷。COMPOSE_PROJECT_NAME=circular-currents；FRONTEND_PORT/BACKEND_PORT/DB_PORT=18229/19229/17729，另有MYSQL_DATABASE/USER/PASSWORD/ROOT_PASSWORD、JWT_SECRET、SEED_DEMO，见.env.example。中文父目录可启动。

SEED_DEMO=true自动seed，异常只记日志；脚本可独立执行。初始3账号、2浮标、3期×2×120=720角度、1研究和1批准说明；自然键只增缺失，不覆盖备注或已有研究。固定seed157/158/159生成三种形状。QA新增调查、运行和说明与seed数量分开记录。

本地开发启动db/redis，安装requirements并设DATABASE_URL/REDIS_URL/JWT_SECRET，运行`uvicorn src.main:app --reload`和`python -m src.worker`；前端`npm ci && npm run dev`，/api代理19229。迁移目录说明metadata初始化，无生产增量升级。测试/CSV/截图/TESTING在批次test-artifacts/gb-0025；MIT见LICENSE。

## 已知差异

- 合成独立角度，不连接设备；真实连续观测的自相关未经处理不能直接套iid标签置换。
- von Mises单峰描述，无均值/κ置信区间；R₂为描述阈值，少量观测尤其不稳。
- energy比较分布，小p不代表效应大小或成因；重复研究未作跨研究多重校正，不自动行动。
- JSON输入已规范角度，不把未知角度归零；每组最多250条/999置换，未做生产压测。
- 单worker无running恢复/事务outbox，中断需另建任务；metadata首建表，Google字体离线回退。
