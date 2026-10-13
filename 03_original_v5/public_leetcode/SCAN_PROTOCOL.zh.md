# LeetCode 完整来源分块适用范围扫描

官方固定 commit 文件已按父任务实际 HTTP 200 / exit 0 下载证据核验、计行并从 `.part` 改名。文件大小 22,995,478 字节，SHA256 为 `b97fc1293701682a25a2f6345f3630b3482ce49912463a7f4b76ab52665a13c9`。实际是 **23,994 对 / 47,988 查询槽**，比 README 的 23,224 对多 770 对；不截断、不去重、不按成功筛选。结构检查所有行均为含两条字符串查询和 schema 对象的记录，constraint 为 list 或 null；没有调用 SQL 解析器或向模型展示查询内容。

全局初始 `GLOBAL_MANIFEST.json` 保持所有行/查询为 NOT_RUN。其 SHA256 固定为 `041d6c0bf43dad8270c099f10bcbcf61cfc4ee5a96f13170ff141e35c5ce45a0`，含逐行字节偏移、长度和哈希。24 块顺序覆盖：前 23 块各 1,000 对，最后 994 对。父此前读过 VeriEQL 论文 §2 的简化 LeetCode 示例；不能把整个来源无条件标为从未暴露的独立 heldout。本工作只记录外部适用范围，不提供人类金标、等价准确率或性能证据。

`scan_chunk.py` 沿用已审的真实 Environment 扫描路径。父唯一执行器需要使用现有 Python 的 `-B -I -S` 和干净允许环境，以独立进程监督 RSS 与墙钟，不得与其他目标运行重叠。首块命令参数：

```text
<python> -B -I -S <today>/public_leetcode/scan_chunk.py
  --runtime-lock <today>/runtime_v3/runtime_paths.json
  --expected-lock-sha256 505e59253be72e73edf236efe647d84cfcebffe15980517072ae20230bdc38d7
  --chunk-index 0
  --out-dir <today>/public_leetcode/runs/chunk_000/attempt_001
```

必须使用新的 `chunk_NNN/attempt_NAME` 输出目录。下一块是 `--chunk-index 1` 和 `chunk_001/attempt_001`，依次至 23。脚本拒绝跳过前面未完成的块；失败、解析错误和 FRONTEND_UNSUPPORTED 都是已记录终态，保留在完整分母中。

CPU 软/硬限制 44/45 秒，墙钟软/硬限制 57/60 秒，RSS 1 GiB 自身采样软限；原生调用期间仍依赖父的整进程监督。正常初始化官方 Environment（DIALECT.ALL，与官方 parallel 默认一致），会创建 Solver 对象，但不创建数据库、不断言 IC、不执行 SQL、不调用 analyze/encode/check/solve。

每个原始查询先调用 v3 `ensure_raw_identifiers(original_schema, original_sql)`，通过后才解析，随后用真实 AST 调用 `recognize(..., identifier_encoding='verieql_double_underscore', original_sql=original_sql)`。`FrontendUnsupported` 必须在其父类 `Ineligible` 前捕获，单列状态，不允许 fallback；不预清洗 schema 或 SQL。kernel SHA 固定为 `defa1812ec36c91a23d428f8d71d2070f808eddeb5f473748d3e7ac09fdfe5f3`。

每块报告仅存该块完整原行/schema/IC/query 与 AST、原因。每次查询先 fsync ATTEMPT 事件，再 fsync RESULT 事件。停止后在同块的新 attempt 目录续跑：脚本检查前次 source、manifest、runtime lock、kernel 和自身版本一致，从原有事件恢复所有完整 RESULT，**不重跑任何已完成查询，包括失败结果**；只有没有完整 RESULT 的中断查询可再次尝试。仅最后一条未写完的事件行可以忽略并明确记录；其他损坏或结果冲突会停止。

`GLOBAL_PROGRESS.json` 保存最后完成检查点时的全局 47,988 槽状态及块索引；未扫描块仍为 NOT_RUN。它不是持续同步的真值：若 SIGKILL/限时发生在最终写入前，需结合该块 initial_not_run 和 query_events 恢复；不可把旧 progress 当作刚完成的全量结果。父必须保留真实 exit status、监督资源及 stdout/stderr。原始 GLOBAL_MANIFEST、所有 earlier attempt 和失败均保留。

既有 461 对的历史 v2 方言对照另存 `../public_dev/DIALECT_SENSITIVITY_SUMMARY.json`：MYSQL 的 108 项解析/AST 错误在 ALL 下为 32 项，eligible 查询仍为 7 条且全为单表。该结果不能升级为 v3 安全前端下的覆盖率，原件不重写。

截至交付，来源校验和静态代码检查完成；真实 LeetCode parser/recognizer 扫描仍由父启动。本子任务未执行目标、原生库或求解。禁止上传/push 的用户指令继续有效。
