# 独立工程审核

**结论：受控生命周期工程条件通过；科学准入仍为 false。** 初审发现的四项必须修复问题均已由作者修复，并经非作者脚本独立复测通过。当前结论仅适用于下述运行契约；最终 RESULT/RECOVERY 文本已检查，工程声明与科学边界符合本次证据；已签署的文件 SHA-256 保存于 `INDEPENDENT_REVIEW.json`。

审核对象：`owned_processes.py`、`fixtures.py`、`validate.py`、作者 `validation_run_01/VALIDATION.json` 及修复后的 `validation_run_03/VALIDATION.json`。最终复测的 owned_processes.py SHA-256 为 `217bbbbac7e0ae39cd19ee905c2a0c13a247888463e3b42132f8a2b246dbcb8b`，其余文件哈希保存于复测 JSON。

审核者未修改作者代码，未运行 SQL、Polygon 或 Z3 科学求解，未启动四个科学槽。未枚举进程、读取外部进程 RSS、安装、修改可执行权限或规避权限限制。所有测试仅以保留的 Popen 句柄操作测试自有子进程。

## 初审发现与修复复测

原始失败证据保留在 `review_run_01/INDEPENDENT_CHECKS.json`；修复后的同类回归证据为 `review_run_01/INDEPENDENT_RECHECK.json`。脚本分别为同目录的 `independent_checks.py` 与 `independent_recheck.py`。

|问题|初审独立复现|修复后独立复测|
|---|---|---|
|SIGALRM 登记竞态|实际自有 Popen 后插入 0.12 秒延迟、截止 0.05 秒：created=1、registered=0、仍运行的未登记句柄=1|watchdog 继承阻塞 SIGALRM；created=1、registered=1、未登记句柄=0|
|清理嵌套异常|ignore_term 自有句柄的 kill 注入 OSError：wait_events=0、cleanup_errors=[]、原 handler 未恢复|两句柄均继续记录 wait；错误聚合，显式报 cleanup unconfirmed，原 handler 恢复|
|流关闭异常|已退出子进程的 stdin.close 注入 OSError：错误未聚合、原 handler 未恢复|错误聚合，显式报 cleanup unconfirmed，原 handler 恢复|
|进入阶段漏回滚|wall_seconds=0.000001：__enter__ 抛异常、closed=false、原 handler 未恢复|进入失败自行回滚，closed=true、原 handler 恢复|

初审未登记句柄，以及故意注入 kill 失败的句柄，均由审核脚本保留并执行恢复后的 kill/wait；没有把“已识别清理失败”冒充为该次原实现自行完成清理。故障注入后抛出 cleanup unconfirmed 是正确的失败关闭结果。

## 独立正向验证

`review_run_01/independent_lifecycle.py` 与 `INDEPENDENT_LIFECYCLE.json` 记录三项通过，合计约 0.600 秒、三个轻量自有子进程：

1. 主线程阻塞读取时，整例截止清理两个保留句柄，其中 ignore_term fixture 升级至 KILL。
2. 将本例 SELF RSS 阈值降低到已有高水位之下，watchdog 自动触发 SELF_RSS_SAMPLED_STOP，打断阻塞读取并完成自有 ignore_term 子进程的 KILL/wait。该测试没有新增内存压力分配，也没有测量子进程 RSS。
3. 科学入口在 Popen 前以 EXTERNAL_Z3_RSS_COVERAGE_UNAVAILABLE 拒绝，句柄数为零。

逐例断言全部句柄 reap、流关闭、watchdog 已 join、原 timer/handler/mask 恢复。独立验证总计创建 11 个轻量 fixture（初审 4、修复复测 4、正向验证 3），测试压力缓冲分配为零。作者 run01 与 run03 各有 7 项通过、7 个自有子进程、科学调用为零；作者 run01 通过不代表初审四条未覆盖异常路径当时正确。

## 适用范围及剩余工程门槛

- 运行范围是 macOS、由主线程拥有的单次上下文、仅有其继承 SIGALRM 屏蔽的 watchdog，生命周期内不新增其他未受控线程。spawn 要求主线程并检查其他 Python 线程；这不是对所有原生运行时线程的通用安全保证。
- 轻量 fixture 不产生后代；仅登记直接 Popen 句柄的实现不能据此声明覆盖任意子孙进程树。任意 preexec/Popen 设置阻塞、长期原生调用或持有 GIL 的计算不在此次保证内。
- `wall_seconds` 表示工作截止触发时间；TERM 宽限、KILL 与 wait 在截止后完成。作者 0.5 秒例耗时约 0.660 秒，不能表述为整个调用必定在 0.5 秒内返回。
- RUSAGE_SELF 是当前 Python 进程的高水位 RSS，不能覆盖外部 Z3 RSS；原生内存参数也不能替代缺失的外部 RSS 遥测。science_admission 必须保持 false，四个科学槽不得启动。
- 缺失外部 RSS 覆盖是工程准入门槛，不能推导为科学失败、假说被否定或研究终点。此次没有生成科学证据。

## 最终作者报告与原生探测复核

已仅读核对 `RESULT.zh.md`、`RECOVERY.zh.md`、两份 native probe 脚本及对应回执，没有另行执行原生探测。四个元数据/启动退出记录均退出 0、已 wait；空闲 Z3 记录为 0.3 秒工作截止、约 0.306370 秒返回、-15、已 wait。脚本没有发送 check-sat；仅启动退出例发送 `(exit)`。四科学槽均为 NOT_RUN，阶段时间 null。

对文件自身独立 stat/hash 核验：原二进制为 0644，副本为 0755，二者 SHA-256 均为 `edae32f9e37ea4b5bb35310d72f0e352d0dc07626cac4e9e30bc1ea9a5bc8efb`。审核者没有修改权限，也没有读取任何外部进程资源信息。

独立读取官方 z3-4.16.0 的 [命令行实现](https://raw.githubusercontent.com/Z3Prover/z3/z3-4.16.0/src/shell/main.cpp)、[参数实现](https://raw.githubusercontent.com/Z3Prover/z3/z3-4.16.0/src/util/env_params.cpp)及[内存管理实现](https://raw.githubusercontent.com/Z3Prover/z3/z3-4.16.0/src/util/memory_manager.cpp)，确认报告将内部分配计数与 OS RSS 区分开来是准确的；线程局部计数同步取决于编译分支，报告已保留编译选项未核实的边界。

作者报告哈希（仅对应当前签署版本）：

- `RESULT.zh.md`：`efd12e9abc729c7b7f245d45890ccab5fec8135660fe6b26c1f34d33132e4b13`。

- `RECOVERY.zh.md`：`e36db0775e99133ae7d7240a6056442b8097b4515c48fa939b8647946412cefc`。

私有远端发布/备份完整性、DELIVERY_MANIFEST 完整性、历史语义准入及完整 Polygon 联合运行不在此次独立签署范围。作者须单独核验发布完成的声明。本轮仍为工程条件通过、RSS 门槛未通过，不产生科学否定或研究终止判断。
