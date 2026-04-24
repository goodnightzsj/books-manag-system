# Bare-metal (systemd) deployment

Templates for Ubuntu / CentOS / Debian hosts.

## Layout assumed

- Source:   `/opt/books-manag-system/`
- Venv:     `/opt/books-manag-system/venv/`
- Env file: `/etc/books/books.env` (see `books.env.example`)
- Data:     `/var/lib/books/{books,uploads}`
- User:     `books:books`

## Steps

```bash
sudo useradd --system --home /var/lib/books --shell /usr/sbin/nologin books
sudo mkdir -p /opt/books-manag-system /var/lib/books/books /var/lib/books/uploads /etc/books
sudo chown -R books:books /opt/books-manag-system /var/lib/books

# deploy code
sudo -u books git clone https://example/books-manag-system.git /opt/books-manag-system
sudo -u books python3.11 -m venv /opt/books-manag-system/venv
sudo -u books /opt/books-manag-system/venv/bin/pip install -r /opt/books-manag-system/backend/requirements.txt

# env + migrations
sudo cp books.env.example /etc/books/books.env && sudo chmod 0640 /etc/books/books.env
sudo -u books bash -c 'cd /opt/books-manag-system/backend && /opt/books-manag-system/venv/bin/alembic upgrade head'

# systemd units
sudo cp books-api.service books-worker.service books-beat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now books-api books-worker books-beat
```

## Ports

- API listens on `127.0.0.1:8000`; front it with nginx (see `../nginx/` templates).
