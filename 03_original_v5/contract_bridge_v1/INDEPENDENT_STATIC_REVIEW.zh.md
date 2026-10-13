# 合同桥接 v1 独立静审

终审对象：MANIFEST SHA `32ee11faea4fee939964cd4ae03a9435d2ebe35877cecd221d7e65b2da30f3dd`。当前 34 个注册案例（30 支持、4 明确 UNVERIFIED）未发现剩余 P0/P1 阻断。审阅仅静态读取/AST/JSON/hash；未导入或执行目标、native、solver。

初轮发现并保留的 P1：`A_.B` 与 `A._B` 可编码成同一 `A___B`，且单表 `A_.B` 已不符合上游 first-separator 拆分。作者二次冻结已在 `prepare` 逐列检查编码唯一性及拆分往返一致性，任一失败整 schema UNVERIFIED。原 34 主病例分母保留；另注册 3 个纯 admission 回归，明确不算 solver 实验。旧哈希、反例与修复证据全部保留在同名 JSON 的两个 review rounds 中。

已核对的关键路径：

- 参考 SMT 与具体数据库 evaluator 均保留原始操作数顺序；只在规范化副本中交换并反转有序比较，NULL 不计严格合同 true，eq/neq 控制保持对称。
- 在加入被测 IC 前保存完整 base-only facts，先要求 SAT 与不可删除基行；分别编译原始/规范化 IC 后恢复基础事实，再在 base-only 上查 XOR，避免用错误合同掩盖差异。
- 固定数据库检查完整 table 集合、实际行数、行宽与全部 NULL/value 单元格；构造常量使用 fastbinding 所需十进制字符串及固定 context。
- 两个原 SQL pair 使用独立参考合同；SAT 模型须满足完整事实与实际 assertions，再经独立合同具体判值、v4 int64 域门及未替换的 SQLite SQL 回放。
- 拒绝、错误、unknown、资源停止与 NOT_RUN 均保留；每 child CPU14/15、墙时24，supervisor child25/内部26秒，RSS为采样软1GiB。

执行后须同时核对无 `stop_reason`、exit 0 和预期 worker 终态，不能把 supervisor `EXITED` 或预期拒绝当等价成功。完整物理合同结论还依赖 runner 的类型/行数/存活门，不能只引用 reference 的 `holds`。当前两条 pair SQL 静态上均简单安全；若扩展到任意 SQL，应在 analyze 前增加共享 raw-frontend gate。此诊断不提供通用证书、自然缺陷率、真人金标或新贡献结论。
