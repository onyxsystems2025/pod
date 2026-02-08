#!/bin/bash
# ============================================================
# Script di setup per VM Ubuntu 24.04 LTS
# Eseguire come root dentro la VM
# ============================================================
set -e

echo "=== Aggiornamento sistema ==="
apt update && apt upgrade -y

echo "=== Installazione prerequisiti ==="
apt install -y curl git ca-certificates gnupg lsb-release sudo ufw

echo "=== Creazione utente podadmin ==="
if ! id "podadmin" &>/dev/null; then
    adduser --disabled-password --gecos "POD Admin" podadmin
    usermod -aG sudo podadmin
    echo "podadmin ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/podadmin
    echo "Utente podadmin creato."
else
    echo "Utente podadmin esiste gia."
fi

echo "=== Installazione Docker ==="
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Aggiungere utente al gruppo docker
usermod -aG docker podadmin

echo "=== Configurazione firewall ==="
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw --force enable

echo "=== Verifica Docker ==="
docker run --rm hello-world

echo ""
echo "============================================"
echo "  Setup completato!"
echo "  Ora esegui come utente podadmin:"
echo "    su - podadmin"
echo "    (poi esegui lo script deploy.sh)"
echo "============================================"
