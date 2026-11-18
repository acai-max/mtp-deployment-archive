import urllib.request

url = "http://127.0.0.1:18020/metrics"
with urllib.request.urlopen(url, timeout=10) as response:
    text = response.read().decode()

found = False
for line in text.splitlines():
    if not line or line.startswith("#"):
        continue
    name = line.split()[0].lower()
    if any(word in name for word in [
        "spec_decode", "speculative", "acceptance"
    ]):
        print(line)
        found = True

if not found:
    print("未找到投机解码指标，请查看服务日志中的接受率统计。")
