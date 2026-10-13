# 独立作者外审

结论：**必须修正（MUST_FIX）**。当前只有一项阻断：#750 的源预测原行字节与官方 strip 后输入未区分。抽样、分母、案例分类及静态边界在所核范围内通过；这不构成实验准入、方法效果或投稿就绪确认。

本审查由独立子任务完成，只读既有 JSON、SQL/DDL 文本和固定源码；使用 Python 标准库重算选择、哈希与 ZIP 成员字节，不导入研究代码或 SQL 解析器，不执行 SQL、SMT、生成器、基线、训练、网络访问或安装。**新增科学执行 0；新 test 0。** 未改作者文件，未另委派，未备份。审查覆盖 REPORT、SELECTION_PROTOCOL、extract_static、EXTRACTION_RECEIPT、CANDIDATES、SOURCE_CHECKS，以及补入的 CASE_ASSESSMENTS、SOURCE_BOUNDARIES、NEXT_STEP。

## 必须修正 R1：把原文件行与官方运行输入分开

REPORT 当前称10例 SQL“逐字核对同版本 dev.json/dail.txt”，SOURCE_CHECKS 的 `predicted_exact=true` 未写明比较采用官方规范化后的输入。独立字节比较发现：

- #750 的 dail.txt 原行（不含行分隔符）是 `SELECT AVG(weight_kg) FROM superhero WHERE gender_id = 2 `，末尾有一个空格，共57字节，SHA-256 `c737a4643d8b37df0240dcb0a3ce65932738bd7830390d1f415b53baaf505a03`。
- 官方 `scripts/disprove_bird.py` 组装输入时调用 `predicted.strip()`，官方 JSONL 和本包 predicted.sql 均为56字节，SHA-256 `f5c9d201cf3a407ec2a79fe2a7618a04e1d21a3343ec11ec098fc5b9022c0c32`。
- 其余9例 predicted 原行与包内一致；全部10例 gold 与 dev.json 字段 UTF-8 字节一致。全部10例 predicted 与官方 JSONL 字段以及 dail 原行按官方 strip 后的字节一致。

这不是 SQL 语义篡改或案例失效，不能因此换样。保留官方实际输入；修订 REPORT 和 SOURCE_CHECKS，明确比较层次、官方 strip 变换及 #750 的原行差异/哈希。限定复核这项后可重新给出最终结论。

## 已独立复核的证据

1. 不运行作者提取器，独立按固定哈希排序、EQ/NEQ/UNRESOLVED 顺序、每数据库至多2例、字面查询对去重和固定1172锚点重算，得到完全相同顺序：1172 → 319 → 1261 → 1490 → 750 → 1073 → 45 → 1526 → 26 → 1390。因此 #750 确为所选 NEQ 的第一条，随后才是 #1073、#45。协议和提取器哈希均与收据一致。文件内容与收据证明可复算性，单凭本地时间戳/哈希不独立证明协议曾先于作者查看所有内容；报告已承认旧结果暴露，不能解释为未见标签的预注册测试。
2. 全包1534：NEQ 853、EQ 572、SYNTAX_ERROR 97、UNKNOWN 10、TIMEOUT 2；词法池551：NEQ 364、EQ 140、SYNTAX_ERROR 41、UNKNOWN 4、TIMEOUT 2。分母无隐匿，#26 的引号内 `Count (` 假阳性保留，未事后替换。分层样本不可估计总体失败率。
3. 40个候选文件哈希、全部源哈希及 SOURCE_BOUNDARIES 中14个证据文件哈希通过；既有 ZIP 的 `disprove-bird.jsonl` 成员与提取源逐字节相同。10份 full-schema.sql 均等于同版官方 schema.json 的全部 DDL 经 `;\n` 拼接，表数分别3/4/3/5/10/7/3/5/3/8。full-C 只指已声明源约束，不包含业务常量，也不证明跨引擎类型保真。
4. #319 两 SQL 字面相同，可以作为真等价对照。#1261 的 Laboratory.ID→Patient.ID 外键、父表PK和同一连接/筛选谓词保证加入 Patient 不改变最终不同 ID 集合；COUNT DISTINCT 等价推导成立。#1490 保持静态等价候选标签，未把官方 EQ 一概当真。#1172 的旧回放结论与“9候选漏判”本轮仅继承既有证据，不是本次重新执行确认。
5. #750 给出的一个 gender、一个 superhero、其余表空的静态反例满足10表源C：未指定的其他 FK 可空，必需PK有值；源C没有 Female→id=2 业务约束。#45 的两组合法父子键、同 School 名称和成绩1/3可产生两行与一组的差异；所需非空字段可在不改变该推导的条件下补足，其余可空字段置NULL。两者都仅证明反例存在，没有证明生成器实际能找到；官方输出字符串不能恢复官方D。
6. 官方脚本只保存最多300字符的结果字符串，不导出 counterexample；main.py 对 SYNTAX_ERROR、UNKNOWN、TIMEOUT、NEQ 分支不同。#1526 的理由与 machine.py:726 的行变量绑定保护条件吻合，但没有轨迹证明更早根因。#26 的 frpm.Street 等列、#1390 的 expense.link_to_event 不存在；两者不是合法原查询对上的生成困难案例。
7. Polygon 的 AVG=sum/count、SMT div/Int cell、CAST返回原操作数、未知约束warning、MySQL重建省略原DDL约束和完整性失败只记录日志，均有固定文本源码支持。它们是语义与复核边界，不是这10例实测失败。UA/precise共享前端与约束映射，切 precise 不自动补足这些缺口。ParSEval官方测试只查阅存在性，未运行，不能报测试PASS。XData核心实现、类路径、实际10例成本仍未核实，保持未运行。

## 唯一下一方案的审查边界

NEXT_STEP 和报告一致，只保留 #750 + 字面 EQ #319，Polygon UA 与同commit precise，两臂相同N=1、类型域和完整约束，最多4个串行worker。ParSEval官方秒数未纳入公平速度比较，XData没有伪造运行。全1534条视作开发暴露、10例均 DEVELOPMENT、0新test 的定位合适，不可升级新机制或独立测试结果。

N=1使 #750 两侧AVG至多一个非NULL输入，确实排除多行小数平均这一问题，但仍须检查空输入NULL、整数范围/SQLite数值表示、字符串等值与具体化，以及全部10表PK/FK/非空映射。#319 的复合PK、两个指向 atom 的FK、字符串和NULL语义也须逐条准入。当前没有证明这些条件已完成。只能认证经原SQL/full-C复核的NEQ；UNSAT、EQU或没找到反例都不推出完整SQLite等价。

预算预案公开了worker墙钟10秒、CPU自身10秒、单次solver不超过3秒、4worker共40秒、独立复核20秒、父进程60秒、无重试及1GiB/50ms采样RSS；RSS是采样停止阈值且可能超冲，不是硬内存保证。CPU自身限制不能写成全进程树CPU上限。启动前必须证明进程组回收和进程树RSS可用并重新检查Mac/unrelated_project及独占锁；做不到即停止。本审查不批准启动实验，也不把文档预案当成已实施资源控制。

以上通过项不解除历史 BACKUP_BLOCKED、DATAHUB_REGISTRATION_BLOCKED，恢复/提交由根任务负责；本次未独立审查恢复完整性。
