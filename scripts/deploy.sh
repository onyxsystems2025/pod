#!/bin/bash
# ============================================================
# Script di deploy - eseguire come utente podadmin
# ============================================================
set -e

APP_DIR="/home/podadmin/pod"

echo "=== Clone del repository ==="
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Inserisci l'URL del repository Git:"
    read -r REPO_URL
    git clone "$REPO_URL" "$APP_DIR"
else
    echo "Repository gia presente, aggiorno..."
    cd "$APP_DIR"
    git pull
fi

cd "$APP_DIR"

echo "=== Configurazione .env ==="
if [ ! -f .env ]; then
    cp .env.example .env

    # Genera SECRET_KEY casuale
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 50 | tr -d '\n')
    sed -i "s|SECRET_KEY=change-me-to-a-random-string|SECRET_KEY=$SECRET_KEY|" .env

    # Genera password DB casuale
    DB_PASSWORD=$(openssl rand -base64 24 | tr -d '\n/+=' | head -c 32)
    sed -i "s|DB_PASSWORD=pod|DB_PASSWORD=$DB_PASSWORD|" .env

    # Imposta settings produzione
    sed -i "s|DEBUG=True|DEBUG=False|" .env
    sed -i "s|DJANGO_SETTINGS_MODULE=config.settings.dev|DJANGO_SETTINGS_MODULE=config.settings.prod|" .env

    # Chiedi l'IP del server per ALLOWED_HOSTS
    echo ""
    echo "Inserisci l'IP del server LXC (es: 192.168.1.200):"
    read -r SERVER_IP
    sed -i "s|ALLOWED_HOSTS=localhost,127.0.0.1|ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP|" .env
    sed -i "s|CORS_ALLOWED_ORIGINS=http://localhost:8000|CORS_ALLOWED_ORIGINS=http://localhost:8000,http://$SERVER_IP|" .env

    # DB host per Docker
    sed -i "s|DB_HOST=localhost|DB_HOST=db|" .env

    # Redis per Docker
    sed -i "s|redis://localhost|redis://redis|g" .env

    echo ""
    echo "File .env creato e configurato."
    echo "Puoi modificarlo ulteriormente con: nano $APP_DIR/.env"
    echo ""
else
    echo "File .env gia presente, salto configurazione."
fi

echo "=== Build e avvio Docker Compose ==="
docker compose build
docker compose up -d

echo "=== Attesa avvio database (10s) ==="
sleep 10

echo "=== Migrazione database ==="
docker compose exec web python manage.py migrate

echo "=== Raccolta file statici ==="
docker compose exec web python manage.py collectstatic --noinput

echo "=== Creazione superuser ==="
echo ""
echo "Crea l'utente amministratore:"
docker compose exec -it web python manage.py createsuperuser

echo ""
echo "============================================"
echo "  Deploy completato!"
echo ""
echo "  Backoffice: http://$SERVER_IP/"
echo "  Admin:      http://$SERVER_IP/admin/"
echo "  API Docs:   http://$SERVER_IP/api/docs/"
echo "  PWA:        http://$SERVER_IP/pwa/"
echo ""
echo "  Comandi utili:"
echo "    docker compose logs -f         # Vedi i log"
echo "    docker compose ps              # Stato servizi"
echo "    docker compose restart web     # Riavvia Django"
echo "    docker compose exec web python manage.py shell  # Shell Django"
echo "============================================"
