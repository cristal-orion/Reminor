# Reminor

Diario personale con AI, analisi emotiva e memoria semantica.

## Architettura

```
├── backend/              # FastAPI REST API
├── reminor-frontend/     # Svelte 5 SPA
├── docker-compose.yml    # Deploy con Docker
```

## Funzionalità

- **Diario** - Scrivi e naviga le pagine del diario con calendario
- **Chat AI** - Conversa con un assistente che conosce il tuo diario
- **Analisi Emozioni** - 8 emozioni analizzate automaticamente per ogni pagina
- **Ricerca Semantica** - Trova ricordi per significato, non solo parole chiave
- **Statistiche** - Streak, volume scrittura, trend emotivi
- **Knowledge Base** - Estrazione automatica di informazioni personali
- **Backup/Export** - Download completo in formato ZIP

## Quick Start

### Requisiti
- Python 3.11+
- Node.js 18+
- API key Groq (gratuita su [console.groq.com](https://console.groq.com))

### Sviluppo locale

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env     # Aggiungi GROQ_API_KEY
cd backend && uvicorn api.main:app --reload --port 8001

# Frontend (nuovo terminale)
cd reminor-frontend
npm install
npm run dev
```

Apri http://localhost:5173

### Docker

```bash
cp .env.template .env  # Aggiungi GROQ_API_KEY
docker-compose up --build
```

Apri http://localhost

## Configurazione

Crea `.env` nella root:

```env
GROQ_API_KEY=gsk_your_key_here
DATA_DIR=./data
```

### LLM Provider

Nelle impostazioni dell'app puoi configurare:
- **Provider**: Groq, OpenAI, Anthropic, Google Gemini, Mistral, DeepSeek
- **Modello**: Selezionabile per ogni provider
- **API Key**: Salvata localmente nel browser

## API Endpoints

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/journal/{user}/entries` | GET/POST | Lista/salva pagine diario |
| `/journal/{user}/entries/{date}` | GET | Legge pagina specifica |
| `/journal/{user}/entries/{date}/analyze` | POST | Analizza emozioni |
| `/journal/{user}/search` | POST | Ricerca semantica |
| `/journal/{user}/stats` | GET | Statistiche utente |
| `/journal/{user}/backup/zip` | GET | Download backup |
| `/chat/{user}` | POST | Messaggio chat AI |
| `/health` | GET | Health check |

## Tech Stack

**Backend**
- FastAPI + Uvicorn
- Sentence-BERT (italiano) per embeddings
- Memvid per memoria video-based
- LiteLLM per multi-provider LLM

**Frontend**
- Svelte 5
- Tailwind CSS
- Vite

**Deploy**
- Docker + docker-compose
- nginx (reverse proxy)

## Struttura Dati

```
data/{user_id}/
├── journal/
│   ├── YYYY-MM-DD.txt           # Pagine diario
│   └── YYYY-MM-DD_emotions.json # Cache emozioni
├── memory.mv2                   # Memoria semantica (memvid)
├── memory_embeddings.npz        # Embeddings
└── knowledge_base.json          # Informazioni estratte
```

## Licenza

MIT
