# Deployment

## Live instance

| what | where |
|---|---|
| VM | Google Compute Engine, `rulebook-vm`, `e2-small` (2 vCPU shared, 2 GB RAM + 2 GB swap), Debian 12, zone `asia-south1-a` (Mumbai) |
| Static IP | `34.93.55.172` (reserved as `rulebook-ip`) |
| Plain URL | http://34.93.55.172/ |
| DNS-style URL | http://34.93.55.172.nip.io/ (nip.io resolves any `<ip>.nip.io` name to that IP; nothing to register) |
| HTTPS URL | https://guy-easily-veterans-victorian.trycloudflare.com (a Cloudflare quick tunnel; it changes if the tunnel restarts, and the current one is always printed on the serial console, see below) |

First boot: VM created 16:44 UTC, service healthy at 16:51 UTC, six and a half minutes, of which
five were pip installing torch.

The deployed instance runs with `PROVIDER_ORDER=gemini,mistral,openrouter,groq`,
`SPREAD_PROVIDERS=gemini`, a single AI Studio key and a Mistral free-plan key. Ten Gemini keys
from ten projects were tried for an hour and Google suspended eight of the projects for quota
circumvention; see `docs/EVALUATION.md`. Settings beyond the fixed keys (provider order, the
Mistral lines) live in the `extra-env` instance metadata attribute, which the startup script
appends to `.env` on every boot:

```bash
printf 'EXTRA_PROVIDERS=mistral\nMISTRAL_URL=...\nMISTRAL_API_KEY=...\nMISTRAL_MODELS=...\nPROVIDER_ORDER=...\n' > extra.txt
gcloud compute instances add-metadata rulebook-vm --zone asia-south1-a --metadata-from-file extra-env=extra.txt
```

Cost: about USD 0.02 per hour for the VM while it runs, plus the static IP. Stop it with
`gcloud compute instances stop rulebook-vm --zone asia-south1-a` when the round is over.

## How it was created

Everything is in `deploy/startup.sh`; the VM runs it on every boot. The commands used, from a
machine with `gcloud` authenticated:

```bash
gcloud compute firewall-rules create rulebook-allow-http \
  --allow tcp:80 --target-tags rulebook-web --source-ranges 0.0.0.0/0

gcloud compute addresses create rulebook-ip --region asia-south1
IP=$(gcloud compute addresses describe rulebook-ip --region asia-south1 --format="value(address)")

gcloud compute instances create rulebook-vm \
  --zone asia-south1-a --machine-type e2-small \
  --image-family debian-12 --image-project debian-cloud --boot-disk-size 20GB \
  --tags rulebook-web --address "$IP" \
  --metadata-from-file startup-script=deploy/startup.sh \
  --metadata "openrouter-key=sk-or-v1-...,repo-url=https://github.com/Sarthak195/rulebook-that-argues.git,openrouter-model=minimax/minimax-m3:free"
```

The startup script:

1. adds a 2 GB swap file (torch plus the embedding model need about 1.2 GB);
2. installs Python, git and curl;
3. clones or pulls the repository into `/opt/rulebook` and writes `.env` from instance metadata
   (the key never enters the repository);
4. installs CPU-only torch and the requirements, builds the index (downloads the 130 MB
   embedding model once);
5. installs a `systemd` unit `rulebook.service` running uvicorn on port 80, restart-always;
6. installs `cloudflared` and a second unit `rulebook-tunnel.service` that opens a quick tunnel to
   port 80 for an HTTPS URL;
7. prints `HEALTH:`, `URL-IP:`, `URL-DNS:` and `URL-TUNNEL:` lines to the serial console.

First boot takes 6 to 10 minutes, almost all of it pip installing torch.

## Operating it

```bash
# what happened on boot, including the URLs
gcloud compute instances get-serial-port-output rulebook-vm --zone asia-south1-a | grep -E "URL-|HEALTH|startup"

# deploy a new commit: the startup script pulls and restarts on every boot
gcloud compute instances reset rulebook-vm --zone asia-south1-a

# or without a reboot (the service takes 20-40 s to load the embedding model on an e2-small)
gcloud compute ssh rulebook-vm --zone asia-south1-a --command \
  "cd /opt/rulebook && sudo git pull --ff-only && sudo systemctl restart rulebook"

# add a free Groq or Gemini key (picked up by the startup script on the next boot, or add the
# line to /opt/rulebook/.env over ssh and restart for an immediate effect)
gcloud compute instances add-metadata rulebook-vm --zone asia-south1-a --metadata "groq-key=gsk_..."
# several keys (only for keys that are legitimately separate; see docs/ARCHITECTURE.md):
# a comma list must go through a file, gcloud splits commas otherwise
echo "key1,key2" > keys.txt
gcloud compute instances add-metadata rulebook-vm --zone asia-south1-a --metadata-from-file gemini-keys=keys.txt
gcloud compute ssh rulebook-vm --zone asia-south1-a --command \
  "echo 'GROQ_API_KEY=gsk_...' | sudo tee -a /opt/rulebook/.env >/dev/null && sudo systemctl restart rulebook"

# change the model without a reboot (the startup script rewrites .env from metadata on boot,
# so also update the metadata for future boots)
gcloud compute instances add-metadata rulebook-vm --zone asia-south1-a --metadata "openrouter-model=<id>"
gcloud compute ssh rulebook-vm --zone asia-south1-a --command \
  "sudo sed -i 's#^OPENROUTER_MODEL=.*#OPENROUTER_MODEL=<id>#' /opt/rulebook/.env && sudo systemctl restart rulebook"

# logs
gcloud compute ssh rulebook-vm --zone asia-south1-a --command "sudo journalctl -u rulebook -n 100 --no-pager"

# stop / start / delete
gcloud compute instances stop   rulebook-vm --zone asia-south1-a
gcloud compute instances start  rulebook-vm --zone asia-south1-a
gcloud compute instances delete rulebook-vm --zone asia-south1-a
gcloud compute addresses delete rulebook-ip --region asia-south1
```

## Docker

```bash
docker build -t rulebook .
docker run --rm -p 8000:8000 --env-file .env rulebook
```

The image builds the index at build time, so the container answers within seconds of starting.
Roughly 1.1 GB because of torch.

## Local

See the README: venv, `pip install -r requirements.txt`, `.env`, `uvicorn app.main:app --reload`.
