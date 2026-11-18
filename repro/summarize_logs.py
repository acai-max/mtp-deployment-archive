import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIMESTAMP = re.compile(r"\b(\d\d-\d\d \d\d:\d\d:\d\d)\b")
GENERATION = re.compile(r"Avg generation throughput: ([\d.]+) tokens/s")
KV_CAPACITY = re.compile(r"GPU KV cache size: ([\d,]+) tokens")
DRAFT_LENGTH = re.compile(r"'num_speculative_tokens': (\d+)")
SPEC_METRICS = re.compile(
    r"Mean acceptance length: ([\d.]+), Accepted throughput: ([\d.]+) tokens/s, "
    r"Drafted throughput: ([\d.]+) tokens/s, Accepted: (\d+) tokens, "
    r"Drafted: (\d+) tokens, Per-position acceptance rate: ([\d., ]+), "
    r"Avg Draft acceptance rate: ([\d.]+)%"
)
WINDOW_FIELDS = [
    "run", "log_line", "time_in_log", "event", "generation_tok_s",
    "mean_acceptance_length", "accepted_tok_s", "drafted_tok_s", "accepted",
    "drafted", "per_position_acceptance", "acceptance_pct",
]
SUMMARY_FIELDS = [
    "run", "draft_length", "spec_windows", "accepted", "drafted",
    "weighted_acceptance_pct", "kv_tokens", "generation_windows", "peak_window_gen_tok_s",
]


def summarize(path):
    content = path.read_text(encoding="utf-8")
    windows = []
    generated = []
    accept_total = draft_total = spec_windows = 0
    for number, line in enumerate(content.splitlines(), start=1):
        generation = GENERATION.search(line)
        speculative = SPEC_METRICS.search(line)
        if not (generation or speculative):
            continue
        timestamp = TIMESTAMP.search(line)
        common = dict(run=path.stem, log_line=number, time_in_log=timestamp[1] if timestamp else "")
        if generation:
            generated.append(float(generation[1]))
            windows.append(dict(common, event="generation", generation_tok_s=generation[1]))
        if speculative:
            mean_length, accept_rate, draft_rate, accepted, drafted, positions, percent = speculative.groups()
            accept_total += int(accepted)
            draft_total += int(drafted)
            spec_windows += 1
            windows.append(dict(common, event="speculation", mean_acceptance_length=mean_length,
                                accepted_tok_s=accept_rate, drafted_tok_s=draft_rate, accepted=accepted,
                                drafted=drafted, per_position_acceptance=positions, acceptance_pct=percent))
    capacity = KV_CAPACITY.search(content)
    length = DRAFT_LENGTH.search(content)
    summary = dict(
        run=path.stem, draft_length=length[1] if length else "",
        spec_windows=spec_windows, accepted=accept_total, drafted=draft_total,
        weighted_acceptance_pct=f"{100 * accept_total / draft_total:.2f}" if draft_total else "",
        kv_tokens=capacity[1].replace(",", "") if capacity else "",
        generation_windows=len(generated), peak_window_gen_tok_s=max(generated, default=""),
    )
    return windows, summary


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    windows, summaries = [], []
    for path in sorted((ROOT / "logs").glob("*-server.log")):
        records, summary = summarize(path)
        windows.extend(records)
        summaries.append(summary)
    if not summaries:
        raise SystemExit("No server logs found")
    (ROOT / "data").mkdir(exist_ok=True)
    write_csv(ROOT / "data" / "windows.csv", WINDOW_FIELDS, windows)
    write_csv(ROOT / "data" / "summary.csv", SUMMARY_FIELDS, summaries)


if __name__ == "__main__":
    main()
