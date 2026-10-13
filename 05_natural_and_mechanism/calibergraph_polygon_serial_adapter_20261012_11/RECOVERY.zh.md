# 离线恢复与验证

作者代码、测试、报告、哈希与独审保存在既有私有仓库 `wanghongsheng01/calibergraph-method-research-20261011` 的 `polygon_serial_adapter_20261012_11/`。上游源码与两份本地隔离副本、生成的含上游删除行的 diff 不重新分发；使用已冻结来源重建。历史第三方 raw/native `BACKUP_BLOCKED` 与公共研究源 `DATAHUB_REGISTRATION_BLOCKED` 并未由本作者包消除。

恢复 Polygon `5e18237394d025dbb805cf833b4f54c321470774` 中 build_adapter.PINS 指定的三份文件，保留相对路径，或使用之前备份包来源说明恢复 `.txt` 快照。工具传输/换行差异若导致哈希不一致，停止而不修改验哈希门槛。源 SHA-256 是本次已核查 UTF-8 文本的身份，不虚称 Git blob 哈希。

使用已有 Python 3.10 以上解释器（本机验证为 Python 3.12），在新的目的目录运行：

```
python3.12 build_adapter.py /path/to/frozen/polygon /path/to/new/isolated_local
python3.12 test_adapter.py /path/to/frozen/polygon
```

测试文件应位于可写的恢复副本，因为它将生成 TEST_RESULTS.json 与 TEST_OUTPUT.txt。测试不需要第三方依赖，不导入 Polygon、不执行 SQL、不启动求解器、不创建子进程。编译提取方法的输入也必须先通过冻结哈希检查。预期 8 项通过，forbidden_audit_events 为空。测试秒数可能不同，不要求计时日志字节相同。

生成的 isolated_local/serial.patch 即本轮小 diff，BUILD.json 绑定前后哈希；备份中的 BUILD.json 和 PATCH_SHA256.txt 可用于核对。完整运行环境不在本包。不要把三个文件覆盖层误当可启动安装；不要调用 disambiguate。任何未来实际运行须先补足 RESULT 中的自有 Z3 生命周期、总截止与覆盖全进程内存的保护，并独立解决 SQL/fullC 类型边界。本轮不授权恢复后自动实验或重试旧批次。
