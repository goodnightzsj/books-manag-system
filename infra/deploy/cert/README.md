# TLS bootstrapping for `books.9962510.xyz`

Pick **one** of the three paths.

---

## Option A · Caddy (one-shot, recommended for fresh VPS)

```bash
# DNS first: A record books.9962510.xyz -> your-vps-ip (TTL 300)
cp .env.example .env  # set SECRET_KEY / ADMIN_PASSWORD / etc.
docker compose -f docker-compose.yml \
               -f infra/deploy/caddy/docker-compose.caddy.yml \
               up -d
```

Caddy obtains certs on first boot via HTTP-01 and renews automatically.
The default `nginx` service is disabled by the overlay's profile flag.

---

## Option B · Nginx + Certbot (more control, requires bootstrap)

```bash
# 1. DNS first: books.9962510.xyz -> this host
# 2. start with bootstrap config (HTTP only)
mv infra/docker/nginx/conf.d/api.conf infra/docker/nginx/conf.d/api.conf.disabled
cp infra/docker/nginx/conf.d/bootstrap.conf.example \
   infra/docker/nginx/conf.d/bootstrap.conf
mkdir -p infra/docker/nginx/certbot-www
docker compose up -d nginx api admin-web reader-web

# 3. issue cert (one-shot)
docker run --rm \
  -v "$(pwd)/infra/docker/nginx/certbot-www:/var/www/certbot" \
  -v "$(pwd)/infra/docker/nginx/certs:/etc/letsencrypt" \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d books.9962510.xyz \
  --email YOU@example.com --agree-tos --no-eff-email -n

# 4. swap configs back
mv infra/docker/nginx/conf.d/api.conf.disabled \
   infra/docker/nginx/conf.d/api.conf
rm infra/docker/nginx/conf.d/bootstrap.conf
docker compose exec nginx nginx -s reload
```

The api.conf already references `/etc/nginx/certs/books.9962510.xyz/`
so mount the certbot-issued tree there in compose:

```yaml
nginx:
  volumes:
    - ./infra/docker/nginx/certs/live/books.9962510.xyz:/etc/nginx/certs/books.9962510.xyz:ro
    - ./infra/docker/nginx/certbot-www:/var/www/certbot:ro
```

Renewal (cron):

```cron
17 3 * * * cd /opt/books && docker run --rm \
  -v "$PWD/infra/docker/nginx/certbot-www:/var/www/certbot" \
  -v "$PWD/infra/docker/nginx/certs:/etc/letsencrypt" \
  certbot/certbot renew --quiet \
  && docker compose exec -T nginx nginx -s reload
```

---

## Option C · Cloudflare proxy (no cert work locally)

DNS proxied (orange cloud) → Cloudflare terminates TLS → origin uses
plain HTTP on :80 (or HTTP via the optional Cloudflare Origin cert).

In this mode keep nginx serving HTTP only -- swap `api.conf` for
`bootstrap.conf` permanently and let Cloudflare front it.

Set Cloudflare SSL/TLS to **Full (strict)** if you also keep an origin
cert, or **Flexible** for the simplest path (less secure).

---

## Sanity checks

```bash
# 1. cert chain
openssl s_client -connect books.9962510.xyz:443 -servername books.9962510.xyz </dev/null 2>/dev/null \
  | openssl x509 -noout -dates -subject -issuer

# 2. HSTS / headers
curl -sI https://books.9962510.xyz/health | grep -iE "strict-transport|content-type|x-frame"

# 3. API smoke
curl -s https://books.9962510.xyz/health
```
