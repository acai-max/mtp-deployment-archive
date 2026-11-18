import json
import time
import uuid
import urllib.request

url = "http://127.0.0.1:18020/v1/chat/completions"

document = "\n".join(
    f"第{i:03d}条：权重量化减少权重存储，缩放系数用于近似恢复数值；"
    "前缀缓存复用相同输入的计算，MTP通过生成和验证草稿加速输出。"
    for i in range(80)
)

def ask(prefix, question, max_tokens=64):
    payload = {
        "model": "qwen3.8-27b",
        "messages": [{
            "role": "user",
            "content": prefix + "\n资料：\n" + document
                       + "\n问题：" + question + "\n请简短回答。"
        }],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    start = time.perf_counter()
    first = None
    usage = {}
    answer = ""

    with urllib.request.urlopen(request, timeout=300) as response:
        for raw in response:
            line = raw.decode().strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("usage"):
                usage = chunk["usage"]
            for choice in chunk.get("choices", []):
                content = choice.get("delta", {}).get("content")
                if content:
                    if first is None:
                        first = time.perf_counter()
                    answer += content

    details = usage.get("prompt_tokens_details") or {}
    print("输入 token:", usage.get("prompt_tokens"))
    print("缓存命中 token:", details.get("cached_tokens", "未返回"))
    if first is not None:
        print("首段正文等待:", round(first - start, 3), "秒")
    else:
        print("未收到正文")
    print("回答:", answer[:120])
    print()

print("先用另一份前缀预热，不计入对照。", flush=True)
ask("预热编号：" + uuid.uuid4().hex, "权重量化有什么作用？", 16)

prefix = "实验编号：" + uuid.uuid4().hex
questions = [
    "资料中的权重量化有什么作用？",
    "资料中的前缀缓存有什么作用？",
    "资料中的MTP有什么作用？",
]

for i, question in enumerate(questions, 1):
    print(f"正式请求 {i}", flush=True)
    ask(prefix, question)
