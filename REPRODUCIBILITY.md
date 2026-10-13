# 编译与复现入口（禁止把接收检查当新实验）

## 目录与源版本

解压三个独立包到同一父目录，均产生 `CaliberGraph/`。核心包MANIFEST.sha256覆盖合并内容；DOWNLOADS.json记录各包hash。最新矩阵是 `02_latest_matrix_addendum/CaliberGraph_empirical_evidence.zip` 内的 `matrix29/`；CSV/PDF保持原hash，ZIP因项目专属整理已重建。现存实验脚本均来自历史源，派生变更见CLEAN_TRANSFORMATIONS.json，不可直接在冻结目录重跑。

## 本次完成的验证范围

执行的检查仅为：路径安全与CRC/逐文件SHA256、Python脚本AST语法、保存JSON/CSV静态计数、LaTeX在新解压副本的编译入口。没有执行训练、SQL、solver或新实验。PDF历史自动bbox审计失败已披露；本次不重绘论文或冒称重新完成科学/版式独审。

在解压目录运行：

```sh
python3.12 tools/verify_handoff.py --root .
python3.12 tools/check_saved_matrix.py --zip 02_latest_matrix_addendum/CaliberGraph_empirical_evidence.zip
```

前者不import实验模块；后者只解析已保存结果，严格保留33×2分母。

## 论文编译

候选入口 `01_manuscript/candidate24/latex/main.tex`，原稿入口 `01_manuscript/original_wording11/latex/main.tex`；需TeX Live中的elsarticle、booktabs、tabularx、ams、hyperref、TikZ及参考文献工具。附页入口 `02_latest_matrix_addendum/CaliberGraph_empirical_addendum.tex`。在新输出目录执行pdflatex/bibtex/pdflatex/pdflatex（附页无bibtex），不得覆盖已交付PDF。LaTeX/Overleaf源已按目录随包，不为节省文件名改写公式或正文。

## 作者代码与运行依赖

- 原v5：`03_original_v5/runtime_fair_v5_statusfix/`、`runtime_v4/`、`contract_bridge_v1/`及`experiments/run_v5_*.py`；原始配置/队列JSON和`runs/`在同包。实际原生Z3是4.12、官方fast bindings，部分代码依赖旧macOS绝对路径。
- 自然诊断：`05_natural_and_mechanism/calibergraph_polygon_*`中的作者broker/owned_processes/run_batch/slot_worker；四例版本分别看13/16/17的FREEZE与README。COUNT20包保留P1/P2/P3最小patch、42回归及失败001/002，不含整份未核许可的上游runtime。
- 最新矩阵：内嵌ZIP的 `matrix29/prepare.py, common.py, worker.py, run_batch.py, owned_processes.py`；数据输入99文件、原候选116、预执行签字/最终独审已保存。`ATTEMPT_STARTED.json`只允许历史一次，不删除锁以重跑。`summarize.py`只读派生，但含原路径预期，迁移应在新目录做。
- ParSEval：Python>=3.10（实跑3.12）、SQLGlot23.12.1、SQLAlchemy2.0.49、Z3 4.16.0、SQLite3.53.3；代码Apache许可随包。准确依赖记录见pilot13 DEPENDENCIES.json、PIP_REPORT与各结果版本字段。
- Polygon：上游Python>=3.11；固定commit、作者资源覆写和各query-specific adapter不可混用。矩阵只使用pilot13 UA，没有装载COUNT修复。原生Z3二进制为macOS，Claude环境需本机适配及新版本指纹；不声称不同平台二进制hash相同。

## 不能自动复现的边界

完整上游代码/平台依赖/大型原始cache尚需按清单恢复；历史脚本绝对路径也需在独立工作副本迁移。因此此包是证据与作者源代码的可核对交接，不是即解即跑的全依赖镜像。原始结果/失败不可因恢复不便重写。恢复环境后若要重新求解，需用户另行同意具体协议和资源预算；不是本次任务的一部分。仅编译入口与静态脚本检查通过不能认证科学复现成功。
