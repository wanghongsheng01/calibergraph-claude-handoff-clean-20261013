# 第 13 轮 SQLite 极小复放：运行前独立静态审查

日期：2026-10-11。审查者：`/root/round13_independent_preexec`；作者：`/root/round13_sqlite_counterexample_replay`。

**结论：PASS，未发现需修改作者代码的阻断。** 仅认可冻结构造、受限启用变更及下述单次执行合同；不是实际 SQL 验证通过，不是实验完成，也不授权新增构造或重试。第 12 轮结论仍为 REJECT H12、无新可晋升机会。

## 冻结及独立性

先只读第 12 轮 `REVIEW.md`、`REVIEW_DECISION.json` 和 `theory/`；收到 root 的第 13 轮最终 SHA 后才读取完整 400 行源代码及全部协议。未读取第 14 轮，未接触外部来源或凭据。没有修改作者源、旧冻结或执行开关。

- 已核对第 13 轮 `protocols/SHA256SUMS.outputs` 的全部 9 项。
- 禁用源和快照 SHA：`467f8df522a9dbb845ec35542f9dd412452ede05debffb9d9056b144c30a5004`。
- 第 12 轮作者 manifest SHA：`dfa81be07edf21839bf83bdaeb9cb1ac065d03d909fc086fbbbaa890155aa33e`；第 12 轮独审三项 SHA 与第 13 轮 freeze 一致。
- 第 13 轮作者 manifest SHA：`210617262055167faad394aad8cc7aa1169ac7ce7d529c86f91d50ce154528e3`。
- 独立 AST 检查确认唯一开关赋值为字面 `False`。仅替换 `EXECUTION_ENABLED = False\n` 为 `EXECUTION_ENABLED = True\n` 后的预期 SHA 为 `50e6d27ad3ebaa9227e274f4247f97d91a2641bfb79ee8b6cf6d2d47df72d755`。这只是对变更字节做 hash，没有保存或执行启用代码。

审查实际操作限于读取、AST/JSON 解析、哈希、写审查报告。未 import runner，未 compile/py_compile，未执行 SQL、数据库/赋值/家族枚举、科学程序、模型、GPU 或 SMT。静态 AST 遍历不生成科学输入。

## 构造、约束及语义

`replay.py:222–279` 以全部 64 个 mask 枚举 C，在六环去掉 C 的无向诱导图中取连通分量。固定二元关系下，这与去除 C 变量节点后的 incidence component 一致。全部 FD 为平凡 FD，故 64 个 C 都闭合；C=V 无 entry，C=∅ 生成全环一个 entry。

每个分量只用两个完整 body assignment，整个 S 共用同一个 tag；S 外固定 tag 0。虽然固定值用 `vi#0` 而非数学记号 `vi#*`，每个变量层互不相交且每个 DB 独立，因此没有引入额外相等关系。tuple set 去重只作用于同一关系内部，不会丢掉重复 C,S 条目。按第 12 轮已证明的边界分类，原始分母为 97，长度分母为 48/24/12/6/6/1；31 只作带标签 S 的成本注解。

独立 Cartesian 控制使用 n=(2,2,1,2,1,1)，相邻层全乘积。13 个 literal rows 与第 12 轮行表在变量值重命名后逐项对应；程序另核对集合一致性。这是构造/合法性校验，不是第二个计数 evaluator。cheap 4 项仅作已有 97 项上的标记。

`replay.py:63–84` 的 schema 为 `TEXT COLLATE BINARY NOT NULL` 两列及完整二元 PK，没有 FK 或单列 key。六个 alias 依次连接并闭合末边，内层 DISTINCT 分别投影 v0,v1,v3 和 v0,v1,v4，外层 COUNT(*) 计不同投影；没有以完整赋值数替代计数语义。固定参数 INSERT 不接收任意 SQL。预期仅继承既有手证：|S|=1 为 9/9、|S|=2 为 11/11、其余为 12/12，Cartesian 为 20/19。

这些预期和约束匹配是静态判断；SQLite 的实际约束执行、PRAGMA/limit 能力、98 个具体 rowsets/hashes、196 个返回值仍未验证。

## SQL 与分母账本

成功运行的静态预算如下，均不是测量值：

| 项目 | 每 DB / 分母 | 成功时总数 |
|---|---:|---:|
| 内存 DB | 97 family + 1 control | 98 |
| 固定计数 SELECT | 2 | 196 |
| CREATE TABLE | 1 | 98 |
| PRAGMA setter | 6 | 588 |
| PRAGMA readback | 6 | 588 |
| 参数 INSERT | 实际行数 | 883 |
| 显式 SQL 总数 | 上述全部 | 2353 |

INSERT 的静态总数是 `48×8 + 24×9 + 12×10 + 6×11 + 6×12 + 1×12 + 13 = 883`：真区间长度 l 的行数为 7+l，全环为 12。这个算式没有程序生成或枚举输入。代码的 setup counter 合并 6 个 PRAGMA setter 与 1 个 DDL，完整成功时为 686；budget verification counter 为 588。最终报告应按该已知分解分开说明 DDL 与 PRAGMA，不把 setup 省略或混入 196。没有显式 BEGIN/COMMIT/ROLLBACK/其他 SELECT；`isolation_level=None` 避免 Python 隐式 BEGIN。此表计 Python 显式提交的 SQL，不将 SQLite 内部操作伪报为零成本。

`replay.py:274–279` 成功写出全 98 项初始 NOTRUN 快照后才建任何数据库；构造或该写出失败时不能宣称已冻结全部具体输入。每条计数分别递增 attempted/completed，M mismatch 不继续 N，不重试。普通可捕获错误且仍有资源写出收据时保留 COMPLETED/FAILED/NOTRUN 全账本，整体 NOTCOMPLETED。成功要求全部循环结束且 completed count SELECT=196，随后必须有有效的 result/completion 和外层退出证据。

## 资源、依赖及单次执行

代码只导入 time/os/signal/resource/sys/hashlib/json/sqlite3；无线程、fork、子进程、网络、ctypes 或用户可扩展输入。SQLite worker threads=0；结构为固定六变量、最多 13 行/DB，候选完整赋值上界为 6×2^6=384。输入、源、预检、输出的字节界在读取/写出时检查。

CPU 为 RUSAGE_SELF 总值，RLIMIT_CPU hard=2 s，采样提前停止值=1.95 s。3 s wall timer 从首个 time 入口持续到退出，SIGALRM 调用 os._exit(124)，无额外清理宽限。固定 SQL 的 progress callback 每 1000 VM ops 再检查资源；Python 信号处理和 OS 调度不是实时系统，但本固定小工作量下限额路径有效。解释器最早启动段不在入口 wall 计时内，必须保留 root `/usr/bin/time -l` 的整次启动耗时与退出码；总 SELF CPU 包括已消耗的启动 CPU。

仅 Darwin；nice 最低优先级数值为 15。RSS 是 Darwin ru_maxrss 的过程峰值采样，128 MiB 是采样拒绝门，不声称 kernel 瞬时硬 RSS cap。metadata、hash、输入准备、序列化及自然退出尾部都必须计成本；phase timing 之外的启动时间由累计值/外层收据覆盖。SQLite limit/PRAGMA 有 readback，不能建立则拒绝；不得为了通过而放宽预算。

`ROOT_RUNTIME_PROVENANCE.json` SHA 为 `503486b11348ba53613ff3e2ae2c9eefb9ac65cea550b93d71e9ec08d88c45dd`。我已独立哈希复核 Python 3.12 可执行文件、_sqlite3 扩展和真实 libsqlite3 dylib 三项字节；均与该 root 元数据文件相符。Python 3.12.13 / SQLite 3.53.3 的版本值属于 root 的 metadata-only 报告。root 必须在启动前再次 rehash 并用固定解释器，不需要给 runner 重复添加同一套校验。OS 原生依赖和冷机恢复尚非完全字节级复现。

exclusive-create 永久 lock 与 run_once 目录在授权验证前创建；进入 main 的启用尝试即消耗尝试，失败也不删锁或另换目录。独审 JSON、禁用源、执行源、前轮证据、fresh preflight 均有 hash 绑定。preflight 必须真实成功、0–60 s、Darwin、load≤4、memory_pressure -Q free≥25%；程序再检查实时 load。外层应先检查资源，不能先启动试跑来探门。缺失/失败的必要 telemetry 或能力必须拒绝，不能用默认值通过。

## 接受的失败边界及强制外层处置

发现一个非阻断边界：资源 guard 抛错后，`replay.py:352` 和 `:390` 再次 checkpoint 可能再次抛错，最终 result/completion 无法落盘；hard CPU/wall 中断也如此。初始文件只是执行前快照，不能据此声称实际 98 项均未运行、实际 SQL=0。root 已明确接受下列保守合同；本次微小复放不要求新增 journal 或放宽限额。

1. 若缺任一有效最终收据、哈希不符、退出非零、信号终止或外层不能确认完整退出，整体为 NOTCOMPLETED，禁止重试、成功率或已复现声称。
2. 如果最终收据不完整，固定计划分母仍完整披露为 98 DB / 196 count SELECT。98 个计划项的实际状态统一为 ACTUAL_STATUS_UNKNOWN；初始 NOTRUN 文件单独标 PRE_EXECUTION_SNAPSHOT。若连初始快照都不完整，denominator_constructed 只能记 false/unknown，不能声称真实输入都已生成。
3. attempted/completed count SELECT 均为 UNKNOWN，上界 196、下界 0，且 completed≤attempted；不是具体零。无有效 receipt 时 DDL 为 UNKNOWN [0,98]、PRAGMA setter/readback 各 UNKNOWN [0,588]、INSERT UNKNOWN [0,883]，显式 SQL 合计 UNKNOWN [0,2353]。实际部分值仅在可靠原始证据存在时才可另列，不能猜测中断点。
4. 有完整有效的失败 receipt 时可保留其确切进度；原始文件和外层 stderr/time/exit 均保留，不覆盖或修到通过。即使内部 receipt 写 COMPLETED，只要外层失败仍 NOTCOMPLETED；可记录其已观察值但不能宣称整次完成。

上述合同也由本目录 `independent_review.json` 机器可读规定。它解决的是失败分母公开及证据诚实性，不承诺恢复每一次中断前的实际状态。

已读 root 新增 `ROOT_EXECUTION_PROTOCOL.json`，SHA `f576f5b71713b8aa08bc15399a6eb170ccbef0968c102035b4e7c323ffd62fbb`。其中成功条件和缺收据的 98 项 UNKNOWN 处置与本审查一致；本审查额外将其他 SQL 类别的未知范围写清。其计划 venv 解释器路径已只读解析到上面 pin 的 Python 二进制，字节 SHA 相同；`-B -E -s -S` 不修改作者源，也不新增科学操作。

## 交接

`independent_review.json` 已由本人填写真实 PASS，可原字节复制到 `13/protocols/independent_review.json` 并由 root pin SHA。只允许源码第 5 行 False→True 的确切 diff；执行源 SHA 必须等于上列预期值。独审通过本身不替代 root fresh preflight、运行前依赖复核和 whole-launch 收据，也不说明限额已经实测或期望已命中。

科学定位保持一个已知合成负例的一次实现一致性核对，非 natural/test、新方法、效率实验或新颖性证据。备份与 DataHub 由 root 统一处理；本审查没有新的外部/企业数据访问，未独立声称私有备份完成。
