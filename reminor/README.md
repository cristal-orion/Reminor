# 🌟 Reminor - Il Tuo Diario Digitale Intelligente (Windows)

> *Un diario personale con AI che comprende davvero i tuoi pensieri*

## 🚀 Avvio Rapido - Windows

```cmd
start_reminor.bat
```

> **Per Linux/ARM**: Usa la distribuzione separata `Reminor-OrangePi-Distribution`

## ✨ Caratteristiche

### 📝 **Editor Integrato**
- Scrivi direttamente nel terminale
- Salvataggio automatico con data
- Navigazione con calendario visivo

### 🧠 **AI Intelligente** 
- **Ricerca semantica**: Trova le pagine più rilevanti usando spaCy
- **Contesto personalizzato**: L'AI sa cosa hai scritto
- **Risparmio token**: Solo le pagine pertinenti alla tua domanda
- **Analisi emozioni**: Comprende i tuoi stati d'animo

### 📅 **Calendario Interattivo**
- Visualizza i giorni con pagine scritte
- Navigazione veloce tra le date
- Apertura diretta delle pagine esistenti

### 🎨 **Interfaccia TUI Professionale**
- Bubble Tea per un'esperienza fluida
- Navigazione intuitiva con frecce
- Design pulito e responsive

## 🛠️ Tecnologie

- **Frontend**: Go + Bubble Tea (Terminal UI)
- **Backend**: Python + Flask (API REST)
- **NLP**: spaCy + modello italiano `it_core_news_md`
- **AI**: Groq API (DeepSeek-R1-Distill-Llama-70B)
- **Database**: File system + vettorizzazione semantica

## 📦 Contenuto Cartella Windows

```
reminor/
├── 🚀 AVVIO WINDOWS
│   ├── start_reminor.bat      # Avvio Windows
│   └── stop_reminor.bat       # Stop Windows
│
├── 🦫 INTERFACCIA GO
│   ├── bubblereminor.go       # Menu principale TUI
│   ├── calendar.go            # Calendario interattivo
│   ├── chat.go                # Chat AI semantica
│   ├── pager.go               # Editor pagine
│   └── go.mod                 # Dipendenze Go
│
├── 🐍 BACKEND PYTHON
│   ├── memory_server.py       # Server API REST
│   ├── enhanced_structured_memory.py
│   ├── enhanced_emotions_analyzer.py
│   └── structured_memory.py
│
└── 📖 DOCUMENTAZIONE
    ├── README.md              # Questa guida
    └── README_SETUP.md        # Setup Windows dettagliato
```

## 🔧 Requisiti Windows

- **Python 3.8+** (con pip)
- **Go 1.21+** 
- **GROQ API Key** (gratuita)
- **4GB+ RAM** raccomandato per spaCy
- **Windows 10/11** (x64)

## ⚙️ Configurazione Windows

1. **Ottieni GROQ API Key**: [console.groq.com](https://console.groq.com/)
2. **Modifica `.env`** nella directory padre:
   ```
   GROQ_API_KEY=la_tua_chiave_qui
   ```
3. **Esegui**: `start_reminor.bat`
4. **Prima volta**: Attendi download modello spaCy (~150MB)

## 💡 Come Funziona l'AI

### 🔍 **Ricerca Semantica**
1. Scrivi nel diario ogni giorno
2. spaCy analizza e vettorizza il contenuto
3. Quando fai una domanda, trova le pagine più simili
4. Solo quelle vengono inviate all'AI

### Esempio:
- **Tu scrivi**: "Oggi sono andato al mare con Maria"
- **Domandi**: "Com'è andata la gita?"
- **AI trova**: La pagina del mare automaticamente
- **Risposta**: Contestuale e personalizzata!

## 🎯 Vantaggi

- **🔒 Privacy**: Tutto in locale, niente cloud
- **💰 Economico**: Usa meno token AI grazie al contesto mirato
- **🧠 Intelligente**: Ricorda meglio di te cosa hai scritto
- **⚡ Veloce**: Interface TUI molto responsive
- **🪟 Windows**: Ottimizzato per Windows 10/11

## 🚨 Risoluzione Problemi Windows

### Chat non funziona
- Controlla che `.env` contenga la GROQ_API_KEY
- Verifica connessione internet
- Assicurati che il server Python sia attivo (porta 8080)

### spaCy non si carica
- Prima installazione richiede download modello (150MB)
- Serve 4GB+ RAM per performance ottimali
- Controlla spazio disco (modello richiede ~500MB)

### "Python not found"
- Installa Python da [python.org](https://python.org)
- Assicurati che sia nel PATH di sistema

### "Go not found"  
- Installa Go da [golang.org](https://golang.org)
- Riavvia il terminale dopo installazione

## 🤝 Supporto

Per problemi o suggerimenti:
1. Controlla `README_SETUP.md` per setup dettagliato Windows
2. Verifica i log del server Python nel terminale
3. Usa `stop_reminor.bat` per reset completo

## 🎉 Buon Diario!

Reminor ti aiuta a riflettere meglio sui tuoi pensieri grazie all'AI che comprende davvero quello che scrivi. 

**Inizia oggi il tuo viaggio di crescita personale!** ✨

---

*Made with ❤️ using Go, Python, and a lot of semantic magic* 🪄