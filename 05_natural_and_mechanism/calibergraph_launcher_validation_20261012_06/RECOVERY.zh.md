# 恢复说明

本包仅含自写工程验证启动器、两个轻量 fixture 的真实日志、结论、哈希及独立工程验收。私有备份目录为 `launcher_validation_20261012_06/`，仓库为既有 `wanghongsheng01/calibergraph-method-research-20261011`。依据 MANIFEST.json 验证内容；先读 RESULT.zh.md、VALIDATION.json 和独审。

不要重新运行 validate_launcher.py：ENGINEERING_ONCE.json 是永久一次性标记，保留原始结果，不为补日志重跑。恢复目录改名不授权绕过标记。canonical runtime 是旧 v2 目录中新建的 `runtime/owned.lock`，没有科学启动记录；它是活锁设施，不应作为“已备份即可使用的活动锁”复制到另一环境。两名 fixture 均已回收。无需读取系统进程验证本包结论。

旧冻结文件不修改。新包保存原 manifest 校验结果和所引用文件哈希；第三方输入、源码和依赖沿用旧来源，不再分发。包的恢复不解决此前历史 raw/native 的 BACKUP_BLOCKED 或 DataHub 源注册阻塞。
