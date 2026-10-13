# 20 轮独立最终审查

结论：**P3 在本轮明确限定的 COUNT(*) 工程测试内通过，无必须修复项。** 审核状态为 `PASS_WITH_DISCLOSED_PRESERVATION_EXCEPTION`：科学结果通过，同时保留前两段各一个未执行辅助脚本的冻结差异，不能称所有历史冻结项均未变化。

## 已执行证据

003 经真实 `SQLParser.parse/parse_query`，再调用真实 ExpressionEncoder，以及 FProject；分组案例先调用 FGroupBy。测试给定具体输入、分组和输出赋值，严格检查 AST 类型，并求值全部生成的算子约束，最后与 SQLite 输出 bag 比较。独立脚本在同一控制段新建 SQLite 数据库，并用另一套 Python COUNT 参考核验四版本共 168 条记录。本次后审只读交叉核对这些记录及绑定结果哈希，未再次执行 SQL、parser 或 solver。

| 版本 | 28 项解析表达式矩阵 | 14 项真实算子链 |
|---|---|---|
| original | 12 PASS / 4 MISMATCH / 12 ERROR | 7 PASS / 6 MISMATCH / 1 ERROR |
| P1 | 28 PASS | 9 PASS / 5 MISMATCH |
| P2 | 28 PASS | 11 PASS / 3 MISMATCH |
| P3 | 28 PASS | 14 PASS |

P1 修复非分组 COUNT(*) 的 append 缩进及整数指示。P2 另为 group COUNT(*) 加入 FILTER 的非 NULL/真值守卫；已有组在 FALSE/NULL FILTER 后输出 0，组不会消失。P3 再修复三处聚合 FILTER 入口的裸标识符解析：`WHERE x` 原被解析为 Literal('x')，新路径为 Attribute('x')。P1/P2 在此路径的错误输出如实保留；例如非分组列过滤原来计 3，SQLite 为 1，P3 为 1。

001 因默认 Python 3.9 不支持原代码类型注解而导入失败；002 使用 3.12，保留了 Implies 字段读取错误及测试 Env 缺 string_hash 的未完成结果。003 新脚本修正测试设施，保留相同 SQL、数据及每版本 28+14 分母。初审也遗漏了这些问题，并误判 singleton Bool 的最终类型；ExpressionEncoder 外层 EnsureInt 使 bound1 FILTER 能通过。纠正记录见 STATIC_ADMISSION_V2，旧记录不改。

## 冻结与资源

003 的 541/541 项冻结哈希匹配，STARTED 绑定匹配，执行的作者及独立脚本均匹配。001 为 477/478 项、002 为 480/481 项匹配；唯一差异都是未执行的旧 `review_local/verify_results.py`。早期冻结发生于该脚本准备期间，随后增加一行 `result = {'status': 'INTERRUPTED'}`，避免异常退出时 finally 引用未初始化变量。只在内存文本中去掉此行，即可重建早期冻结 SHA256 `1b1f64a3…`；当前文件为 `3c9b715f…`。001/002 的脚本列表均仅含 parser_test.py，没有执行旧 verifier。此差异是已披露的并发准备问题，不回改 freeze 或旧脚本掩盖。所有真正已执行输入均匹配。

三段实际执行墙钟分别为 0.096648375、0.3479476668871939、0.4025717079639435 秒，累计 **0.8471677498511374 秒**，小于共同 60 秒预算。各收据线程数 1、禁止事件为空、solver 调用 0；最大记录 RSS 为 60,489,728 字节。共同锁、load 门和预算绑定检查一致。RSS 保护是虚拟 CPU 定时器采样后停止，不是操作系统硬内存上限。

## 历史影响与限制

重新核对四例原 SQL/DDL 哈希、8 份历史结果、14 份保存 SMT 及冻结编码源码，均未变。#750 走 AVG→安全 Count helper，#319/#1172/#1261 走 Count_Distinct；四例均无 GROUP BY/FILTER，因此 P1/P2/P3 不触及其历史路径。#750/#1172 的既有原 SQLite 反例仍成立；#1261 仍只是已审核 N≤1 范围的有界结果。自然开发例 Polygon 完成覆盖保持 **4/8**，本轮没有新增 solver 实验。

本结果是 **real SQLParser + FGroupBy/FProject 的具体固定赋值公式验证**，不是完整 Environment.check/QueryEncoder 管线，也不是编码一般正确性或完备性证明。mo_imports 的后台监控线程被明确替换为同步测试替身，真实 import/export 仍执行且未解析 exports 为 0，不能称无适配部署验证。

28 项矩阵含物理 bound0；14 项算子链的空输入用至少一个 deleted 槽表示。P3 只承诺本轮整数列、NULL 和常量条件的 COUNT(*) FILTER 边界。带引号字面量保持仍只有静态审查证据；其他 grouped aggregate FILTER、一般 SQLite 字符串数值转换不在修复声明内。合成表 t 的测试也不替代自然案例原 DDL 完整约束 C 的既有验证。

精确文件哈希、冻结差异及统计见 FINAL_REVIEW.json。本次后审未修改任何旧包、冻结文件或既有结果。
