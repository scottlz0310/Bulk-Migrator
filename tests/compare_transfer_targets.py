import json
import os

def load_targets(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def compare_targets(file1, file2):
    targets1 = load_targets(file1)
    targets2 = load_targets(file2)

    # ルートフォルダ名を無視して path, name, size で比較
    def strip_root(path):
        parts = path.lstrip('/').split('/')
        return '/'.join(parts[1:]) if len(parts) > 1 else ''

    set1 = set((strip_root(t['path']), t['name'], t['size']) for t in targets1)
    set2 = set((strip_root(t['path']), t['name'], t['size']) for t in targets2)

    only1 = set1 - set2
    only2 = set2 - set1

    print(f"{file1} にのみ存在: {len(only1)} 件 (ルートフォルダ名無視)")
    for p, n, s in sorted(only1):
        print(f"  {p} ({n}, size={s})")
    print(f"{file2} にのみ存在: {len(only2)} 件 (ルートフォルダ名無視)")
    for p, n, s in sorted(only2):
        print(f"  {p} ({n}, size={s})")

    # lastModifiedDateTime の違いも出す（ルートフォルダ名無視）
    path2info2 = { (strip_root(t['path']), t['name'], t['size']): t for t in targets2 }
    diff_time = []
    for t in targets1:
        key = (strip_root(t['path']), t['name'], t['size'])
        if key in path2info2:
            t2 = path2info2[key]
            if t.get('lastModifiedDateTime') != t2.get('lastModifiedDateTime'):
                diff_time.append((strip_root(t['path']), t['lastModifiedDateTime'], t2.get('lastModifiedDateTime')))
    print(f"lastModifiedDateTime が異なるファイル: {len(diff_time)} 件 (ルートフォルダ名無視)")
    for p, t1, t2 in diff_time:
        print(f"  {p}: {t1} vs {t2}")

if __name__ == "__main__":
    # デフォルトパス
    file1 = os.path.join('logs', 'onedrive_transfer_targets.json')
    file2 = os.path.join('logs', 'sharepoint_transfer_targets.json')
    compare_targets(file1, file2)
