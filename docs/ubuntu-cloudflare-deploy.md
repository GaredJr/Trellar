# Ubuntu Server + Cloudflare Tunnel Deployment

This guide deploys Trellar on Ubuntu as a `systemd` service and then exposes it through Cloudflare Tunnel when you are ready to attach your domain.

## 1) SSH into your Ubuntu server

From your Mac:

```bash
ssh <ubuntu-user>@<ubuntu-server-ip>
```

## 2) Clone and configure the app on Ubuntu

```bash
git clone <your-repo-url> Trellar
cd Trellar
[ -f .env ] || cp .env.example .env
```

Create or edit `.env` with your production values:

```bash
nano .env
```

Minimum recommended values:

```dotenv
FLASK_SECRET_KEY=replace-with-a-long-random-secret
TRELLAR_USE_SUPABASE=1
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## 3) Install and start Trellar as a service

Default is private origin (`127.0.0.1:8000`), best for Cloudflare Tunnel:

```bash
./scripts/install_ubuntu_service.sh
```

Check status and logs:

```bash
sudo systemctl status trellar
sudo journalctl -u trellar -f
```

## 4) Optional: allow direct LAN testing before Cloudflare

If you want to open the app on your local network first, bind to all interfaces:

```bash
BIND_HOST=0.0.0.0 PORT=8000 ./scripts/install_ubuntu_service.sh
```

If UFW is enabled, allow the port from your LAN:

```bash
sudo ufw allow from 192.168.0.0/16 to any port 8000 proto tcp
```

Then test from another device on your Wi-Fi:

```text
http://<ubuntu-server-ip>:8000
```

## 5) Later: connect the app to your domain through Cloudflare Tunnel

Install `cloudflared` on Ubuntu (use Cloudflare's official install docs for your Ubuntu version), then run:

```bash
cloudflared tunnel login
cloudflared tunnel create trellar
cloudflared tunnel list
```

Copy the tunnel UUID and configure hostname + service:

```bash
./scripts/install_cloudflare_tunnel.sh <tunnel-uuid> <subdomain.yourdomain.com> http://localhost:8000
```

Example:

```bash
./scripts/install_cloudflare_tunnel.sh 11111111-2222-3333-4444-555555555555 trellar.example.com http://localhost:8000
```

This script:

- Writes `/etc/cloudflared/config.yml`
- Copies tunnel credentials to `/etc/cloudflared/`
- Creates Cloudflare DNS route for your hostname
- Installs and starts the `cloudflared` service

Verify:

```bash
sudo systemctl status cloudflared
cloudflared tunnel info <tunnel-uuid>
```

Your app should then be reachable at:

```text
https://<subdomain.yourdomain.com>
```

## 6) Updating app code later

On Ubuntu:

```bash
cd ~/Trellar
git pull
./.venv/bin/pip install -r requirements.txt
sudo systemctl restart trellar
```
