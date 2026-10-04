#!/usr/bin/env bash
# Installs or updates Python from zero on an Ubuntu 24.04 (or newer) server, such as
# Google Cloud's free e2-micro. Run it from the folder where you uploaded the files:
#
#   First time:  sudo bash install.sh python-from-zero.tar.gz your-domain.example.com
#   Updates:     sudo bash install.sh python-from-zero.tar.gz
#
# What it sets up:
#   /opt/python-from-zero          the course files (replaced on every update)
#   /var/lib/python-from-zero      the database and daily backups (never replaced)
#   /etc/python-from-zero.env      your settings and secrets (made once, then yours to edit)
#   python-from-zero service       runs the app, restarts it if it stops, starts it on boot
#   Caddy                          serves the site on https with a free certificate
#   python-from-zero-backup timer  copies the database every day and keeps 14 days
set -euo pipefail

ARCHIVE="${1:?Give the path to python-from-zero.tar.gz, for example: sudo bash install.sh python-from-zero.tar.gz your-domain.com}"
DOMAIN="${2:-}"
APP=/opt/python-from-zero
DATA=/var/lib/python-from-zero
ENVFILE=/etc/python-from-zero.env
SERVICE=python-from-zero

say() { printf '\n== %s\n' "$*"; }

[ "$(id -u)" = 0 ] || { echo "Run this with sudo."; exit 1; }
[ -f "$ARCHIVE" ] || { echo "Can't find $ARCHIVE. Upload it first, or check the name."; exit 1; }

say "Checking Python"
python3 -c 'import sys; sys.exit(sys.version_info < (3, 12))' || {
  echo "This needs Python 3.12 or newer. Use an Ubuntu 24.04 LTS (or newer) server image."; exit 1; }

# The free server has 1 GB of memory; a swap file stops installs and busy moments from running out.
if ! swapon --show | grep -q .; then
  say "Adding 1 GB of swap"
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

if ! command -v caddy >/dev/null; then
  say "Installing Caddy (it handles https)"
  apt-get update -q
  apt-get install -y -q caddy
fi

say "Installing the course files"
id course >/dev/null 2>&1 || useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin course
mkdir -p "$DATA/backups"
chown -R course:course "$DATA"
chmod 750 "$DATA"
rm -rf "$APP.new" && mkdir -p "$APP.new"
tar -xzf "$ARCHIVE" -C "$APP.new"
[ -f "$APP.new/app/server.py" ] || { echo "That archive doesn't look like the course. Run python deploy/pack.py again."; exit 1; }
chown -R root:root "$APP.new" && chmod -R a+rX,go-w "$APP.new"
rm -rf "$APP.old"
[ -d "$APP" ] && mv "$APP" "$APP.old"
mv "$APP.new" "$APP"

NEW_SETTINGS=0
if [ ! -f "$ENVFILE" ]; then
  say "Making the settings file $ENVFILE"
  cat > "$ENVFILE" <<EOF
# Settings for Python from zero. Edit with:  sudo nano $ENVFILE
# Then apply them with:                     sudo systemctl restart $SERVICE
# This file holds secrets: never copy it anywhere public.
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
PUBLIC_URL=https://${DOMAIN:-your-domain.example.com}
OWNER_EMAIL=
ALLOWED_EMAILS=
TUTOR_DAILY_LIMIT=100
TUTOR_TOTAL_DAILY_LIMIT=2000
EOF
  chmod 600 "$ENVFILE"
  NEW_SETTINGS=1
fi

say "Setting up the service"
cat > /etc/systemd/system/$SERVICE.service <<EOF
[Unit]
Description=Python from zero course app
After=network-online.target
Wants=network-online.target

[Service]
User=course
Group=course
WorkingDirectory=$APP
EnvironmentFile=$ENVFILE
Environment=HOST=127.0.0.1 PORT=8765 COURSE_DATA_DIR=$DATA TRUST_PROXY=1 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ExecStart=/usr/bin/python3 $APP/app/server.py --no-browser
Restart=always
RestartSec=3
# Keep the app in its lane: it can only write to its data folder.
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=$DATA

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/bin/$SERVICE-backup <<EOF
#!/usr/bin/env python3
"""Copy the course database safely (even while it's in use) and keep the last 14 copies."""
import datetime, pathlib, sqlite3
data = pathlib.Path("$DATA")
if (data / "course.db").exists():
    src = sqlite3.connect(data / "course.db")
    out = sqlite3.connect(data / "backups" / f"course-{datetime.date.today()}.db")
    src.backup(out)
    out.close()
    src.close()
for old in sorted((data / "backups").glob("course-*.db"))[:-14]:
    old.unlink()
EOF
chmod 755 /usr/local/bin/$SERVICE-backup
cat > /etc/systemd/system/$SERVICE-backup.service <<EOF
[Unit]
Description=Back up the Python from zero database

[Service]
Type=oneshot
User=course
ExecStart=/usr/local/bin/$SERVICE-backup
EOF
cat > /etc/systemd/system/$SERVICE-backup.timer <<EOF
[Unit]
Description=Daily backup of the Python from zero database

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable --now $SERVICE-backup.timer >/dev/null
systemctl enable $SERVICE >/dev/null
systemctl restart $SERVICE

if [ -n "$DOMAIN" ]; then
  say "Pointing https://$DOMAIN at the app"
  cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
	encode gzip
	reverse_proxy 127.0.0.1:8765 {
		# Pass the tutor's replies through as they're written, so they stream.
		flush_interval -1
	}
}
EOF
  systemctl reload caddy || systemctl restart caddy
fi

sleep 2
say "Checking the app"
if curl -fsS http://127.0.0.1:8765/api/health; then
  echo
  echo "The app is running."
else
  echo "The app didn't answer. See what went wrong with:  sudo journalctl -u $SERVICE -n 50"
  exit 1
fi

if [ "$NEW_SETTINGS" = 1 ]; then
  cat <<EOF

Next: add your settings.
  1. sudo nano $ENVFILE
     Fill in GEMINI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and OWNER_EMAIL.
     Save with Ctrl + O then Enter, leave with Ctrl + X.
  2. sudo systemctl restart $SERVICE
EOF
fi
echo
echo "Done. Logs: sudo journalctl -u $SERVICE -f    Backups: $DATA/backups"
