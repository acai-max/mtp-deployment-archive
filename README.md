# Qwen3.8-27B MTP 部署与测评归档

这里的 MTP 指 **Multi-Token Prediction（多 token 预测）**。在 vLLM 的推测解码中，MTP 模块先提出若干候选 token，再由目标模型验证。本仓库记录在单卡环境对 Qwen3.8-27B 量化模型进行的 MTP 实验，不是模型权重镜像。

## 从哪里看

| 想了解 | 入口 |
|---|---|
| 服务器上测到了什么、哪些结论不成立 | [测评报告](docs/evaluation.md)、[逐窗口 CSV](data/windows.csv)、[汇总 CSV](data/summary.csv) |
| 怎么启动 baseline、full-vocab、k=2/3/4 和 prefix-cache | [部署与复现](docs/reproduction.md)、[实验启动脚本](repro/run_profile.sh) |
| 小词表、显存预算、缓存命中与版本兼容 | [避坑指南](docs/gotchas.md) |
| 核对原证据、模型配置和实验来源 | [8 份脱敏日志](logs/)、[配置](configs/)、[文件清单](MANIFEST.json) |
| 查上游实现和其他机器的测评 | [HyperQwen 代码快照](upstream/HyperQwen/)、[上游测评](upstream/HyperQwen/docs/benchmarks.md) |

历史实验日期为 **2026-10-21**，归档日期为 **2026-11-18**。上游记录固定到 [HyperQwen `95ac251`](https://github.com/syv-ai/HyperQwen/tree/95ac251bc3b71017c883e83004cf4fb188d066a4)。本机实验与上游其他设备的结果分开记录；归档没有重跑 GPU 压测。

## 首要结论

- 同一批历史日志中，受限草稿词表的 token 接受率为 **9.85%**，完整词表（未开 spec attention）为 **45.16%**。复现中文任务时，先用完整词表做对照。
- spec attention、草稿长度和 prefix cache 都会改变可用 KV 容量；baseline 为 **87,722 token**，完整词表 + spec attention 的 k=3 为 **45,568 token**。不能只看生成速度。
- 日志包含服务端窗口统计；脚本会打印客户端首段延迟和耗时，但没有找到当时的完整客户端结果。因此不把窗口峰值或文件名中的 “best” 写成端到端提速结论。

## 数据边界

发布了实验日志、可读配置及备份、草稿词表 ID、提取的实验脚本、已固定版本的上游代码与说明。保留上游及各组件许可证；模型卡保留原出处。日志中的访问凭据和实例专属路径已脱敏。未发布原始 Shell 历史、模型权重与备份、完整 tokenizer、虚拟环境及上游两项演示媒体。云平台系统日志与其他项目不在采集范围内。
