# SpotIt direct-engine 语义勘误（仅静态审计）

结论：固定提交 `fb1bdaae8f3e4a544d08feffa44bc14270d99329` 的历史 direct-engine 运行使用 **default auto → SetSemanticsVerifier**，不能标作一般 bag-semantics 基线。此次只新增本勘误和 `SEMANTICS_TEXT_LOCATIONS.json`，未改 source、runner、运行锁、原始 report 或 records；未联网、未导入目标、未执行 native/solver。

## 已确认的误标

| 文件与行 | 原文问题 | 正确解释 |
|---|---|---|
| `runtime_v2/spotit_paths.json:884` | `Engine default strict bag semantic setting` | 默认 auto 选择 set；`all_null_is_deleted=false` 是 NULL 行处理设置，不是 bag 开关。 |
| `runtime_v2/spotit_paths_02.json:895` | 同一旧 note | 同上；该文件 :898 的 `default auto set semantics retained; scalar one-row scope only` 已正确，但与旧 note 矛盾。 |

应以本勘误覆盖旧 note 的解释，不改写历史锁，否则会破坏记录中的 SHA 对应关系。全部证据文件 SHA、行号和原文片段见 JSON。

## 调用链与实际比较

`runtime_v2/case_worker.py:192` 构造 Environment 时未传 `semantics` 或 `all_null_is_deleted`，并设置 `generate_code=False`。固定 source 的 `environment.py:94–114` 使默认 `semantics=None` 进入 Verifier；`:1164` 调用 `self.verifier.run`。`verifiers/verifier.py:92–109` 在有、无双侧 ORDER BY 时都实例化 SetSemanticsVerifier，并调用 `table_equivalence`，原 list/bag 选择已注释。`set_semantics_verifier.py:153–172` 对两侧结果检查双向成员存在性，没有要求重复次数相等。source 的三个关键文件与已闭合 `spotit_paths_02.json` 中记录的 SHA 全部一致。

注意同一 SetSemanticsVerifier 中 `z3()` 的代码生成字符串仍含计数相等逻辑。历史 direct worker 使用 `generate_code=False`，实际结论取自 `table_equivalence`；不能拿该字符串或类的 import 清单证明实际 bag 语义。本审计不据此承诺显式传 `semantics='bag'` 能修复调用链，任何后续更改须独立检查并重跑。

## 历史运行应如何解释

- `runs/spotit_engine_first2_01` 使用旧锁 SHA `b7f2630a72cb1018165623f693ecc0cb5020a85d19c614d43df6e2e7113cc7d2`，两个尝试在导入时失败，official verdict 都是 NOT_RUN；不能把它记成 set 或 bag 运行成功。`frozen_checkpoint_01` 副本同样保留。
- `runs/spotit_engine_first2_02` 和 `runs/spotit_engine_remaining4_02` 使用锁 SHA `6f701d9dd26c83866ed85448652ff34a2f1404392b6130d512575a045994de86`，合计六个 exposed scalar DEV 案例。`official` 是该固定 fork 的 auto/set 路径；flat、product、selector 是另三个候选 arm。`24` 个 verdict slot 是六例 × 四 arm，不能说是 24 个独立 SpotIt 实验。
- 原始 reports 中的 `unequal_as_bags` 是 SQLite 结果经过 Python `Counter` 的回放比较；它是有效的 bag 回放字段，**不是** engine 语义声明。JSON 逐处记录这些位置，无须全局替换。
- `manuscript_v1/main.tex:54` 与 `stage1_frozen/main.tex:54` 已正确限定为 set engine、标量单行条件下的比较，并否定完整 SpotIt+ 复现；无需将这些正确边界改成新结果。

## 不受此勘误影响的 bag 文字

`runtime_v3/runtime_paths.json` 指向另一固定源 `sources/verieql_v1`（提交 `3b99928bf976c11cb59c9db6a177adba21f75798`）。其 `verifiers/verifier.py:92–105` 无双侧 ORDER BY 时选择 BagSemanticsVerifier；不能因 SpotIt fork 的误标把该源或所有其他 arm 改称 set。`runtime_fair/common.py:175` 的 Counter 也是有效回放检查。论文中受限标量聚合的输入 bag multiplicity 主张是否成立是单独证明义务，本勘误不否定或认证该主张。

## 科学边界与后续引用

只有在两侧确实各产生 1 行，且行值与 NULL 比较规则一致时，set 与 bag 的重复次数差异才不出现。这个条件不证明 parser、聚合、NULL 或行保留实现的整体正确性；更不能外推到多行、重复敏感结果或有序列表。六例 DEV 一致仍只是受限已暴露诊断，不能升级成泛化、性能优势、真人金标或独立 held-out 结果。

建议后续表格标签使用：**SpotIt+ pinned VeriEQL submodule, direct SQL, default auto/set, all_null_is_deleted=False, scalar DEV only**。完整 SpotIt+ 的 LLM、约束挖掘和外层流程未复现；直接导入其 submodule 不等同于完整 SpotIt+。此勘误不改变任何原 verdict，也不以文字修订代替需要的新实验。

备份状态：`BACKUP_BLOCKED_BY_USER_NO_UPLOAD_NO_PUSH`。本次遵守用户明确禁止上传/push 的范围。
