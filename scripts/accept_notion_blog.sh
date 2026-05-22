#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="${ROOT_DIR}/output/acceptance"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/notion_blog_$(date -u +%Y%m%dT%H%M%SZ).log"

echo "== Notion Blog 一键验收开始 =="
echo "Repo: $ROOT_DIR"
echo "Log:  $LOG_FILE"

echo
echo "[1/4] 运行单测"
python -m unittest tests/test_blog_pipeline.py | tee -a "$LOG_FILE"

echo
echo "[2/4] 编译检查"
python -m compileall trendradar/blog_pipeline.py trendradar/core/loader.py | tee -a "$LOG_FILE"

echo
echo "[3/4] 预检查 notion_blog 配置"
python - <<'PY' | tee -a "$LOG_FILE"
from trendradar.core.loader import load_config

cfg = load_config()
nb = cfg.get("NOTION_BLOG", {}) or {}
enabled = bool(nb.get("ENABLED", False))
token = (nb.get("TOKEN", "") or "").strip()
dbid = (nb.get("DATABASE_ID", "") or "").strip()
topics = nb.get("TOPICS", []) or []

print(f"enabled={enabled}")
print(f"token_configured={bool(token)}")
print(f"database_id_configured={bool(dbid)}")
print(f"topics_count={len(topics)}")

if not enabled:
    print("RESULT: SKIP (notion_blog.enabled=false)")
elif not token or not dbid:
    print("RESULT: DRY_RUN_ONLY (token/database_id 缺失)")
else:
    print("RESULT: READY_TO_PUBLISH")
PY

echo
echo "[4/4] 执行流水线 (limit=5)"
set +e
python -m trendradar.blog_pipeline --limit 5 | tee -a "$LOG_FILE"
PIPELINE_EXIT_CODE=${PIPESTATUS[0]}
set -e

echo
PUBLISHED_COUNT="$(grep -c "已发布到 Notion" "$LOG_FILE" || true)"
GENERATED_COUNT="$(grep -c "已生成(未发布)" "$LOG_FILE" || true)"
SKIP_COUNT="$(grep -c "已跳过博客生成与 Notion 发布" "$LOG_FILE" || true)"

echo "== 验收结果 =="
echo "published_count=${PUBLISHED_COUNT}"
echo "generated_only_count=${GENERATED_COUNT}"
echo "skip_count=${SKIP_COUNT}"
echo "pipeline_exit_code=${PIPELINE_EXIT_CODE}"
echo "log_file=${LOG_FILE}"

if [[ "${PUBLISHED_COUNT}" -gt 0 ]]; then
  echo "PASS: 已成功发布到 Notion。"
elif [[ "${GENERATED_COUNT}" -gt 0 ]]; then
  echo "WARN: 仅生成未发布，请检查 token/database_id。"
elif [[ "${SKIP_COUNT}" -gt 0 ]]; then
  echo "WARN: notion_blog.enabled=false，未执行发布。"
elif [[ "${PIPELINE_EXIT_CODE}" -ne 0 ]]; then
  echo "WARN: 流水线执行失败（通常是 AI/网络/代理配置问题），请查看日志定位原因。"
else
  echo "WARN: 未检测到预期日志，请检查 ${LOG_FILE}"
fi
