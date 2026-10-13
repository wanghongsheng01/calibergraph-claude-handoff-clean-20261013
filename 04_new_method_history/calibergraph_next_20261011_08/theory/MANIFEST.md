# 文件完整性说明

- `SHA256SUMS.inputs`：本轮读取的07四个假说/见证文件及适用的 `/Users/loctek/AGENTS.md`。07文件只读，未修改。
- `SHA256SUMS.outputs`：本目录报告、三个JSON、此说明及输入manifest；不包含输出manifest自身，避免自引用哈希。
- 校验工作目录为 `/Users/loctek/Documents/Codex/2026-10-11/task-3`；执行 `LC_ALL=C shasum -a 256 -c calibergraph_next_20261011_08/theory/SHA256SUMS.outputs` 可复核输出字节。首次默认 C.UTF-8 locale 下 Perl 启动失败；明确 C locale 后重做完整哈希，无科学程序运行。
- 本轮仅运行了文件读写、JSON格式解析和SHA256元数据校验；没有运行fixture、SQL、solver、科学计算、模型、GPU或队列。
- JSON格式检查只确认可解析，不验证理论、实例语义或性能。
- 参考文献通过只读web工具核验，未下载/提交论文副本；引用版本和定位见 `references.json`。
- 私有GitHub备份由父任务统一处理；本子任务未提交或推送，不声称已通过备份门。
