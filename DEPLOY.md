# Deployment Reminor su VPS

## Prerequisiti
- VPS con Debian/Ubuntu
- Docker e Docker Compose installati
- Dominio puntato all'IP della VPS (es. `app.reminor.it`)
- Porte 80 e 443 aperte nel firewall

## Quick Start

### 1. Clona il repository sulla VPS

```bash
ssh user@tua-vps-ip
git clone https://github.com/TUO-USERNAME/Reminor-4.2-main.git
cd Reminor-4.2-main
```

### 2. Configura le variabili d'ambiente

```bash
# Copia il template
cp .env.production.template .env.production

# Genera una chiave JWT sicura
openssl rand -hex 32

# Modifica il file con la chiave generata
nano .env.production
```

Esempio `.env.production`:
```env
JWT_SECRET_KEY=la-tua-chiave-generata-con-openssl
GROQ_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

### 3. Configura il dominio nel Caddyfile

```bash
nano Caddyfile
```

Sostituisci `app.reminor.it` con il tuo dominio.

### 4. Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

Oppure manualmente:
```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Verifica

```bash
# Controlla che i container siano attivi
docker-compose -f docker-compose.prod.yml ps

# Controlla i log
docker-compose -f docker-compose.prod.yml logs -f
```

Visita `https://app.reminor.it` - Caddy genererà automaticamente il certificato SSL.

---

## Comandi Utili

### Visualizza log
```bash
docker-compose -f docker-compose.prod.yml logs -f
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs caddy
```

### Riavvia servizi
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Aggiorna dopo modifiche al codice
```bash
git pull
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Backup dati
```bash
# I dati sono nel volume Docker 'reminor_data'
docker run --rm -v reminor_data:/data -v $(pwd):/backup alpine tar cvf /backup/reminor_backup.tar /data
```

### Ripristino backup
```bash
docker run --rm -v reminor_data:/data -v $(pwd):/backup alpine tar xvf /backup/reminor_backup.tar -C /
```

---

## Architettura

```
Internet
    │
    ▼
┌─────────────────┐
│   Caddy:443     │  ← SSL automatico Let's Encrypt
│   (reverse      │
│    proxy)       │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌──────────┐
│Frontend│  │ Backend  │
│ /srv/  │  │ :8000    │
│frontend│  │ FastAPI  │
└───────┘  └──────────┘
                │
                ▼
           ┌─────────┐
           │  Data   │
           │ Volume  │
           └─────────┘
```

---

## Troubleshooting

### Certificato SSL non funziona
- Verifica che il dominio punti all'IP corretto: `dig app.reminor.it`
- Verifica che le porte 80/443 siano aperte: `sudo ufw allow 80,443/tcp`
- Controlla i log di Caddy: `docker-compose -f docker-compose.prod.yml logs caddy`

### Backend non risponde
- Controlla i log: `docker-compose -f docker-compose.prod.yml logs backend`
- Verifica che JWT_SECRET_KEY sia configurato in `.env.production`

### Container non partono
- Verifica spazio disco: `df -h`
- Verifica memoria: `free -m`
- Ricostruisci: `docker-compose -f docker-compose.prod.yml build --no-cache`
