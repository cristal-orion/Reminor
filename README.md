# Reminor

Diario personale con AI, analisi emotiva e memoria semantica.

## Architettura

```
├── backend/              # FastAPI REST API
├── reminor-frontend/     # Svelte 5 SPA
├── docker-compose.yml    # Deploy sviluppo
├── docker-compose.prod.yml # Deploy produzione con Caddy + SSL
```

## Funzionalità

- **Diario** - Scrivi e naviga le pagine del diario con calendario
- **Chat AI** - Conversa con un assistente che conosce il tuo diario
- **Analisi Emozioni** - 8 emozioni analizzate automaticamente con LLM
- **Ricerca Semantica** - Trova ricordi per significato, non solo parole chiave
- **Statistiche** - Streak, volume scrittura, trend emotivi
- **Knowledge Base** - Estrazione automatica di informazioni personali
- **Backup/Export** - Download completo in formato ZIP
- **Autenticazione** - JWT con registrazione e login

## Quick Start

### Requisiti
- Python 3.11+
- Node.js 18+
- Docker (opzionale)

### Sviluppo locale

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd backend && uvicorn api.main:app --reload --port 8001

# Frontend (nuovo terminale)
cd reminor-frontend
npm install
npm run dev
```

Apri http://localhost:5173

### Docker (Sviluppo)

```bash
docker compose up --build
```

Apri http://localhost

### Docker (Produzione con SSL)

Per deploy su server con dominio e certificato SSL automatico:

```bash
# Modifica il dominio in Caddyfile
# Crea .env.production con JWT_SECRET_KEY

docker compose -f docker-compose.prod.yml up --build -d
```

Caddy gestisce automaticamente i certificati Let's Encrypt.

## Configurazione LLM

L'API key per il modello LLM si configura **dall'interfaccia** dell'app:

1. Vai in **Impostazioni** (icona ingranaggio)
2. Clicca su **Configura LLM**
3. Seleziona il provider (Groq, OpenAI, Anthropic, Gemini, Mistral, DeepSeek)
4. Inserisci la tua API key
5. Salva

La chiave viene salvata localmente nel browser e usata per:
- Chat AI
- Analisi delle emozioni

### Provider supportati

| Provider | Modelli esempio | API Key |
|----------|-----------------|---------|
| Groq | llama-3.3-70b-versatile | [console.groq.com](https://console.groq.com) |
| OpenAI | gpt-4o, gpt-4o-mini | [platform.openai.com](https://platform.openai.com) |
| Anthropic | claude-3-5-sonnet | [console.anthropic.com](https://console.anthropic.com) |
| Google | gemini-2.0-flash | [aistudio.google.com](https://aistudio.google.com) |
| Mistral | mistral-large-latest | [console.mistral.ai](https://console.mistral.ai) |
| DeepSeek | deepseek-chat | [platform.deepseek.com](https://platform.deepseek.com) |

## Variabili d'ambiente (opzionali)

```env
# Backend
JWT_SECRET_KEY=your-secret-key    # Per autenticazione (obbligatorio in prod)
DATA_DIR=./data                    # Directory dati utenti
```

## API Endpoints

### Autenticazione
| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/auth/register` | POST | Registrazione utente |
| `/auth/login` | POST | Login (ritorna JWT) |
| `/auth/me` | GET | Info utente corrente |
| `/auth/refresh` | POST | Rinnova token |

### Diario
| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/journal/entries` | GET | Lista pagine diario |
| `/journal/entries` | POST | Salva pagina |
| `/journal/entries/{date}` | GET | Legge pagina specifica |
| `/journal/entries/{date}/analyze` | POST | Analizza emozioni (richiede LLM config nel body) |
| `/journal/entries/{date}/emotions` | GET | Recupera emozioni salvate |
| `/journal/search` | POST | Ricerca semantica |
| `/journal/stats` | GET | Statistiche utente |
| `/journal/backup/zip` | GET | Download backup |

### Chat
| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/chat` | POST | Messaggio chat AI (richiede LLM config nel body) |
| `/health` | GET | Health check |

## Tech Stack

**Backend**
- FastAPI + Uvicorn
- LiteLLM (multi-provider: Groq, OpenAI, Anthropic, Gemini, Mistral, DeepSeek)
- Sentence-Transformers per embeddings
- Memvid per memoria video-based
- JWT per autenticazione
- bcrypt per password hashing

**Frontend**
- Svelte 5
- Vite

**Deploy**
- Docker + docker-compose
- Caddy (reverse proxy + SSL automatico Let's Encrypt)
- nginx (solo sviluppo)

## Struttura Dati

```
data/
├── users.json                      # Database utenti
└── {user_id}/
    ├── journal/
    │   └── YYYY-MM-DD.txt          # Pagine diario
    ├── emotions.json               # Emozioni analizzate
    ├── memory.mv2                  # Memoria semantica (memvid)
    └── user_knowledge.json         # Knowledge base estratta
```

## Licenza

MIT
