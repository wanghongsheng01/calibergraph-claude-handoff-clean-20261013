# Polygon / FewRows 一手范围核验（阶段15，2026-10-11）
状态：**PAPER_CLAIM / NOT_REPRODUCED / CHECKED_PROOF=false**。未运行SQL、SMT、枚举、基准或artifact；只创建本阶段新报告。JSON是结构化证据账本，原文不随交付再分发。

## Polygon
[作者全文](https://arxiv.org/html/2504.06542v1)，PACMPL9(PLDI),2025，DOI10.1145/3729303；[ACM出版社](https://dl.acm.org/doi/10.1145/3729303)本次403。
任务是生成满足输出性质的数据库（反驳/多查询消歧）；创新是AST组合UA、lattice和conflict-driven search。§3.3的full semantics仍为**每表至多n行**；§3.8 Thm3.12仅在该界内complete。Fig7含NULL、外连接、GROUP BY及COUNT/MIN/MAX/SUM/AVG；[官方example](https://raw.githubusercontent.com/polygon-sql/polygon/main/example.py)有PK/FK/operational constraints，但本次没有审计其完整实现。

| §4 Table1任务 | solved/total | 平均/中位秒（仅solved） |
|---|---:|---:|
| ER | 5497/24455 | 0.6/0.1 |
| D-50 | 4004/4245 | 6.4/3.7 |
| D-100 | 2392/2475 | 21.7/18 |

60秒预算；ER分母不是全体已知可反驳实例。消歧集经bounded VeriEQL分组及timeout剔除。§4.2各工具时间是各自成功子集。具体全实验n和机器配置尚未核清；example的bound=2不能代替全实验设置。§4中2861/2816上游任务数不一致，保留疑点。
[版本化artifact](https://zenodo.org/records/15059866) v2标示21.4MB zip；[README](https://zenodo.org/records/15059866/files/README.md?download=1)估计RQ1全量30小时、RQ3全量500小时，均非本次实测。无下载或安装。

## FewRows
[Sara Cohen作者全文](https://arxiv.org/html/2609.09978v1)，[2026-09-09 arXiv v1元数据](https://arxiv.org/abs/2609.09978)；本次证据是预印本，**不是DKE已发表论文**。
§2为set-valued存储关系上的combined semantics。Thm7：总原子界 `2^w max(|Q|,|Q'|)`；每关系界 `2^w_p max(sj(Q,p),sj(Q',p))`。Thms13/15需key-anchorability及acyclic FK/chase；§5只覆盖指定comparison classes。
`{1,2}^m`是每个multiset变量的值块大小，不是每表两行。Example8分别出现16的上界、9的corner及3的较小witness，不能混为紧界。§2联系COUNT multiplicity；§7把更一般aggregation列为后续方向。没有建立SQL NULL/3VL或任意SQL的转译覆盖。
“Use of AI Tools”明确不报告实验；没有可引用的实测分母或运行成本。定位定理不等于独立验完证明。

## 对本阶段开发诊断的约束（本次判断）
H15仅拟在固定四来源dev03_07/10/15/04、原SQL/schema、完整operational C和exact-N不变条件下，重复比较N2/3/4冷启动成本；具体预算由root协议负责，本报告未冻结或执行。
- 可以借文献约束界语义、失败状态和成本分母，并检查import/encode/solver三段。
- 不能把exact-N直接等同至多n；不能将700ms查询预算与Polygon60s结果直接排名。
- 不能以Boolean corner为N2完备性证明；不能把无witness、timeout或OOM写成全局正确性/科学hardness。
- 四个开发来源不支持方法创新、真实业务缺陷发现或优于既有系统的主张。此前06已做2/4/8诊断且有解析恒等式解释，H15只补开发成本归因。

DKE目标已由root旧稿明确为Thanisch等2019年measurement论文；详见同目录 `dke_candidates.md/json`。作者机构元数据/摘要不能替代原文实验和语义范围。DataHub注册为root已知阻塞，backup由root统一；原文byte hash不可得，清单仅核本次作者产物。

