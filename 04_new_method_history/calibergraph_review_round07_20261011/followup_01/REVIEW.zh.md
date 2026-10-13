# Round 07 revision_02 独立修复复审

**五项原发现均 resolved；保留 NULL/HOLD。** `new_validated_mechanism = null`，没有保留新的候选问题，没有新科学证据支持方法晋升或随机实验。这里的“通过”仅指修复准确、边界表达合格，不代表 H1/H2 已获证明。

本轮只读 revision_02 的五个指定文件，随后经父任务扩展范围，只读新增 `provenance_correction.json`，并对原审核五个交付文件仅做字节哈希检查。未修改作者文件或原审核。没有执行 SQL、solver、benchmark 或其他科学实验；只有文件读取、写报告、JSON 检查及 SHA256 操作。未重新检索文献，文献条件沿用已完成的独立一手核验。

| 原发现 | 状态 | revision_02 锚点与判定 |
|---|---|---|
| P1-01：minmax 量词过强 | **resolved** | 主文件第 63 行明确限定 query-independent、每表一行及含 disequality/IS NULL 的类型空间；区分类型数 T 与值域大小 q；承认均匀类型抽样的 1/T 独立于 q，且不反对 pair-driven，也不是 equality-only C 的下界。 |
| P1-02：H1 可退化为常量模板枚举 | **resolved** | 主文件第 49、53 行明确承认 degree-zero 常量模板满足原条件；重开须给出严格非可锚定片段的新 small-model 结果，或计入构造/重建代价后优于有界枚举的复杂度界。二者都是未来证明义务，文中没有声称已完成。新 small-model 定理本身可以有价值；不能再把随后的枚举包装成另一个新多项式机制。 |
| P2-01：F_q 弱界误称 vacuous | **resolved** | 主文件第 31 行增加 q 为素数幂、取值在 F_q 的前提；degree=q−1 对应弱成功界 1/q，不再写成近 1 保证或完全无信息。 |
| P2-02：COUNT 与 C 的语法层次 | **resolved** | 主文件第 41 行及 SQL 第 25–29 行明确常量头 bag-query cores；JSON 第 143 行将 COUNT 标为 observer。2 与 4 仍为手推多重度，没有将 C 扩为任意聚合语言。 |
| P2-03：DeHaan PDF 页码基准 | **resolved** | `neighbor_audit.md` 第 75 行区分印刷 170–171 页、PDF 一起计 190–191 页、零起索引 189–190。 |

附加先例表述也已闭合：主文件第 37 行明确承认 Few Rows §4 已公开 Customer/Orders residual 及 existential 值依赖 counted 值的修复方向；本轮不把实例形态或缺口重新作为原创发现。

复审额外发现的谱系问题已 **resolved**：原 `REVISION_MANIFEST.json` 记录的是审核结束前的中间 manifest 哈希。作者未覆盖历史，而用 `provenance_correction.json` 指明唯一被替代字段。该修正文件 SHA256 与父任务给定值相符；正确最终审核 manifest 的 `c17a0358…d219ef97` 及其余四个原审核交付哈希均经本轮只做哈希的检查相符。原 revision manifest 本身仍匹配给定的 `b9387d11…9406d`，四个 revision 内容文件也匹配其中记录。

**remaining：无未闭合的本轮修复项。** 理论门仍未通过：合法性、完整分离性、非平凡代价界及新颖性尚未形成一条已证明的新机制；这些保留义务不会因文字修复而消失。主文件第 3、5、53、65、85、90 行与 revision manifest 的 NULL/HOLD 和零实验记录一致。下一步仍无可获准的实验；若重开，应先交付具体科学命题及证明或反例。

本报告与结果 JSON 已冻结；所有输入、原审核仅哈希对象及本轮交付校验值见 `FOLLOWUP_MANIFEST.json`、`SHA256SUMS`。私有备份留给父任务在本轮最终回传后统一完成。
