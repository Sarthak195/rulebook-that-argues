#!/bin/bash
# GCE startup script: installs the service on a fresh Debian 12 VM and starts it on port 80.
# Re-runs on every boot; each step is idempotent. Progress is echoed to the serial console,
# so `gcloud compute instances get-serial-port-output <vm>` shows what happened.
#
# Expects two instance metadata attributes:
#   openrouter-key    the OpenRouter API key (free-tier models are enough)
#   repo-url          the public git repository to deploy
set -euo pipefail
exec > >(tee -a /var/log/rulebook-startup.log) 2>&1
echo "=== rulebook startup $(date -u +%FT%TZ) ==="

META="http://metadata.google.internal/computeMetadata/v1/instance/attributes"
KEY=$(curl -sf -H "Metadata-Flavor: Google" "$META/openrouter-key" || true)
REPO=$(curl -sf -H "Metadata-Flavor: Google" "$META/repo-url" || echo "https://github.com/Sarthak195/rulebook-that-argues.git")
MODEL=$(curl -sf -H "Metadata-Flavor: Google" "$META/openrouter-model" || echo "minimax/minimax-m3:free")
APP=/opt/rulebook

# --- swap: torch + the embedding model need ~1.2 GB; e2-small has 2 GB -------------------
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo "swap enabled"
fi

# --- packages -------------------------------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git curl > /dev/null
echo "packages installed"

# --- code -----------------------------------------------------------------------------------
if [ -d "$APP/.git" ]; then
  git -C "$APP" pull -q --ff-only || true
else
  git clone -q "$REPO" "$APP"
fi
cd "$APP"
printf 'OPENROUTER_API_KEY=%s\nOPENROUTER_MODEL=%s\n' "$KEY" "$MODEL" > .env
chmod 600 .env
echo "code at $(git rev-parse --short HEAD)"

# --- python ---------------------------------------------------------------------------------
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
.venv/bin/pip install -q --upgrade pip
# CPU-only torch keeps the install at ~200 MB instead of ~2.5 GB of CUDA wheels.
.venv/bin/pip install -q torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -q -r requirements.txt
echo "dependencies installed"

# --- index (downloads the embedding model once) ---------------------------------------------
.venv/bin/python scripts/ingest.py | tail -3

# --- service --------------------------------------------------------------------------------
cat > /etc/systemd/system/rulebook.service <<UNIT
[Unit]
Description=The Rulebook That Argues With Itself
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=$APP
ExecStart=$APP/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 1
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable -q rulebook
systemctl restart rulebook
echo "service started"

# --- HTTPS URL via a Cloudflare quick tunnel (no account needed; URL changes on restart) -------
if ! command -v cloudflared > /dev/null; then
  curl -sL -o /tmp/cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
  dpkg -i /tmp/cloudflared.deb > /dev/null
fi
cat > /etc/systemd/system/rulebook-tunnel.service <<UNIT
[Unit]
Description=Cloudflare quick tunnel for the rulebook service
After=rulebook.service

[Service]
ExecStart=/usr/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:80
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable -q rulebook-tunnel
systemctl restart rulebook-tunnel

# Wait for the app, then print both URLs to the serial console.
for i in $(seq 1 60); do
  if curl -sf http://127.0.0.1/health > /dev/null; then break; fi
  sleep 5
done
IP=$(curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip || true)
echo "HEALTH: $(curl -sf http://127.0.0.1/health || echo unreachable)"
echo "URL-IP: http://$IP/   URL-DNS: http://$IP.nip.io/"
for i in $(seq 1 24); do
  T=$(journalctl -u rulebook-tunnel --no-pager 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1 || true)
  if [ -n "$T" ]; then echo "URL-TUNNEL: $T"; break; fi
  sleep 5
done
echo "=== rulebook startup done $(date -u +%FT%TZ) ==="
