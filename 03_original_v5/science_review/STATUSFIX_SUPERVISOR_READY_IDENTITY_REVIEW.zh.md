# 新 statusfix supervisor 注册身份独立复核

结论：当前锁与六源身份可用于父任务已明确授权的 **14 槽**小型集成；这不是运行 PASS，也不是论文科学放行。复核者为不同 AI，非真人评阅；本轮未导入或执行任何目标/native/solver/SQL。

- READY 锁：`16c76c134cdca4ef9461506968cecbbdb73ce6bc6304acdbeb7e878f19613d18`。独立核对 854 文件全部匹配，12 根目录清单完全匹配且无 symlink。相对原 pending 仅 `status` 和集成注册 metadata 改变，六源及全部依赖字节不变。
- suite：`84b1077a998a5cac1d05e6ad5631fc3f6b0f6a618f0e228402c2eb70c08f12e9`。四个原 case 字典完整不变，24 个注册 cost 槽中只选择索引 5–18 共 14，另外 10 个保留 NOT_RUN；不运行 differential。预期 1 SAT、6 UNSAT、6 C-UNSAT 拒绝、1 合同未验证；7 RETURNED 与 7 NOT_RUN_CONTRACT_STOP。父已明确批准 14，不能仍按 4 计分母/资源。
- 新 precheck `c29fddb633977267de78b42d0df62e2de43b2fdc1f04fb6d50ce1fe5699b3751` 绑定当前锁/suite/命令；旧 `4fe69…` 对象回执保留为历史。命令 `51ef33f1a5ff81fdff7a2ffce055b9c65fdfb1a9420872f0dd684433990ee125` 已固定现有项目 `.venv/bin/python -B -I -S`，入口与解释器哈希相符。

`supervisor.py:151` 的 valid-completed gate 没有显式检查 `RETURNED_INCOMPLETE_RECEIPT`。这属于防御/故障注入覆盖缺口：当前可正常 exit0 的 SAT/UNSAT 路径在 `worker.py:326` 回调前关闭 attempt/oracle 状态；异常走 exit2，中断不能返回该回调。静态检查未证明当前存在 COMPLETE + exit0 + incomplete-receipt 的可达 P0/P1 路径；这不是形式不可达证明。若人为注入不一致报告或未来逻辑回归，现 gate 可能接受，因此后续硬化应新建版本及专门故障注入，不改此次六源身份。14 槽覆盖正常返回及 typed stop，不覆盖该注入情形。

外部 24+24 回归实际执行的是 worker；虽有 supervisor 源文件哈希，不能继承为新 supervisor 实跑。父需另核这次全部 14 个实际回执：正常 7 槽 exit0，typed 7 槽 exit2，所有资源观察无异常、cleanup/日志传播一致。总体 supervisor exit2 为 typed 负控的预期，不应当成“全通过”。新成本不得替换冻结主 168 槽或并入其性能数据。身份审查不确认科学新意、泛化或投稿通过。
