# 恢复与低负担验证

作者代码、所有作者/独审夹具及结果、原生输出摘要、来源与哈希备份至既有私有 `wanghongsheng01/calibergraph-method-research-20261011` 的 `z3_lifecycle_20261012_12/`。不提交 `native_local/z3` 或第三方源码；原二进制恢复路径及哈希在 BINARY_COPY.json / probe 脚本，原 SQL/fullC 不重新分发。先核验 DELIVERY_MANIFEST.json。

本机采用已有 `/opt/homebrew/bin/python3.12` 3.12.13，macOS 下仅标准库。换路径需显式记录解释器路径修改，不能冒充同一哈希运行。无需安装大依赖。恢复后验证仅经授权运行；本包不授权自动重试科学槽。

普通夹具命令 `python3.12 -B validate.py validation_recovery_01` 在本目录创建新的不可覆盖结果目录，实际创建 7 个轻量自有子进程；一次最多两子进程，本 Python 一次固定分配 40 MiB，测试阈值 48 MiB。既有 validation_run_01/02/03 是历史证据，不覆盖。测试主体结束后所有已登记子进程必须 returncode 非空；cleanup unconfirmed 不能当成功。

如重建原生探测，先从原冻结来源恢复同 SHA-256 的二进制，复制到新隔离 native_local/z3 并只给副本可执行位，禁止改旧来源。probe_z3_metadata.py 和 probe_z3_idle.py 会创建固定不可覆盖目录；恢复重跑应在另一个完整恢复目录进行。它们仅帮助/启动退出/空闲输入，不发送 check-sat。它们不测量外部 RSS，也不能授权科学求解。不要把探测专用内存参数作为科学预算。

OwnedCase 仅适用于独占单线程宿主，不允许生命周期额外线程或未登记后代；整例截止不是含清理在内的严格硬实时保证；突然父进程被 SIGKILL 等未覆盖。science_admission 固定拒绝外部 Z3 RSS 缺口，改变它不能仅改布尔值或用内部计数冒充 RSS。未来若运行必须另行补足经过允许和验证的保护、完整 Polygon 集成与语义准入。

本轮 datahub list 已复核，公共源码研究源缺少匹配模块，继承 DATAHUB_REGISTRATION_BLOCKED：受限工作区无 canonical registry 写权限，且当前授权要求不改变外部系统，未扩展注册表。历史第三方 raw/native BACKUP_BLOCKED 与本轮可恢复作者包状态分开报告；本包用来源/哈希恢复第三方文件，不声称将二进制备份到 Git。
