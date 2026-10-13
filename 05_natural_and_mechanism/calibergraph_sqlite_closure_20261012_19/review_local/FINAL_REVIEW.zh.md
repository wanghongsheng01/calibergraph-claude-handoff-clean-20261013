# 19 包证据闭环独立后审

结论：**PASS，无未解决的must-fix**。此次后审只读保存的执行结果、源文件与哈希，未重跑SQL、目标导入、parser或solver。独立验证脚本此前已由主执行器执行，回放和COUNT结果分别保存在首段部分结果与补完段结果中。

## 保留失败，分段记录

首段0.10004812525585294秒，8个作者SQLite候选与8个独立新库重建均通过；随后额外SQLParser导入请求mo_imports监控线程，被Thread.start门阻止。COUNT矩阵尚未开始，补丁未生成，独立COUNT因此FileNotFound。原independent_validation.json顶层FAILED及两个错误完整保留，不能称首段整体PASS。

补完段仅删除不必要的parser导入和演示，保留真实ExpressionEncoder、原矩阵及SQLite计数oracle；独立wrapper只调用validate_count_ast，没有重跑8个候选。补完段0.04989416617900133秒，两段累计实际执行墙钟0.14994229143485427秒，小于用户总60秒限制。不是同一连续批次。用户原要求为总60秒/一线程；连续单批是作者自行增加的执行计划，其修订已明确记录。两个收据线程数均为1，没有子进程/网络事件或solver调用。首段发生的是被阻断的线程启动请求，不能写“从未尝试启动线程”。

## 原SQL/DDL独立回放结果

| 构造 | 每表最大N / 总源行 | gold | predicted |
|---|---|---|---|
| 1073_invalid_date | 1 / 2 | 1 | 0 |
| 1073_nullable_pk | 1 / 2 | 0 | 1 |
| 45_text_N1 | 1 / 2 | ('S','x') | ('S',0.0) |
| 45_large_int_N1 | 1 / 2 | ('S',9007199254740993) | ('S',9007199254740992.0) |
| 45_group_N2 | 2 / 4 | ('S',1), ('S',3) | ('S',2.0) |
| 45_bag_N2 | 2 / 4 | ('S',0) 两份 | ('S',0.0) 一份 |
| 1526_N1 | 1 / 4 | 1.0 | NULL |
| 1526_sum_scalar | 3 / 7 | 0.8333333333333334 | 0.5 |

8例均由独立脚本根据作者保存的完整columns/stored_rows，在另一全新内存库执行冻结原DDL、自行插入、校验全部源表列和精确存储类型/NULL、显式NN及INTEGER PK、PK/UNIQUE、FK和integrity，再执行原SQL并比较无序bag。源码hash与09候选目录独立核对。nullable INT PK分支没有被擅自强化为NOT NULL；大整数比较没有先转float，0/0例保留bag重数。因此这8个合成数据库现在是**已独立回放的源合法反例**，但仍非官方原反例库、真实业务数据或新增自然任务。

## COUNT(*)真实AST单测

作者原/补丁各28边界，独立原/补丁各28边界，逐项状态和预期计数一致。原无FILTER分支产生4个值不符；FILTER且bound=2的12个组合产生Plus(Bool,Bool)类型错误。bound=1单个布尔项可能由EnsureInt转换正确，不能概括为所有带FILTER都错。

最小补丁仅把一条append移出filter条件，并改为`If(Not(deleted), Int(1), Int(0))`整数指示。28个补丁边界全部通过；独立脚本确认全文只改变该语句，源码原hash未变。补丁SHA256为76b80b04bfb55b7f0a3f788ce44744831c29adf17d14bf771bf0089e6189b4cf。

测试直接调用真实ExpressionEncoder并检查其AST，没有solver。parser路径因首段导入被阻断，**仍未动态验证**；完整自然查询流水线也未验证。补丁只在隔离内存副本测试，未并入既有基线，不能写成已有强基线已修复或四例均已获Polygon验证。

## 冻结与事后保全边界

首段369项、新段378项hash均与实际文件一致；两个STARTED绑定各自FREEZE，两个CLOSED绑定实际收据。新段freeze未预先纳入旧ATTEMPT_STARTED，此缺口不事后改写freeze。已根据冻结run_once中确定的JSON字段/顺序/indent及旧FREEZE hash重建旧marker预期字节，与实际逐字节相等；这是**事后验证**，不能称其曾包括在378项运行前锁定中。

技术方案/控制器已有审阅PASS消息；最后附加hash覆盖检查因旧marker遗漏而未生成最终运行前准入JSON。执行时间与该补充建议交叉，后审如实保留这一流程边界，不追补虚假的运行前文件。该记录完整性问题不改变保存的SQLite/AST结果。

已有4/8有效开发例的Polygon bounded-run覆盖不变；新增SQLite回放不增加这个分母或覆盖数。1526的来源日期冲突仍不认证业务意图。此次是语义证据闭环与局部工程缺陷确认，anti-masking关闭，未产生方法创新证据。

逐结果、资源、hash与限制见FINAL_REVIEW.json。
