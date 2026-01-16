# 📔 Reminor - Intelligent Personal Diary

> *Un diario digitale intelligente con memoria semantica e chatbot AI integrato*

Un diario personale di nuova generazione che combina scrittura tradizionale con intelligenza artificiale avanzata per comprendere e ricordare le tue esperienze.

## 🌟 Caratteristiche Principali

### 🤖 **Chatbot AI Integrato**
- Conversazioni naturali sui tuoi ricordi
- Analisi emotiva delle voci del diario  
- Risposte empatiche e personalizzate
- Powered by Groq API (Llama 3.1)

### 🧠 **Sistema di Memoria Semantica Avanzato**
- **Entity Index**: Riconoscimento automatico di nomi, luoghi e concetti
- **Ricerca Hybrid a 3 livelli**:
  1. Entity Index (veloce per nomi propri)
  2. Keyword Search (fallback robusto)  
  3. Semantic Search (TF-IDF + spaCy word vectors)
- **Date Intelligence**: Parsing intelligente di date italiane

### 🎵 **Riconoscimento Musicale Automatico**
- Rileva automaticamente la musica che stai ascoltando
- Integrazione con AudD API
- Salva le tracce nel contesto delle tue voci

### 📝 **Editor Avanzato**
- Interfaccia intuitiva con Tkinter
- Autosalvataggio intelligente
- Formattazione ricca del testo
- Gestione automatica delle date

## 🔧 Hardware Target

### Configurazione Consigliata
- **Display**: 4.2" ePaper (400x300) - WeAct Studio o compatibili
- **SBC**: Raspberry Pi Zero 2W / Orange Pi Zero 3
- **RAM**: 2GB minimo (4GB consigliato per AI)
- **Storage**: microSD 16GB+
- **Input**: Tastiera USB/Bluetooth
- **Connettività**: WiFi per setup e API AI

### Requisiti Software
- **OS**: Raspberry Pi OS / Ubuntu / Debian
- **Python**: 3.10+ 
- **Dipendenze**: Installate automaticamente dal setup

## 🚀 Installazione Rapida

### Metodo 1: Script Automatico (Consigliato)
```bash
# Clone del repository
git clone https://github.com/cristal-orion/Reminor-4.2.git
cd Reminor-4.2

# Installazione e avvio automatico
chmod +x run_reminor.sh
./run_reminor.sh
```

Lo script `run_reminor.sh` gestisce automaticamente:
- ✅ Creazione ambiente virtuale Python
- ✅ Installazione dipendenze da requirements.txt
- ✅ Download modello spaCy italiano (it_core_news_sm)
- ✅ Verifica configurazione .env
- ✅ Avvio applicazione

### Metodo 2: Installazione Manuale
```bash
# Preparazione sistema
sudo apt update && sudo apt install python3 python3-pip python3-tk python3-venv

# Setup progetto
git clone https://github.com/cristal-orion/Reminor-4.2.git
cd Reminor-4.2

# Ambiente virtuale
python3 -m venv venv
source venv/bin/activate

# Dipendenze
pip install -r requirements.txt
python -m spacy download it_core_news_sm

# Configurazione
cp .env.template .env
# Modifica .env con la tua GROQ_API_KEY

# Avvio
python reminor.py
```

### Metodo 3: Installazione come Pacchetto
```bash
# Installazione sistema con setup.py
git clone https://github.com/cristal-orion/Reminor-4.2.git
cd Reminor-4.2
pip install .

# Avvio da qualsiasi directory
reminor
```

## ⚙️ Configurazione API

### Groq API (Richiesta)
1. Registrati su [Groq Console](https://console.groq.com/keys)
2. Genera una API key gratuita
3. Aggiungi al file `.env`:
```bash
GROQ_API_KEY=gsk_your_api_key_here
```

### Modelli AI Supportati
- **DeepSeek R1** (default) - Ragionamento avanzato
- **Llama 3.3** - Conversazione naturale
- **Qwen** - Analisi multilingue

## 🎮 Utilizzo

### Controlli Principali
```
↑↓     Navigazione menu / Scorrimento testo
←→     Navigazione calendario / Modifica impostazioni  
ENTER  Conferma selezione
ESC    Torna al menu principale
CTRL+S Salva diario
F2     Toggle emozioni (editor) / Ragionamento AI (chat)
```

### Funzioni Principali
- **📝 Nuova Pagina**: Editor giornaliero con salvataggio automatico
- **📅 Calendario**: Visualizza e naviga tra le voci passate
- **🔍 Ricerca**: Trova testo in tutto il diario
- **🤖 Chat Pensieri**: Parla con AI che conosce il tuo diario
- **📊 Emozioni**: Grafici settimanali delle emozioni rilevate
- **⚙️ Impostazioni**: Personalizza tema, font e backup

### Chat AI Avanzata
- **Contesto Automatico**: Analizza ultime 15 voci del diario
- **Memoria Conversazione**: Mantiene continuità del dialogo  
- **Supporto Emotivo**: Risposte empatiche e personalizzate
- **Ragionamento Visibile**: F2 per vedere il processo di pensiero AI

## 📊 Analisi Emozioni

### Emozioni Monitorate
- **Positive**: Felice, Sereno, Grato, Motivato
- **Negative**: Triste, Arrabbiato, Ansioso, Stressato

### Visualizzazioni
- 📈 **Matrice Settimanale**: Griglia giorni × emozioni
- 📊 **Barre Progresso**: Intensità 0-100% per emozione
- 📅 **Navigazione Temporale**: Scorri settimane precedenti

## 💾 Struttura Dati

```
~/.mysoul_journal/
├── YYYY-MM-DD.txt           # Voci diario quotidiane
├── YYYY-MM-DD_emotions.json # Analisi emozioni giornaliere  
├── settings.json            # Configurazioni utente
├── emotions_cache.json      # Cache analisi AI (performance)
└── memory_graph.gpickle     # Grafo memoria strutturata
```

## 🔒 Privacy e Sicurezza

- **🏠 Dati Locali**: Il diario rimane completamente sul dispositivo
- **🔐 API Key Privata**: Salvata solo localmente, mai trasmessa
- **🤐 Zero Telemetria**: Nessun tracking o raccolta dati
- **🧠 AI Minimale**: Solo testo del diario inviato per analisi (encrypted HTTPS)
- **💾 Backup Opzionale**: Google Drive solo se esplicitamente abilitato

## ⚡ Performance per Embedded

### Ottimizzazioni
- **🚀 Avvio Rapido**: <5 secondi su RPi Zero 2W
- **💾 Memoria Efficiente**: <150MB RAM utilizzata
- **🔋 Basso Consumo**: Modalità risparmio ePaper
- **📱 UI Responsive**: 400x300 pixel ottimizzati
- **💨 Cache Intelligente**: Riduce chiamate API

### Compatibilità Hardware
- ✅ **Raspberry Pi**: Zero 2W, 3B+, 4B, 5
- ✅ **Orange Pi**: Zero 2, Zero 3  
- ✅ **Rock Pi**: S, 4SE
- ✅ **Display**: ePaper 4.2", LCD, HDMI

## 🔧 Risoluzione Problemi

### Errori Comuni
```bash
# Modello spaCy mancante
python -m spacy download it_core_news_sm

# Tkinter non trovato (Ubuntu/Debian)
sudo apt install python3-tk

# Font rendering issues
sudo apt install fonts-dejavu

# API timeout issues
export GROQ_TIMEOUT=30
```

### Debug Mode
```bash
# Avvio con debug completo
python reminor.py --debug

# Test configurazione
python -c "import reminor; print('OK')"
```

## 🛣️ Roadmap

### v1.1 (Prossima Release)
- [ ] **Companion App Mobile**: Setup via smartphone BLE
- [ ] **Backup Multi-Cloud**: Dropbox, iCloud, OneDrive  
- [ ] **Plugin Audio**: Dettatura vocale con Whisper
- [ ] **Sensori Ambientali**: Temperatura, umidità, pressione

### v1.2 (Future)
- [ ] **Multiutente**: Profili separati e privacy
- [ ] **AI Locale**: Ollama integration per offline mode
- [ ] **Themes Avanzati**: Personalizzazione completa UI
- [ ] **API REST**: Integrazione con app esterne

### Hardware Future
- [ ] **Touch Support**: Display touch capacitivi
- [ ] **E-Ink Color**: Display ePaper a colori
- [ ] **IoT Integration**: Home Assistant, MQTT
- [ ] **Wearable Sync**: Smartwatch, fitness tracker

## 📄 Tecnologie

### Core
- **Python 3.10+**: Linguaggio principale
- **Tkinter**: UI desktop cross-platform
- **spaCy**: Natural Language Processing
- **NetworkX**: Grafici di memoria strutturata

### AI/ML
- **Groq API**: LLM cloud ad alte prestazioni  
- **DeepSeek R1**: Modello di ragionamento avanzato
- **spaCy it_core_news_sm**: Modello italiano NER

### Deploy
- **setuptools**: Packaging e distribuzione
- **venv**: Ambienti virtuali isolati
- **bash**: Script automazione Linux

## 🤝 Contribuire

### Aree di Sviluppo
- **🔌 Hardware**: Supporto nuovi display e SBC
- **🤖 AI**: Provider alternativi (OpenAI, Anthropic, locale)
- **🌍 Localizzazione**: Traduzioni (inglese, francese, spagnolo)
- **♿ Accessibilità**: Screen reader, alto contrasto
- **📱 Mobile**: App companion iOS/Android

### Setup Sviluppo
```bash
git clone https://github.com/cristal-orion/Reminor-4.2.git
cd Reminor-4.2
python -m venv venv
source venv/bin/activate
pip install -e .
pip install pytest black flake8  # Dev tools
```

## 📄 Licenza

MIT License - Vedi [LICENSE](LICENSE) per dettagli completi.

## 🙏 Ringraziamenti

- **Groq**: API AI gratuita e veloce
- **spaCy**: Eccellente NLP per italiano  
- **Raspberry Pi Foundation**: Hardware accessibile
- **Python Community**: Ecosistema ricco e stabile

---

**Reminor** - *Il tuo compagno di riflessione digitale con AI* 🤖✨

*Progettato per la contemplazione, ottimizzato per l'embedded, potenziato dall'intelligenza artificiale.*
