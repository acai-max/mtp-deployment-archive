# MTP 部署避坑

| 现象 | 优先检查 |
|---|---|
| 开启小词表后接受率异常低 | 优先用 `MTP_DRAFT_VOCAB=0` 做控制实验，核对语种和域；检查 ID 映射、`mtp.draft_lm_head.*` 与补丁是否匹配。历史数据中小词表约 9.85%，不是普遍阈值。 |
| 日志写着 MTP，但跑不快 | 核对 `speculative_config`，查 `SpecDecoding metrics` 或用指标探针取前后计数差；再看 TTFT 和真实端到端速度。只看到启动参数不代表有草稿被接受。 |
| 增大 k 后吞吐没增加 | 接受率会随草稿位置下降，验证和显存也有成本。先做 k=2/3/4 固定负载对照，不能只对比草稿吞吐。 |
| 开 MTP 后 KV 少了 | 对照启动日志中权重、激活、CUDA graph 和 KV 预算。实际最大长度、并发及显存水位要一起验证；不要把 8,192 配置当成可承受任意并发。 |
| 第二轮前缀请求命中不稳定 | 确保模板、缓存盐与前缀的 token 序列一致；核对 prefix cache 和 Mamba 设置。不要把进程累计命中率或一次短生成的 100% 接受率当成单请求结论。 |
| 模型能拉取但加载失败 | 对照 `compressed-tensors` 与实际索引：服务器验证报告是 pack-quantized，组位宽含 4/8 位，并发现 34 个 MTP 张量。检查索引、权重分片、量化配置和后端是否出自同一版本，不要混用 `.bak-mtp` 和现行索引。 |
| 修改开关好像没变化 | 查看实际输出的参数、编译缓存和补丁状态。尤其不同 attention backend 可能不适用同一个 `SPEC_ATTN` 开关，参照 [上游避坑](../upstream/HyperQwen/docs/gotchas.md) 和 [启动脚本](../upstream/HyperQwen/single-user/start_qwen.sh)。 |
| 测试流中有空行、心跳或迟到的 usage | SSE 需跳过非 data 事件；读到结束时保留最终 usage。区分首段正文与第一事件，不要用响应 chunk 数量替代 token 数。 |

不要把实验端口裸露在公网。上传任何追加日志前，排除 Authorization、API key、私有 URL、原始用户请求和终端历史。
