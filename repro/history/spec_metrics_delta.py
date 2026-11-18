import json
import time
import urllib.request

base = "http://127.0.0.1:18020"
names = [
    "vllm:spec_decode_num_drafts_total",
    "vllm:spec_decode_num_draft_tokens_total",
    "vllm:spec_decode_num_accepted_tokens_total",
]

def metrics():
    with urllib.request.urlopen(base + "/metrics", timeout=10) as response:
        text = response.read().decode()
    result = dict.fromkeys(names, 0.0)
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        key, value = line.split()[:2]
        name = key.split("{")[0]
        if name in result:
            result[name] += float(value)
    return result

before = metrics()

payload = {
    "model": "qwen3.8-27b",
    "messages": [{
        "role": "user",
        "content": "请写一篇约1500字的科普文章，解释大模型权重量化如何降低部署成本，包含权重、缩放系数、量化误差和适用场景。直接输出正文。"
    }],
    "temperature": 0,
    "max_tokens": 512,
    "stream": False,
    "chat_template_kwargs": {"enable_thinking": False},
}

print("正在请求模型生成……", flush=True)
request = urllib.request.Request(
    base + "/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=300) as response:
    result = json.load(response)

print("用量:", result.get("usage"))
print("正文预览:", result["choices"][0]["message"].get("content", "")[:100])

print("等待统计刷新……", flush=True)
time.sleep(6)
after = metrics()

delta = [after[name] - before[name] for name in names]
print("本次新增草稿轮数:", delta[0])
print("本次新增草稿 token:", delta[1])
print("本次接受草稿 token:", delta[2])
if delta[1] > 0:
    print("草稿接受率:", f"{delta[2] / delta[1]:.2%}")
else:
    print("生成请求已完成，但没有记录到新增草稿，需要继续检查运行日志。")
