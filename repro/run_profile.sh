#!/usr/bin/env bash
set -euo pipefail

archive_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
: "${MODEL:?Set MODEL to the prepared model directory}"
hyperqwen_dir="${HYPERQWEN_DIR:-$archive_root/upstream/HyperQwen}"
profile="${1:-baseline}"
export SPEC=mtp DRAFT_TOKENS=3 MTP_DRAFT_VOCAB=0 PREFIX_CACHE=0 SPEC_ATTN=1

case "$profile" in
  baseline) SPEC=off; SPEC_ATTN=0 ;;
  mtp-small-vocab) MTP_DRAFT_VOCAB=1; SPEC_ATTN=0 ;;
  mtp-full-vocab) SPEC_ATTN=0 ;;
  mtp-spec-attn|mtp-best) ;;
  mtp-k2) DRAFT_TOKENS=2 ;;
  mtp-k4) DRAFT_TOKENS=4 ;;
  mtp-prefix-cache) PREFIX_CACHE=1 ;;
  *) printf 'Unknown profile: %s\n' "$profile" >&2; exit 2 ;;
esac

export MODEL CTX=fast MAX_LEN=8192 MAX_SEQS=1 GPU_UTIL=0.90 VISION=0 TOOLS=0
export HOST=127.0.0.1 PORT="${PORT:-18020}"
cd -- "$hyperqwen_dir"
exec bash single-user/start_qwen.sh
