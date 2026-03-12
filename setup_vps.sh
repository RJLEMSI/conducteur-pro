#!/bin/bash
# =============================================================================
# ConducteurPro - Script de migration VPS
# Ce script configure entièrement le VPS OVH pour héberger ConducteurPro
# =============================================================================

set -e

# --- Configuration ---
DOMAIN="conducteurpro.fr"
APP_DIR="/opt/conducteurpro"
REPO_URL="https://github.com/RJLEMSI/conducteur-pro.git"
DB_NAME="conducteurpro"
DB_USER="conducteurpro"
DB_PASS="ConducteurProDB2026!Secure"
APP_PORT=8501
EMAIL="contact@conducteurpro.fr"

echo "========================================="
echo " ConducteurPro - Installation VPS"
echo "========================================="
echo ""

# --- 1. Mise à jour du système ---
echo "[1/9] Mise à jour du système..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx \
    postgresql postgresql-contrib ufw curl wget software-properties-common

# --- 2. Configuration du pare-feu ---
echo "[2/9] Configuration du pare-feu..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable
echo "Pare-feu activé (SSH + HTTP + HTTPS uniquement)"

# --- 3. Configuration de PostgreSQL ---
echo "[3/9] Configuration de PostgreSQL..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || echo "Utilisateur PostgreSQL existe déjà"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || echo "Base de données existe déjà"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
echo "PostgreSQL configuré: base=$DB_NAME, user=$DB_USER"

# --- 4. Cloner le dépôt ---
echo "[4/9] Clonage du dépôt ConducteurPro..."
sudo rm -rf $APP_DIR
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR
git clone $REPO_URL $APP_DIR
cd $APP_DIR

# --- 5. Environnement Python ---
echo "[5/9] Configuration de l'environnement Python..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# --- 6. Configuration des secrets Streamlit ---
echo "[6/9] Configuration des secrets..."
mkdir -p $APP_DIR/.streamlit

# Les secrets sont configurés via le script configure_secrets.sh
# qui sera téléchargé séparément (non versionné sur GitHub)
echo "IMPORTANT: Exécutez configure_secrets.sh après ce script pour configurer les clés API"

# --- 7. Service systemd ---
echo "[7/9] Création du service systemd..."
sudo tee /etc/systemd/system/conducteurpro.service > /dev/null << SERVICE_EOF
[Unit]
Description=ConducteurPro Streamlit App
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin:/usr/bin:/bin
ExecStart=$APP_DIR/venv/bin/streamlit run app.py --server.port=$APP_PORT --server.address=127.0.0.1 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable conducteurpro
echo "Service systemd créé (sera démarré après configuration des secrets)"

# --- 8. Configuration Nginx ---
echo "[8/9] Configuration de Nginx..."
sudo tee /etc/nginx/sites-available/conducteurpro > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name conducteurpro.fr www.conducteurpro.fr;

    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    location /_stcore/stream {
        proxy_pass http://127.0.0.1:8501/_stcore/stream;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
NGINX_EOF

sudo ln -sf /etc/nginx/sites-available/conducteurpro /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
echo "Nginx configuré"

# --- 9. Résumé ---
echo ""
echo "========================================="
echo " Installation terminée !"
echo "========================================="
echo ""
echo "PROCHAINES ÉTAPES :"
echo ""
echo "1. Configurer les secrets (clés API) :"
echo "   bash configure_secrets.sh"
echo ""
echo "2. Démarrer l'application :"
echo "   sudo systemctl start conducteurpro"
echo ""
echo "3. Configurer le DNS dans OVH :"
echo "   - Type A : conducteurpro.fr → 51.38.185.245"
echo "   - Type A : www.conducteurpro.fr → 51.38.185.245"
echo ""
echo "4. Une fois le DNS propagé (5-30 min), lancer :"
echo "   sudo certbot --nginx -d conducteurpro.fr -d www.conducteurpro.fr --email $EMAIL --agree-tos --non-interactive"
echo ""
echo "Ton app sera alors accessible sur https://conducteurpro.fr"
echo "========================================="
