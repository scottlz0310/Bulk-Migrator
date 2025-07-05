import sys
import re

LOG_PATH = "logs/transfer.log"

# コマンドライン引数でファイル名を指定
if len(sys.argv) < 2:
    print("Usage: python tests/analyze_single_file_log.py '<ファイル名の一部または全体>'")
    sys.exit(1)

keyword = sys.argv[1]

with open(LOG_PATH, encoding="utf-8") as f:
    log_lines = f.readlines()

# 指定ファイル名を含む全ログ行を抽出
matched_lines = [l for l in log_lines if keyword in l]

# パス部分を抽出（START/ERROR/DEBUGなどの行からパスを推定）
def extract_path(line):
    # 例: START: <path> など
    m = re.search(r': (.+?)( |$)', line)
    if m:
        return m.group(1)
    return None

paths = set()
for l in matched_lines:
    p = extract_path(l)
    if p:
        paths.add(p)

print(f"--- ログ中に '{keyword}' を含む行数: {len(matched_lines)} ---")
print(f"--- パスのバリエーション一覧（重複除去）---")
for p in sorted(paths):
    print(p)

print("\n--- サンプルログ行（最大20件）---")
for l in matched_lines[:20]:
    print(l.strip())
