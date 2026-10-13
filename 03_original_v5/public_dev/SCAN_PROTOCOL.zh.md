# 全量公共 DEV 适用性扫描（尚未执行）

固定来源是已暴露的 VeriEQL v1.0 Calcite 397 行与 literature-rewrite 64 行，共 461 对、922 查询槽。两个输入 SHA 固定在脚本 INPUTS 中；不得抽样、去重、筛成功行或把它们改称独立 test。原始行文本、完整 schema/constraint/pair 及行哈希一并保留。

运行前须由父确认 runtime_v2/runtime_paths.json 为 READY 并提供准确 SHA。脚本再次逐项核对整个 runtime 文件清单、导入根集合及 kernel SHA（c5ef813532ad190c5af82e2255da973fe8bc469ab24aed7da304678edcd46c35），不接受 pending，也不自行更新清单。使用已验证 Z3 4.12.0.0 与支持依赖，初始化原始 Environment（MYSQL，正常 __init__，因此会创建 Solver 对象），直接调用其 parse_sql_query，再把未经替换的真实 AST 与原始 schema 传给 recognize(..., identifier_encoding='verieql_double_underscore')。

不创建数据库、不断言 IC、不调用 analyze/is_parsable/encode/check/solve，不执行 SQL。这里只判断解析和当前窄片段适用性；保存 IC 不代表验证 IC，可识别也不代表等价性、加速、独立适配、泛化或竞争力成立。

运行由父唯一控制；示例参数（`READY_SHA` 须替换为父最终值）：

```text
<existing-python> -B -I -S <today>/public_dev/scan_eligibility.py \
  --runtime-lock <today>/runtime_v2/runtime_paths.json \
  --expected-lock-sha256 READY_SHA \
  --out-dir <today>/public_dev/runs/full_scan_01
```

输出目录须新建且位于 public_dev 下，不可覆盖。必须以干净允许环境和唯一计算子进程运行，并由父复用独立 RSS/墙钟监督；旧 case supervisor 的命令行参数不同，不能原样套入。脚本自身从入口开始设置 CPU 44 秒软/45 秒硬限制、墙钟 60 秒定时终止；57 秒软停给最终报告留 3 秒，采样 RSS 1 GiB 达限即停。RSS 自监测有采样间隔，原生调用期间仍需要父监督，不能宣称连续硬 RSS 上限。

输出保留：

- initial_not_run.json：在任何目标/native 导入前保存完整输入及所有未运行槽。
- query_events.jsonl：每个查询先写 QUERY_ATTEMPT，再写真实 AST、eligible、reason、必要时完整 traceback 的 QUERY_RESULT，并 fsync。ValuesTable 使用带类型字段的记录表示，识别器实际收到的仍是原对象。
- progress.json：最后完成行、累计原因分母及资源采样。
- scan_report.json：成功或可捕获失败后的完整状态；若进程被强制停止，该文件可能停在较旧阶段，应以 initial_not_run 加 query_events 的最后事件恢复。已有 ATTEMPT 无 RESULT 的槽是效果未知，其余未尝试槽仍为 NOT_RUN，不能误报扫描全完成。
- emergency.jsonl：墙钟/CPU 信号停止的最小记录；SIGKILL 无法保证新增记录，父进程 exit status 是必需的补充证据。

每查询区分 ELIGIBLE、INELIGIBLE、解析/AST 记录失败、识别器失败、未运行及进行中效果未知。pair_both_eligible 采用三值逻辑：任意一个明确 false 则 false，两个 true 才 true，其余 null；行内错误状态另行保留，不因 pair=false 隐去错误。

线程照实记录，mo_imports 的临时 monitor 不被隐藏或伪称单线程。父需等待并记录实际进程退出；报告资源时间均明确是最终写入前采样，不冒充包含整个解释器退出的精确墙钟。

本轮只编写并以标准库 AST 静态核查。没有实际扫描结果，也没有新增实验主张。禁止上传/push 的用户指令继续有效。
