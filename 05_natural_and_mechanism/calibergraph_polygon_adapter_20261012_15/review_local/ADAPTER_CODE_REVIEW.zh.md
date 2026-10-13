# #1172 适配器代码独立复核

首次检查版本 SHA256：`33ee72718aab0772ac85b14bdd260961d8226ea9ce4b672549263d581de5a547`。

检查 `case1172_adapter.py`、`test_adapter.py` 及已保存 `TEST_RESULTS.json`。未执行作者测试，未导入 Polygon，未调用 solver。独立运行 `adapter_semantic_check.py`：150 个实际适配器原域交叉案例通过，4 个额外负例正确拒绝。

## 首次审查必须修复：TEMP 源表遮蔽

`validate_original` 的 sqlite_schema 签名、foreign_key_check 和 integrity_check 使用 main 模式，但原 SQL、N≤1 检查和 project_original 的表名未限定模式。TEMP 同名 table/view 可以遮蔽真正经过验证的源表。

最小复现：main.Patient 有 `(ID=1, SEX='M')`，main.Laboratory 空；执行 `CREATE TEMP TABLE Laboratory AS SELECT * FROM main.Laboratory`，再插入 temp.Laboratory `(ID=99, Date=0, T-BIL=2)`。原验证接受，原 SQL 输出 `[0,0]`，投影及固定提升后输出 `[1,0]`。这是输入模式解析校验漏洞，不是 N≤1 观察商理论反例。

修复建议：在验证开始时拒绝 TEMP 模式中遮蔽三个源表的同名 table/view，或拒绝所有 TEMP 用户模式对象。必须保留原 SQL 回放；仅将投影改为 main 限定名仍不足以解决原 SQL 的 TEMP 名称解析。增加回归负例确认验证拒绝这种连接状态。

## 其他检查结论

- 正向投影以 SQLite 存储后的列 SQL 比较生成类别；无 Python 原数值推测，能避开非法 UTF-8 原 TEXT 的宿主解码。
- 反向代码先完整校验抽象表、列、N≤1、类型、PK/NN 和两条 FK，再执行固定键/日期/未观察列规范化；没有补父行、补 NULL、改非法 FK 或删除行。
- 抽象 Int 上的宿主整数比较和无限精度键规范化与已声明商语义一致；原 SQLite 的 64 位键域由正向存储校验和反向固定 1 保证。
- 保留 3 表、64 列、7 条约束项；未观察列按 NULL 性保存。DATE 代表 0 没有被宣称为日期转换。
- `replay_lifted` 使用原 DDL、外键开启、固定插入、完整 C 校验与原 SQL 回放；延迟 FK 只允许前向引用插入顺序，不放宽最终 C。
- 已保存作者测试显示 217 个 T-BIL×SEX 组合（31×7），并非 217 种 T-BIL 值。其 parse/encode-only 防护代码在 search/solve_precise 入口抛出 BaseException，进程审计禁止子进程；这些记录只能作工程接线测试，不是科学求解结果。

具体 worker diff 尚未在首次代码检查中提供，故此报告不覆盖 worker 接线与科学计时流程。
