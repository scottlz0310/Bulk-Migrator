import json
import re

# 設定
FILELIST_PATH = "logs/onedrive_transfer_targets.json"  # 生成されたファイルリスト
LOG_PATH = "logs/transfer.log"  # 転送ログ

# ファイルリスト読み込み
with open(FILELIST_PATH, encoding="utf-8") as f:
    filelist = json.load(f)

# ログ読み込み
with open(LOG_PATH, encoding="utf-8") as f:
    log_lines = f.readlines()

# ファイルごとにログ上の出現・エラー状況を調査
def analyze_file_in_log(fileinfo, log_lines):
    name = fileinfo["name"]
    path = fileinfo["path"]
    # ログ上でのパス出現回数
    path_count = sum(path in line for line in log_lines)
    # 404やエラーの有無
    error_lines = [l for l in log_lines if path in l and ("404" in l or "Not Found" in l or "ERROR" in l)]
    # 成功ログの有無
    success_lines = [l for l in log_lines if path in l and ("SUCCESS" in l or "完了" in l)]
    return {
        "name": name,
        "path": path,
        "log_count": path_count,
        "error_count": len(error_lines),
        "success_count": len(success_lines),
        "error_lines": error_lines[:3],  # 先頭3件だけ
        "success_lines": success_lines[:3],
    }

def main():
    results = []
    for f in filelist:
        res = analyze_file_in_log(f, log_lines)
        results.append(res)
    # サマリ出力
    print(f"{'path':60} | log | error | success")
    print("-"*90)
    for r in results:
        print(f"{r['path'][:60]:60} | {r['log_count']:3} | {r['error_count']:5} | {r['success_count']:7}")
    # 詳細出力例（エラー多発ファイルのみ）
    print("\n--- Error details (top 5 files) ---")
    for r in sorted(results, key=lambda x: -x['error_count'])[:5]:
        print(f"\n{r['path']}")
        for l in r['error_lines']:
            print(l.strip())

if __name__ == "__main__":
    main()
