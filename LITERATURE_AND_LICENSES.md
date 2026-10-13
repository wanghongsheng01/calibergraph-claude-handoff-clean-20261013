# 一手文献、许可与恢复边界

以下为此前核验记录的恢复入口，不宣称本次重新复现论文结果。作者文献笔记在 `08_literature_notes/`，候选稿参考文献在 `01_manuscript/candidate24/latex/references.bib`。

|对象|一手入口|证据边界|
|---|---|---|
|VeriEQL|https://arxiv.org/html/2403.03193v2|有界复杂SQL/IC；本地原baseline v1.0 commit3b99928b；不得声称一般不支持JOIN|
|SpotIt+|https://arxiv.org/html/2603.04334v3|旧实验只调用引擎，不复现完整约束挖掘/模型流程|
|Polygon|https://arxiv.org/abs/2504.06542 ; https://doi.org/10.1145/3729303 ; https://github.com/polygon-sql/polygon|UA/precise，at-most与原exact-live不同；代码5e18237394d025dbb805cf833b4f54c321470774|
|FewRowsTellThemApart|https://arxiv.org/html/2609.09978|完整性阈值只对文中指定片段成立，不提升任意SQLite一行界限|
|ParSEval|https://github.com/sfu-db/ParSEval/tree/88cfe245bcf249a5b0df561a6b09c116ff2a2896|生成测试数据库；EQ在本记录是采样一致；完整论文元数据见引用文件|
|冻结官方运行|https://github.com/sfu-db/ParSEval/actions/runs/37547685455 ; https://api.github.com/repos/sfu-db/ParSEval/actions/artifacts/11452059162|BIRD1534条输出；归档可能过期/要求登录，优先核包内固定字节，不用新运行替换|
|BIRD|https://bird-bench.github.io/|官方2024-04-27公告将数据许可改为CC BY-SA4.0；本次2026-10-13只读核验|
|DKE相邻实证尺度|https://doi.org/10.1016/j.datak.2024.102309 ; https://doi.org/10.1016/j.datak.2023.102154|此前仅出版社可读摘要/节摘要，未获得完整结果表；不能推出固定录用门槛|

## 随包材料的处理

- BIRD派生原SQL/DDL、选中案例、固定语料保持来源标识；归属于BIRD作者（Jinyang Li等，论文及官方页所列团队），数据受 https://creativecommons.org/licenses/by-sa/4.0/ 约束。选取/格式化是本研究的派生处理，未修改所选SQL/DDL语义；派生数据继续保留相应归属和同许可。作者代码/报告并不自动整体改许可。
- ParSEval代码为Apache2.0，已核固定commit的LICENSE与pyproject；`06_public_sources/parseval_code/LICENSE`原样随包，源码未改。BIRD原数据权利与ParSEval源码许可分别记录，不能用代码许可抹去数据许可。
- Polygon固定快照及官方仓库未见明确LICENSE；完整原树、派生完整runtime和第三方二进制不随包，保留作者最小补丁、运行器、来源commit和逐文件SHA256恢复清单。公开可读不等于已取得任意再分发许可。
- VeriEQL/SpotIt完整上游树、LeetCode大语料及第三方论文全文不随包；许可未统一核定，提供本地身份与一手恢复方式。官方SQL案例覆盖已实际用到的BIRD十对及新33对；不是声称附入全部48,910查询槽的原SQL。
- 作者原稿、候选稿、适配/补丁、实验记录和独审材料仅按用户授权交接。没有公司生产数据库、凭据、账号会话、大模型权重或P19全文。涉及P19只保留本论文的重叠风险说明。

## 精确缺失清单

`EXTERNAL_MISSING_FILES.csv`逐文件列原位置、字节数、SHA256、未打包原因与恢复方式，包括Z3平台二进制、Python依赖、固定上游树、大型cached AST/公开语料。不能在Claude端把原macOS路径当作可访问网址；需要用户复制本地字节或依法从一手来源恢复并核hash。没有本地实际持有的BIRD完整SQLite数据库/大模型权重可提供精确hash，故不宣称已附入，也不伪造hash。重放本轮合成候选所需的完整DDL和候选值已在矩阵ZIP中。
