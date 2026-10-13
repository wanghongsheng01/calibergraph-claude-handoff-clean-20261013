# 固定数据库 oracle 脚本独立静审

对 `fixed_oracle_check.py`（SHA `8c03887df0f80e284695ea9485970deeac5d1a834bf9ec289c3ba4690fe30adb`）及其冻结注册的 12 例 / 21 条查询，未发现 P0/P1。仅静态审阅，未导入或执行目标/native，原件未改。完整 SHA 与逐处行号见同名 JSON。

- 固定绑定使用 `constants.Not` 和 `constants.IntVal(str(value))`，符合实际 fastbinding/context。全部 schema（包括未查询的 E）、行数、行宽及 NULL/整数单元格均参与完整 facts/IC 的 SAT 检查，再进入回放。
- 原始 SQL 未替换。`common.guarded_replay` 先 raw gate、真实 parse/recognize、整数域审计；只有 SAFE 才执行 SQLite。注册的 18 safe、3 unknown 预期自洽，包含 2^63 聚合溢出、2^63−2 安全边界及零不掩盖中间溢出的控制。
- 监督为每子进程 CPU14/15秒、wall24/父25秒、总89秒、RSS采样软1GiB；未运行、unknown、错误保留。

非阻塞加固两项：① 为按行/列绑定的 `zip` 显式断言符号长度（当前固定源码保证一致）；② 最终 control match 再要求无 `stop_reason` 且 worker.status 为 COMPLETE，以封住罕见退出/kill观测竞争。父任务应将任何 resource-stop/stop_reason 记录排除在成功控制之外。

SAT只验证官方实际发出的合同，不证明任意原始IC翻译正确；这些固定输入不使用已知literal-left方向问题。构造控制通过及预期溢出拒绝均不是自然缺陷率、真人金标、等价算法成功或性能优势。
