# 部署与复现

## 准备

1. 使用 Linux + NVIDIA CUDA 环境、与本归档 [HyperQwen 快照](../upstream/HyperQwen/) 对应的 Python / vLLM 版本和补丁。历史环境是 Python 3.12.15、vLLM 0.31.0、PyTorch 2.13.0 和 Transformers 5.17.0；[包目录记录](../configs/package-dist-info.txt)是环境清单，不是可直接安装的 lockfile。先阅读快照内的 [安装说明](../upstream/HyperQwen/docs/install.md) 和 [vLLM 0.31 说明](../upstream/HyperQwen/docs/vllm-0.31.md)，确认 CUDA 与 GPU 架构匹配。
2. 从有访问权的来源准备模型，再按上游文档准备量化头和 MTP 张量。这里的 [模型卡](../configs/model/README.md)介绍原始 AutoRound 发布物，当前服务器配置有后续修改，不能用模型卡替代 [实际量化检查](../configs/model-format-check.json)。本仓库不包含可直接加载的权重。
3. 对应仓库快照内的 `patches/series` 检查补丁状态；小词表额外核对 [草稿词表补丁](../upstream/HyperQwen/patches/qwen3_5-mtp-draft-vocab.patch) 是否已应用。单有 JSON 或设置 `MTP_DRAFT_VOCAB=1` 不会生成量化 draft head。要复原 ID 张量，可检查 JSON 后，用 PyTorch 将其保存为 `torch.long`；仍然需要匹配的模型与 head。

## 启动

```bash
MODEL=/absolute/path/to/Qwen3.8-27B-W4A16-AutoRound \
HYPERQWEN_DIR=/absolute/path/to/HyperQwen \
bash repro/run_profile.sh baseline
```

依次切换 profile：`baseline`、`mtp-small-vocab`、`mtp-full-vocab`、`mtp-spec-attn`、`mtp-k2`、`mtp-k4`、`mtp-best`、`mtp-prefix-cache`。各次停止上一组再启动下一组，默认端口 18020 仅绑定本机。prefix-cache 组的缓存开关来自日志；其余启动参数以 [历史白名单配置](../configs/launch-options.json) 为准。脚本是便于复跑的包装，不声称复刻每个历史环境变量。

## 客户端验证

```bash
curl --fail http://127.0.0.1:18020/v1/models
python repro/history/sse_decode_early.py
python repro/history/spec_metrics_delta.py
python repro/history/prefix_cache_probe.py
```

原客户端脚本是服务器历史中提取的代码，默认连本机 18020。SSE 压测用固定中文 prompt、greedy、最多 512 输出 token、先预热，随后重复测量；输出近似 decode tok/s、首段正文等待与端到端速度。SSE 分块不一定逐 token，首段正文也可能晚于第一条 reasoning delta。prefix probe 先用另一份前缀预热，再重复相同长前缀并更换尾部问题，同时记录 `cached_tokens`。如果给本地服务启用了鉴权，使用环境注入令牌的客户端，勿把令牌写入探针或日志。

建议每组保存客户端输出、服务启动日志、硬件版本、相同请求参数和重复次数；对比 k 时固定前缀策略、输入、采样、并发与输出长度；对比前缀缓存时额外分开冷请求与复用请求。历史恢复脚本与其来源见 [索引](../repro/history/index.json)。
