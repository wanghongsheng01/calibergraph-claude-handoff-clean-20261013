# 窄合同语义桥 v1：待独立审阅、未执行

这是独立目录中的诊断实现，不修改官方源码、既有实验或论文。修复来源为已定位的 literal-left 有序比较方向错误；修复本身不构成论文级创新。当前没有通用证书，没有性能、自然缺陷发生率或泛化结论。

## 明确支持范围

完整物理 schema 仅 `INT`，表列名为大写 ASCII 简单标识符且不得含 `__`；此外所有编码 `TABLE__COLUMN` 必须唯一，且按官方首个 `__` 拆分后精确回到原表列。这样拒绝 `A_` 表与 `B` 列导致的歧义，不只检查字符串中没有 `__`。输入根节点只接受显式 `None` 或 conjunction list；节点只接受 `not_null`、`and` 以及恰好一个 Python 整数字面量和一个单列引用的 `lt/lte/gt/gte/eq/neq`。布尔、浮点、列列比较、PK/FK、OR、日期及其他节点均整体 `UNVERIFIED_CONTRACT`，不把支持的局部当作完整合同。

这里的比较要求引用列每一物理行均非 NULL 且谓词为真；这是明确注册的严格谓词 IC，不是 SQL `CHECK` 允许 UNKNOWN 的惯例。参考 emitter 保持原始左右顺序，独立具体数据库 evaluator 同样保持原始顺序。normalizer 仅在副本中把 literal-left 改为 column-left 并反转有序比较方向；原始 AST 与每个叶节点的映射保留。

## 诊断与分母

`fixtures.json` 注册 N1/N2 各 17 项，共 34 项：每个 N 的六比较 × 两方向，加 none、not_null、AND、OR 拒绝控制和 primary 拒绝控制。30 项为支持片段，4 项为明确拒绝控制。每项都有 4/5/6/NULL 固定数据库；N2 另有 [4,6] 和 [6,NULL]。这些均为已暴露的构造诊断，不是 held-out 或人工业务金标。

每次入口只执行一个指定 case，报告保留全部 34 项注册状态；其余为 NOT_RUN。每个求解槽及固定数据库也在执行前登记。错误、unknown、资源中断和未运行不得从分母删去。预期值是数学注册值，只有实际回执才是运行结果。

另有 3 项纯 admission 回归，在任何目标/native 导入之前检查：跨表编码碰撞、单表不可逆编码均拒绝；正常表和首下划线列可逆编码仍接受。这 3 项单列报告，不加入 34 项 solver 分母，不冒充 SQL 语义证据。独立审阅在第一版发现此 P1，旧哈希与修复记录保留在独立审阅报告。

流程为：实际官方 source-text parser 校验 AST（文本只覆盖 `< <= > >= !=` 和 not-null；`eq` 只走 JSON API，绝不声称 parser 支持 `=`）；建立完整 N1/N2 基表；在未调用被测 IC 编译器前捕获 base-only type/exact-row facts；检查 base SAT 和不可删除行；独立发射原始顺序参考；原版 emitter 分别编译原 AST/normal AST，每次恢复基础 facts；在 base-only 上检查两种 XOR；用固定数据库绑定全部 NULL/value 并检查参考与修正表达式；另查参考合同 SAT。

`lt_literal_left_N1/N2` 还在独立参考合同下运行真实官方 `Environment.analyze`：`SELECT SUM(T.A) FROM T WHERE T.A < 5` 对 `SELECT SUM(T.A) FROM T`。SAT 必须解码完整数据库、独立核原合同、通过已锁 v4 int64 域门，然后回放原 SQL 并保留完整输出。SQL 回放使用 SQLite，是执行 oracle；合同 evaluator 不是第二个 SQL 引擎。

## 仅由主任务执行

独立审阅通过前不要执行以下入口。本目录目前仅做 stdlib AST/JSON/hash 静态核验，未 import 自写模块、目标、native 或求解器。

使用现有 `.venv/bin/python -B -I -S` 调用 `supervise.py`，传入 `--runtime-lock` 指向 `experiments/v4_registration_01/runtime_paths_v4.json`、`--runtime-lock-sha256 29220d333a6a3f9812ab2c24aecd7877f7cf5c9e919e80b612f880bf1dc92f1f`、本目录 `MANIFEST.json` 的实际 `--manifest-sha256`、`--case-id lt_literal_left_N1`、以及本目录 `runs/` 下从未存在的新 `--out-dir`。然后独立检查回执再执行 N2；全队列由主任务顺序调度，禁止本工具自动并发。

每次只有一个计算 child：累计 CPU soft/hard 为 14/15 秒，child 内墙钟警报 24 秒；supervisor 在 child 墙钟 25 秒停止，自身内部 26 秒警报兜底。RSS 1 GiB 为每 50 ms 自身 `proc_pidinfo` 观察 child 的软门，不是硬 RSS 上限；child checkpoint 另查 ru_maxrss。初次解释器启动不包含在其自身计时内；supervisor CPU 不包含在 child CPU 限额。保留实际线程观测，不把 Python 线程枚举当原生单线程证明。每个求解检查最多 1200 ms 且共享剩余 CPU/墙钟预算，pair 使用共享剩余预算。资源停止后最后未保存效果为未知。

`CODE_MANIFEST.json` 与 `FIXTURE_MANIFEST.json` 分别锁代码和固定输入；根 `MANIFEST.json` 锁入口、参考模块、完整 fixture、借用的 common、官方 emitter/parser 和 v4 kernel。已有 runtime lock 再锁完整依赖与源文件。报告/日志只写新 runs 子目录，不改锁定文件。上传/push 在本任务禁止，未进行外部备份。
