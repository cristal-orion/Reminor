# Privacy Policy - Reminor

**Ultimo aggiornamento:** 5 Febbraio 2026

## 1. Introduzione

Questa Privacy Policy descrive come **Reminor** raccoglie, utilizza, conserva e protegge i tuoi dati personali quando utilizzi il nostro servizio di diario personale potenziato dall'intelligenza artificiale, disponibile all'indirizzo [app.reminor.it](https://app.reminor.it).

Reminor è progettato con la **privacy by design**: i tuoi dati sono isolati, criptati quando necessario, e mai utilizzati per scopi commerciali o pubblicitari.

**Titolare del trattamento:**  
Affinity Srl  
Via Lanzara 33, 80014 Nocera Inferiore (SA)  
P.IVA: 06221050658  
Email: info@affinitylab.it

## 2. Dati che raccogliamo

### 2.1 Dati account
- **Email**: utilizzata per l'autenticazione e comunicazioni di servizio
- **Nome** (opzionale): per personalizzare l'esperienza
- **Lingua preferita** (italiano/inglese): per adattare l'interfaccia
- **Password**: memorizzata in forma hash (bcrypt)
- **Data di creazione account**

### 2.2 Dati diario
- **Contenuto delle pagine di diario**: testo inserito dall'utente
- **Date delle voci**: associati ai contenuti del diario
- **Analisi emotiva**: punteggi su 8 dimensioni emotive (felice, triste, arrabbiato, ansioso, sereno, stressato, grato, motivato)
- **Insight giornalieri**: analisi generate dall'AI sul contenuto
- **Knowledge base**: informazioni estratte automaticamente dal diario per personalizzare la chat

### 2.3 Dati tecnici e di utilizzo
- **Statistiche di scrittura**: numero di parole, streak giornalieri, frequenza di scrittura
- **Log di accesso**: timestamp delle operazioni (esclusivamente per fini di sicurezza)

### 2.4 API Key (opzionale)
- **API key dei provider LLM**: se configurate, vengono memorizzate in forma criptata (Fernet encryption)
- **Provider e modello preferito**: configurazione LLM scelta dall'utente

## 3. Come utilizziamo i dati

| Dato | Finalità | Base giuridica |
|------|----------|----------------|
| Email, password | Autenticazione e sicurezza account | Esecuzione del contratto (Art. 6(1)(b) GDPR) |
| Contenuto diario | Fornire il servizio di journaling | Esecuzione del contratto (Art. 6(1)(b) GDPR) |
| Analisi emotiva | Funzionalità di analisi e statistiche | Consenso esplicito (Art. 6(1)(a) GDPR) |
| API key | Connessione ai servizi LLM scelti dall'utente | Esecuzione del contratto (Art. 6(1)(b) GDPR) |
| Knowledge base | Personalizzazione delle risposte AI | Interesse legittimo (Art. 6(1)(f) GDPR) - migliorare il servizio |

**Nota importante**: L'analisi emotiva e la chat AI richiedono l'invio del contenuto del diario ai provider LLM scelti dall'utente. Questo avviene **solo su richiesta esplicita** dell'utente e utilizzando la API key fornita dall'utente stesso.

## 4. Conservazione dei dati

### 4.1 Durata
- **Dati account**: conservati fino alla richiesta di cancellazione dell'account
- **Contenuto diario**: conservato fino alla cancellazione esplicita da parte dell'utente
- **API key**: conservate fino alla rimozione da parte dell'utente
- **Log di sicurezza**: massimo 90 giorni

### 4.2 Cancellazione
- L'utente può richiedere la cancellazione completa di tutti i dati scrivendo a welcome@reminor.it o info@affinitylab.it
- I dati vengono rimossi entro 30 giorni dalla richiesta
- I backup vengono eliminati secondo i cicli di retention automatici

## 5. Condivisione con terzi

### 5.1 Provider LLM (servizi AI)
I seguenti dati vengono condivisi **solo quando l'utente utilizza le funzionalità AI** (analisi emotiva o chat):

| Provider | Dati condivisi | Paese | Privacy Policy |
|----------|---------------|-------|----------------|
| Groq | Contenuto diario, messaggi chat | USA | [groq.com/privacy](https://groq.com/privacy) |
| OpenAI | Contenuto diario, messaggi chat | USA | [openai.com/privacy](https://openai.com/privacy) |
| Anthropic | Contenuto diario, messaggi chat | USA | [anthropic.com/privacy](https://anthropic.com/privacy) |
| Google (Gemini) | Contenuto diario, messaggi chat | USA | [policies.google.com/privacy](https://policies.google.com/privacy) |
| Mistral | Contenuto diario, messaggi chat | Francia | [mistral.ai/privacy](https://mistral.ai/privacy) |
| DeepSeek | Contenuto diario, messaggi chat | Cina | [deepseek.com/privacy](https://deepseek.com/privacy) |

**Importante**:
- I dati vengono inviati ai provider LLM **solo quando richiesto esplicitamente dall'utente**
- L'utente deve fornire la propria API key per attivare queste funzionalità
- Reminor non ha accesso alle API key degli utenti (sono criptate)
- I provider LLM possono avere le proprie politiche di utilizzo dei dati

### 5.2 Hosting e infrastruttura
- **Provider**: OVH
- **Localizzazione**: Varsavia, Polonia (EU)
- **Certificazioni**: ISO 27001, ISO 27017, ISO 27018, ISO 27701, GDPR compliant
- **Sicurezza fisica**: Data center Tier III con controlli biometrici e videosorveglianza 24/7

### 5.3 Altri terzi
Reminor **non condivide** i tuoi dati con:
- Servizi di analytics o tracciamento
- Reti pubblicitarie
- Broker di dati
- Altri terzi non essenziali per il servizio

## 6. Sicurezza dei dati

### 6.1 Misure tecniche
- **Password**: hash con bcrypt (cost factor 12+)
- **API key**: criptazione simmetrica con Fernet (chiave derivata da JWT_SECRET_KEY)
- **Isolamento dati**: ogni utente ha una directory separata identificata da UUID
- **Token JWT**: autenticazione stateless con scadenza (24h access, 30d refresh)
- **Comunicazione**: HTTPS/TLS 1.3 per tutte le connessioni
- **Backup**: criptati e accessibili solo all'utente proprietario

### 6.2 Misure organizzative
- Accesso ai server limitato al personale autorizzato
- Logging di sicurezza per rilevare accessi anomali
- Aggiornamenti regolari di sicurezza

## 7. I tuoi diritti (GDPR)

In qualità di interessato, hai i seguenti diritti:

### 7.1 Diritti principali
1. **Diritto di accesso** (Art. 15): ottenere una copia dei tuoi dati personali
2. **Diritto di rettifica** (Art. 16): correggere dati inaccurati
3. **Diritto alla cancellazione** (Art. 17): richiedere la rimozione dei tuoi dati
4. **Diritto di limitazione** (Art. 18): limitare il trattamento in determinate circostanze
5. **Diritto alla portabilità** (Art. 20): ricevere i dati in formato strutturato (JSON/ZIP)
6. **Diritto di opposizione** (Art. 21): opporti al trattamento basato su interesse legittimo
7. **Diritto di non essere sottoposto a decisioni automatizzate** (Art. 22)

### 7.2 Come esercitare i diritti
Invia una richiesta a: **welcome@reminor.it**

- Tempo di risposta: 30 giorni
- Identificazione richiesta: email associata all'account
- Formato esportazione: JSON o ZIP (come disponibile nell'app)

### 7.3 Reclami
Hai il diritto di presentare reclamo all'Autorità Garante per la Protezione dei Dati Personali:
- **Sito web**: [www.garanteprivacy.it](https://www.garanteprivacy.it)
- **Email**: garante@gpdp.it

## 8. Esportazione e backup

Reminor offre strumenti di **data portability** integrati:

- **Backup ZIP**: scarica tutto il diario, emozioni, e knowledge base
- **Backup JSON**: formato machine-readable completo
- **File .mv2**: backup della memoria semantica

Tutti i backup sono accessibili dall'utente in qualsiasi momento attraverso l'interfaccia web.

## 9. Cookie e tecnologie simili

### 9.1 Cookie tecnici (necessari)
| Cookie | Scopo | Durata |
|--------|-------|--------|
| `access_token` | Autenticazione JWT | Sessione / 24h |
| `refresh_token` | Refresh autenticazione | 30 giorni |
| `language` | Preferenza lingua | Persistente |

### 9.2 Cookie di terze parti
- **Nessuno**: Reminor non utilizza cookie di tracciamento, analytics o pubblicitari

## 10. Servizio AI e considerazioni specifiche

### 10.1 Trasmissione dati AI
Quando utilizzi le funzionalità AI (analisi emotiva o chat):
- Il contenuto del diario viene inviato ai provider LLM
- I dati possono essere processati al di fuori dell'UE (USA, Cina per DeepSeek)
- I provider possono conservare i dati secondo le proprie policy

### 10.2 Consigli per la privacy
- **Non inserire dati sensibili** di terzi nel diario senza consenso
- **Verifica la privacy policy** del provider LLM scelto
- **Utilizza provider UE** (es. Mistral) per maggiore protezione GDPR
- **Non inserire**: codici fiscali, numeri di carta di credito, dati sanitari sensibili

## 11. Modifiche alla Privacy Policy

Ci riserviamo il diritto di aggiornare questa Privacy Policy. Le modifiche saranno:
- Pubblicate su questa pagina con data aggiornata
- Comunicate via email per cambiamenti sostanziali
- Efficaci 30 giorni dopo la pubblicazione

## 12. Contatti

Per domande sulla privacy o per esercitare i tuoi diritti:

**Titolare del trattamento:** Affinity Srl  
**Email privacy:** welcome@reminor.it  
**Email aziendale:** info@affinitylab.it  
**P.IVA:** 06221050658  
**Responsabile della protezione dei dati (DPO):** Non designato (non obbligatorio per questa tipologia di trattamento)

---

## Riepilogo per l'utente

✅ **I tuoi dati sono:**
- Isolati per utente (UUID)
- Criptati quando sensibili (password, API key)
- Mai venduti o condivisi per scopi commerciali
- Esportabili in qualsiasi momento
- Cancellabili su richiesta

⚠️ **Ricorda:**
- L'uso delle funzionalità AI implica l'invio di dati ai provider LLM
- Tu controlli quale provider utilizzare tramite la tua API key
- Se non configuri un LLM, i dati rimangono solo sui nostri server

🛡️ **Consigliato:**
- Usa una password forte e unica
- Non condividere la tua API key
- Esporta regolarmente i tuoi dati
- Leggi la privacy policy del provider LLM scelto
