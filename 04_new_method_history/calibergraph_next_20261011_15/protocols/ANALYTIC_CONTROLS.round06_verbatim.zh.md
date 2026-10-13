# 第六轮测量前的已知语义控制

这是作者侧原文推导，尚待独立审阅；不是新算法，也没有测量所谓“零耗时基线”。本协议不允许从冻结 VeriEQL 的耗时或超时直接推出科学困难或方法机会。

- dev03_10 / 1264：两式的 CASE 仅有显式 ELSE NULL 与省略 ELSE 的区别；内连接左右换序、别名重命名；投影 DISTINCT PAGE_ID 与 NOT IN 子查询一致。在所述整数、标准 NULL/bag 语义下，已知 CASE 默认 NULL 和内连接换序规则给出等价。完整 C 保留，但这项推导不依赖额外加强 C。
- dev03_15 / 1421：QUERIES LEFT JOIN NPV 与 NPV RIGHT JOIN QUERIES 表达同一外连接；两个分量的 row equality 与对应等式的 AND 有同样三值逻辑；两个参数的 IFNULL 与 COALESCE 在已限定整数输入上相同。投影相同，因此已有外连接换序及函数恒等式给出等价。不得把 SMT 对此多花时间包装为强语义控制无法解决的问题。
- dev03_07 / 1173：先保留 DATE、布尔 SUM、除法与 ROUND 的语义边界。本批不以未经认证的 SQLite 方言回放来证明其官方编码正确，也不据此称自然缺陷。
- dev03_04 / 1468：保留 decimal ROUND、VARCHAR 及官方比较器提前退出边界。不得把其 query solver 未被调用当作求解困难，亦不得以排除该固定来源改善成功率。

四个来源均来自已暴露的开发数据；本批没有独立最终测试。本轮 retained method hypothesis 为 null（equitable quotient 直接先例且严格覆盖0/21），没有候选算法、性能对照实验或消融结果可报告。C-model sanity 是现成合法数据库采样的可执行控制，只检查生成/回放链；不能称生成反例方法胜出。

所有12单元结束或被资源门停止后，记录完整分母、C与query检查、原SQL回放、全阶段成本、未准入项及失败。若无实际query SAT model并通过独立C及原SQL回放，就明确“本批未验证查询反例生成成功”。如果只有已知语义恒等式或前端不足解释观测，不允许据此晋级新方法或盲目增大N。

SQLite 原始文档核查（本轮实际读取）：[CASE 无 ELSE 默认 NULL](https://www.sqlite.org/lang_expr.html#the_case_expression)、[row value 的 NULL 比较](https://www.sqlite.org/rowvalue.html#row_value_comparisons)、[IFNULL 等价于两参数 COALESCE](https://www.sqlite.org/lang_corefunc.html#ifnull)。它们支持限定 SQLite 回放语义；不代替对其他方言实现的证明，也不是本轮复算结果。
