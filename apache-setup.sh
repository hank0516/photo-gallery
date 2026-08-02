#!/bin/bash
# Photo Gallery 部署腳本
# 執行前確認已 build frontend: cd frontend && npm run build
set -e

APACHE_CONF="/etc/apache2/sites-enabled/cloud.hansu.tw.conf"
SERVICE_SRC="/home/hank/my_websites/photo-gallery/photo-gallery-api.service"
DIST="/home/hank/my_websites/photo-gallery/frontend/dist"

# === 1. Systemd service ===
echo "1/4 Installing systemd service..."
sudo cp "$SERVICE_SRC" /etc/systemd/system/photo-gallery-api.service
sudo systemctl daemon-reload
sudo systemctl enable photo-gallery-api
sudo systemctl start photo-gallery-api
echo "✓ Service started"
systemctl status photo-gallery-api --no-pager -l

# === 2. Apache: photo-gallery-specific Alias (before generic /sites) ===
# We serve /sites/photo-gallery/ → frontend/dist/ (not the project root)
# This alias must appear BEFORE the generic "Alias /sites ..."
echo ""
echo "2/4 Adding Apache alias for frontend dist..."

if grep -q "photo-gallery/frontend/dist" "$APACHE_CONF"; then
    echo "✓ Alias already present"
else
    # Insert specific alias before the generic /sites alias
    sudo sed -i 's|Alias /sites "/var/www/html/sites"|Alias /sites/photo-gallery/ "'"$DIST"'/"\n                Alias /sites "/var/www/html/sites"|' "$APACHE_CONF"
    echo "✓ Added Alias /sites/photo-gallery/ → $DIST/"
fi

# === 3. Apache: SPA fallback + Directory block ===
echo ""
echo "3/4 Adding SPA fallback..."

if grep -q "photo-gallery SPA fallback" "$APACHE_CONF"; then
    echo "✓ SPA fallback already present"
else
    BLOCK="                # photo-gallery SPA fallback\\n                <Directory \"$DIST\">\\n                    Options -Indexes\\n                    AllowOverride None\\n                    Require all granted\\n                    FallbackResource /sites/photo-gallery/index.html\\n                </Directory>"
    # Insert after the mdeditor Directory block
    sudo sed -i '/FallbackResource \/sites\/mdeditor\/index.html/{
        n
        n
        a '"$BLOCK"'
    }' "$APACHE_CONF"
    echo "✓ Added SPA fallback"
fi

# === 4. Apache: API proxy (before expense-tracker) ===
echo ""
echo "4/4 Adding API proxy..."

if grep -q "photo-gallery API proxy" "$APACHE_CONF"; then
    echo "✓ Proxy already present"
else
    sudo sed -i 's|ProxyPass /api/expense-tracker/ |ProxyPass /api/photo-gallery/ http://127.0.0.1:8002/api/photo-gallery/\n                ProxyPassReverse /api/photo-gallery/ http://127.0.0.1:8002/api/photo-gallery/\n\n                ProxyPass /api/expense-tracker/ |' "$APACHE_CONF"
    echo "✓ Added proxy /api/photo-gallery/ → port 8002"
fi

# === 5. Test & reload ===
echo ""
echo "Testing Apache config..."
sudo apache2ctl configtest && sudo systemctl reload apache2
echo "✓ Apache reloaded"

echo ""
echo "============================================"
echo " 部署完成！"
echo " 前端: https://cloud.hansu.tw/sites/photo-gallery/"
echo " API:  https://cloud.hansu.tw/api/photo-gallery/docs"
echo "============================================"
