#!/bin/bash
# Renovate systemd service セットアップスクリプト

set -e

echo "=== Renovate systemd service セットアップ ==="
echo ""

# 現在のディレクトリを確認
if [ ! -f "renovate.service" ]; then
    echo "エラー: このスクリプトはプロジェクトルートから実行してください"
    exit 1
fi

# 環境変数の確認
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "エラー: GITHUB_PERSONAL_ACCESS_TOKEN が設定されていません"
    echo ""
    echo "以下のコマンドで設定してください:"
    echo "  export GITHUB_PERSONAL_ACCESS_TOKEN='your_token_here'"
    exit 1
fi

echo "1. 環境変数ファイルを作成..."
sudo tee /etc/systemd/system/renovate.env > /dev/null << EOF
# Renovate systemd service用の環境変数
GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN
EOF

echo "2. 環境変数ファイルのパーミッションを設定..."
sudo chmod 600 /etc/systemd/system/renovate.env
sudo chown root:root /etc/systemd/system/renovate.env

echo "3. serviceファイルをコピー..."
sudo cp renovate.service /etc/systemd/system/renovate.service

echo "4. systemd設定を更新..."
sudo systemctl daemon-reload

echo "5. サービスを有効化（起動時に自動実行）..."
sudo systemctl enable renovate.service

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "=== 使い方 ==="
echo "手動実行:"
echo "  sudo systemctl start renovate.service"
echo ""
echo "ステータス確認:"
echo "  sudo systemctl status renovate.service"
echo ""
echo "ログ確認:"
echo "  sudo journalctl -u renovate.service -f"
echo ""
echo "無効化（起動時の自動実行を停止）:"
echo "  sudo systemctl disable renovate.service"
echo ""
echo "次回システム起動時にRenovateが自動実行されます。"
