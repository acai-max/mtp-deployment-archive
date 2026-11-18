import json
import statistics
import time
import urllib.request

url = "http://127.0.0.1:18020/v1/chat/completions"

payload = {
    "model": "qwen3.8-27b",
    "messages": [{
        "role": "user",
        "content": (
            "请写一篇约1500字的科普文章，解释大模型权重量化如何"
            "降低部署成本，包含权重、缩放系数、量化误差和适用场景。"
            "直接输出正文。"
        ),
    }],
    "temperature": 0,
    "max_tokens": 512,
    "stream": True,
    "stream_options": {"include_usage": True},
    "chat_template_kwargs": {"enable_thinking": False},
}

def run_once():
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    first_content = None
    last_content = None
    usage = None
    parts = []

    start = time.perf_counter()

    with urllib.request.urlopen(request, timeout=300) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()

            # 跳过空行、心跳等，只处理SSE数据
            if not line.startswith("data:"):
                continue

            data = line[5:].strip()
            if data == "[DONE]":
                break

            event = json.loads(data)

            if event.get("usage"):
                usage = event["usage"]

            for choice in event.get("choices", []):
                content = choice.get("delta", {}).get("content")
                if content:
                    now = time.perf_counter()
                    if first_content is None:
                        first_content = now
                    last_content = now
                    parts.append(content)

    end = time.perf_counter()

    if not usage or first_content is None:
        raise RuntimeError("没有收到正文或token用量，请检查服务返回。")

    tokens = usage["completion_tokens"]
    total = end - start
    first_wait = first_content - start

    # 流式分块不一定逐token发送，因此这是近似生成速度
    decode_time = last_content - first_content
    decode_rate = (
        (tokens - 1) / decode_time
        if tokens > 1 and decode_time > 0 else 0
    )

    return {
        "tokens": tokens,
        "first_wait": first_wait,
        "total": total,
        "decode_rate": decode_rate,
        "end_to_end_rate": tokens / total,
        "text": "".join(parts),
    }

print("正在预热一次……")
run_once()
print("预热完成，开始正式测试。\n")

results = []

for i in range(1, 4):
    result = run_once()
    results.append(result)

    print(f"第{i}次")
    print("输出token数:", result["tokens"])
    print("首段正文等待:", round(result["first_wait"], 3), "秒")
    print("总耗时:", round(result["total"], 3), "秒")
    print("生成阶段估算速度:", round(result["decode_rate"], 2), "token/s")
    print("端到端输出速度:", round(result["end_to_end_rate"], 2), "token/s")
    print()

print("三次中位数:")
for key, label in [
    ("first_wait", "首段正文等待（秒）"),
    ("decode_rate", "生成阶段估算速度（token/s）"),
    ("end_to_end_rate", "端到端输出速度（token/s）"),
]:
    print(label, round(statistics.median(r[key] for r in results), 3))

print("\n第一轮正文预览:")
print(results[0]["text"][:200])
