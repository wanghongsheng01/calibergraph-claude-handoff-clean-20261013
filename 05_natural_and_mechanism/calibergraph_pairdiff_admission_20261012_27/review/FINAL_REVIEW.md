# 独立静态终审

结论：**ACCEPT_STOP_WITH_LIMITATIONS**。接受 `REJECT_AVAILABLE_WORKLOAD` 作为停止本轮、不实施窄原型、新增求解预算为 0 的决定。未发现需要阻止该停止决定的 must-fix。此结论不认证通用 SQL 编译器语义，不证明理论上无机会，也不构成性能输赢结果。

审查者未参与本轮作者工作。本次只阅读冻结材料、扫描器、已有记录及四份 Polygon 原源码，并用 Python 标准库独立重计和核对哈希；没有导入或运行 scan.py、sqlglot、Polygon，没有执行 SQL、SMT、benchmark、构造第二候选或改写作者材料。

## 核查结果

- 冻结一致：CODE_FREEZE 的 6 个文件、INPUT_FREEZE 的 3 个源文件及 parser wheel、FINAL_DECISION 的全部证据哈希、Polygon 的 4 个源码哈希均独立匹配。哈希一致可验证当前文件身份，不等于独立证明历史时间顺序。
- 分母闭合：25,528 条记录、25,528 个唯一 ID；10,568 条先排除，14,960 条进入 AST 流程；315 条准入，132 条整对相同，183 条非平凡，其中 138 条有 JOIN。所有记录的事件中没有 U/J 严格消去事件；零符合门槛。
- LeetCode 排除数 10,558 中，左 SQL 命中 10,557，右 SQL 命中 27；材料正确区分 SQL 重合与实际开发过整对，不把这些排除记录伪称为新的 final test。旧全库曝光已披露。
- 11 条原 SCANNER_ERROR 全为 TokenError；派生表透明改名，没有修改原记录或重新筛选。另 95 条 ParseError 与拒绝项保留分母。
- 四类、每类按 stable-ID SHA256 排名前三的 12 个代表均独立重算匹配；两侧 SQL 均与原来源行逐字一致。类别可重叠，12 是展示条目数，不是额外独立样本数。
- 预门槛确为至少 20 对、3 来源族、每对比两查询共享 DAG 少 2 节点且至少 20%，必须有 U/J 消去。扫描器未读取源 verdict/timing 作为选样条件。冻结文件当前一致支持未事后改门槛的记录链，但历史执行仍依据现存收据。

## 规则与实现

`difference` 的精确相同项归零、相同选择/投影向下传递差分、UNION ALL 的 Counter 多重集逐 occurrence 抵消，以及 JOIN 单边精确相同后的零乘积消去，符合所声明的局部 bag 差分规则。JOIN 的剩余乘积明确保留另一公共因子；没有用公共 JOIN 因子除法或注入性假设。分支与 JOIN 的 children tuple 保留重复边，节点集合只用于共享 DAG 计数，不把 bag 重数改成集合语义。两侧都变化的 JOIN 仅记描述性 identity 事件，不虚记收益。S-different 不生成错误的 NOT 谓词。

列引用解析为当前输入的位置，别名不作为值；关系排列、输出位置与 JOIN 参数次序保留。完整查询的 DISTINCT、聚合、outer/special JOIN、order/limit 等屏障在 compile_rel 前整对拒绝，未向屏障后传播差分。完整 C/schema 的成本不由静态 DAG 计数代表。

**非阻塞实现边界，后续若重新开发必须处理：** `scan.py:normname` 无条件 lower，并未检查 quoted 标记，也不接收方言参数。因此 PROTOCOL 中“quoted identifiers retain exact value / source-dialect normalization”的字面承诺并未完全由代码实现；当前供应 schema 的规范化不应外推为通用标识符保真。`scalar` 的比较分支还丢弃操作数类型返回值，未实现一般性的比较可类型检查或 totality 认证。它保留原谓词结构而不作强制转换重写，但不足以声称实现了完整的类型安全 SQL 编译器。本轮结论已限制为保守结构扫描，且零门槛收益，不因此启动修复、重扫或实验。若后续把 315 条用于语义正确性证明，这两点将成为 must-fix。

## Polygon 与结论边界

实际阅读 environment 的两侧解析/编码和非等价约束、QueryEncoder 的延迟 Initializer、Initializer 的独立算子标签与共享基础表标签、formula 的 label 序列化缓存，均支持 POLYGON_PATH_CHECK 的有限描述。没有证据允许声称 Polygon 不共享任何内容，也没有做全仓库缺失证明。

必要未来控制确实包含 B0 原版 Polygon、B1 公共 DAG 共享加单输出 tuple 重数差判别、C 仅添加前置差分编译。B1 未实现且未测量；节点数不能证明 SMT 或时间收益。引用的既有代数/单输出观察未被宣称为新颖性；本审查未新增文献核验。

0 U/J 只描述冻结来源、SQL 重合排除策略和 v1 fragment。JOIN 重排、等式交换、屏障后局部机会及被排除来源均未被穷尽；不能把“无合格样本”提升为“所有自然工作负载无机会”。RESULT 与 FINAL_DECISION 已明确这一点，故证据足以支持停止本轮。

交付：本文件与 FINAL_REVIEW.json。无停止决定相关的未解决阻塞；无需新增求解或重新扫描。
