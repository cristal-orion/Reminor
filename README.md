# Reminor

Un diario personale potenziato dall'intelligenza artificiale. Scrivi i tuoi pensieri, e Reminor li analizza, li ricorda e ci conversa con te.

**[Prova la demo live](https://app.reminor.it)**

## Cosa fa

Reminor non e' un semplice diario. Ogni volta che scrivi, il sistema:

- **Analizza le tue emozioni** - 8 dimensioni emotive tracciate nel tempo
- **Costruisce una memoria semantica** - ricerca per significato, non solo parole chiave
- **Parla con te** - una chat AI che conosce il tuo diario e il tuo contesto
- **Mostra i tuoi trend** - statistiche, streak di scrittura, evoluzione emotiva

Supporta italiano e inglese.

## Come provarlo

1. Vai su **[app.reminor.it](https://app.reminor.it)** e crea un account
2. Vai in **Impostazioni** > **Configura LLM** e inserisci una API key (vedi [provider supportati](#provider-supportati))
3. Scrivi la tua prima pagina di diario e clicca **Analizza emozioni**

Senza API key puoi scrivere e navigare il diario, ma la chat AI e l'analisi emotiva non funzioneranno.

## Provider supportati

L'AI non e' inclusa: porti la tua API key. Questi i provider supportati:

| Provider | Modelli consigliati | Dove prendere la key |
|----------|-------------------|----------------------|
| Groq | llama-3.3-70b-versatile | [console.groq.com](https://console.groq.com) |
| Google | gemini-2.0-flash | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | gpt-4o-mini | [platform.openai.com](https://platform.openai.com) |
| Anthropic | claude-3-5-sonnet | [console.anthropic.com](https://console.anthropic.com) |
| Mistral | mistral-large-latest | [console.mistral.ai](https://console.mistral.ai) |
| DeepSeek | deepseek-chat | [platform.deepseek.com](https://platform.deepseek.com) |

**Groq** e **Google** offrono piani gratuiti sufficienti per uso personale.

La chiave viene criptata server-side (Fernet encryption) e associata al tuo account.

## Self-hosting

Vuoi installarlo sul tuo server? Serve solo Docker.

### Deploy rapido (produzione con SSL)

```bash
git clone https://github.com/cristal-orion/Reminor.git
cd Reminor

# Configura
cp .env.production.template .env.production
# Modifica .env.production: imposta JWT_SECRET_KEY e HF_TOKEN
# Modifica Caddyfile: sostituisci app.reminor.it con il tuo dominio

# Avvia
docker compose -f docker-compose.prod.yml up --build -d
```

Caddy gestisce automaticamente i certificati SSL con Let's Encrypt.

### Variabili d'ambiente

```env
# Obbligatorio
JWT_SECRET_KEY=...   # python -c "import secrets; print(secrets.token_hex(32))"

# Per il modello di embeddings (ricerca semantica)
HF_TOKEN=...         # Token da huggingface.co/settings/tokens
                     # Richiede accesso a google/embeddinggemma-300m
```

### Deploy sviluppo (locale)

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd backend && uvicorn api.main:app --reload --port 8000

# Frontend (altro terminale)
cd reminor-frontend && npm install && npm run dev
```

Apri http://localhost:5173

---

## Architettura

```
Browser (Svelte 5)
    |
    v
  Caddy (SSL + reverse proxy)
    |
    v
  FastAPI (backend)
    |
    +-- LiteLLM (chat, analisi emozioni)
    +-- Sentence-Transformers (embeddings locali)
    +-- Memvid (memoria semantica)
```

### Tech stack

| Layer | Tecnologia |
|-------|-----------|
| Frontend | Svelte 5, Vite |
| Backend | FastAPI, Uvicorn, Python 3.11 |
| AI | LiteLLM (multi-provider), Sentence-Transformers, Memvid |
| Auth | JWT + bcrypt + Fernet (encryption API keys) |
| Deploy | Docker, Caddy (SSL automatico) |

### Struttura dati

```
data/
+-- users.json                    # Database utenti (password bcrypt, LLM config criptata)
+-- {user_id}/
    +-- journal/
    |   +-- YYYY-MM-DD.txt        # Pagine diario (plain text)
    +-- emotions.json             # Emozioni analizzate
    +-- memory.mv2                # Memoria semantica (memvid)
    +-- memory.npz                # Embeddings (sentence-transformers)
```

### API

<details>
<summary>Endpoints principali</summary>

**Autenticazione**
| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/auth/register` | POST | Registrazione |
| `/auth/login` | POST | Login (ritorna JWT) |
| `/auth/me` | GET | Info utente |
| `/auth/settings/llm` | PUT | Salva configurazione LLM |
| `/auth/settings/language` | PUT | Cambia lingua (it/en) |

**Diario**
| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/journal/entries` | GET | Lista pagine |
| `/journal/entries` | POST | Salva pagina |
| `/journal/entries/{date}` | GET | Legge pagina |
| `/journal/entries/{date}/analyze` | POST | Analizza emozioni |
| `/journal/entries/{date}/emotions` | GET | Emozioni salvate |
| `/journal/search` | POST | Ricerca semantica |
| `/journal/stats` | GET | Statistiche |
| `/journal/backup/zip` | GET | Download backup |
| `/journal/rebuild-vectors` | POST | Ricostruisce indice semantico |

**Chat**
| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/chat` | POST | Messaggio chat AI |
| `/health` | GET | Health check |

</details>

## Licenza

MIT
