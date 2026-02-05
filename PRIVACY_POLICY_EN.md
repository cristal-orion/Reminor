# Privacy Policy - Reminor

**Last updated:** February 5, 2026

## 1. Introduction

This Privacy Policy describes how **Reminor** collects, uses, stores, and protects your personal data when you use our AI-powered personal diary service, available at [app.reminor.it](https://app.reminor.it).

Reminor is designed with **privacy by design**: your data is isolated, encrypted when necessary, and never used for commercial or advertising purposes.

**Data Controller:**  
Affinity Srl  
Via Lanzara 33, 80014 Nocera Inferiore (SA), Italy  
VAT: 06221050658  
Email: info@affinitylab.it

## 2. Data We Collect

### 2.1 Account Data
- **Email**: used for authentication and service communications
- **Name** (optional): to personalize the experience
- **Preferred language** (Italian/English): to adapt the interface
- **Password**: stored in hashed form (bcrypt)
- **Account creation date**

### 2.2 Diary Data
- **Diary page content**: text entered by the user
- **Entry dates**: associated with diary content
- **Emotional analysis**: scores on 8 emotional dimensions (happy, sad, angry, anxious, calm, stressed, grateful, motivated)
- **Daily insights**: AI-generated analysis of content
- **Knowledge base**: information automatically extracted from the diary to personalize the chat

### 2.3 Technical and Usage Data
- **Writing statistics**: word count, daily streaks, writing frequency
- **Access logs**: operation timestamps (exclusively for security purposes)

### 2.4 API Key (optional)
- **LLM provider API keys**: if configured, stored in encrypted form (Fernet encryption)
- **Preferred provider and model**: LLM configuration chosen by the user

## 3. How We Use Your Data

| Data | Purpose | Legal Basis |
|------|---------|-------------|
| Email, password | Authentication and account security | Contract execution (Art. 6(1)(b) GDPR) |
| Diary content | Provide journaling service | Contract execution (Art. 6(1)(b) GDPR) |
| Emotional analysis | Analysis and statistics functionality | Explicit consent (Art. 6(1)(a) GDPR) |
| API key | Connect to user-selected LLM services | Contract execution (Art. 6(1)(b) GDPR) |
| Knowledge base | Personalize AI responses | Legitimate interest (Art. 6(1)(f) GDPR) - improve service |

**Important note**: Emotional analysis and AI chat require sending diary content to the LLM providers chosen by the user. This happens **only upon explicit user request** and using the API key provided by the user.

## 4. Data Retention

### 4.1 Retention Period
- **Account data**: retained until account deletion is requested
- **Diary content**: retained until explicitly deleted by the user
- **API keys**: retained until removed by the user
- **Security logs**: maximum 90 days

### 4.2 Deletion
- Users can request complete deletion of all data by writing to welcome@reminor.it or info@affinitylab.it
- Data is removed within 30 days of the request
- Backups are deleted according to automatic retention cycles

## 5. Sharing with Third Parties

### 5.1 LLM Providers (AI Services)
The following data is shared **only when the user uses AI features** (emotional analysis or chat):

| Provider | Data Shared | Country | Privacy Policy |
|----------|-------------|---------|----------------|
| Groq | Diary content, chat messages | USA | [groq.com/privacy](https://groq.com/privacy) |
| OpenAI | Diary content, chat messages | USA | [openai.com/privacy](https://openai.com/privacy) |
| Anthropic | Diary content, chat messages | USA | [anthropic.com/privacy](https://anthropic.com/privacy) |
| Google (Gemini) | Diary content, chat messages | USA | [policies.google.com/privacy](https://policies.google.com/privacy) |
| Mistral | Diary content, chat messages | France | [mistral.ai/privacy](https://mistral.ai/privacy) |
| DeepSeek | Diary content, chat messages | China | [deepseek.com/privacy](https://deepseek.com/privacy) |

**Important**:
- Data is sent to LLM providers **only when explicitly requested by the user**
- The user must provide their own API key to activate these features
- Reminor does not have access to user API keys (they are encrypted)
- LLM providers may have their own data usage policies

### 5.2 Hosting and Infrastructure
- **Provider**: OVH
- **Location**: Warsaw, Poland (EU)
- **Certifications**: ISO 27001, ISO 27017, ISO 27018, ISO 27701, GDPR compliant
- **Physical security**: Tier III data center with biometric controls and 24/7 video surveillance

### 5.3 Other Third Parties
Reminor **does not share** your data with:
- Analytics or tracking services
- Advertising networks
- Data brokers
- Other non-essential third parties

## 6. Data Security

### 6.1 Technical Measures
- **Passwords**: hashed with bcrypt (cost factor 12+)
- **API keys**: symmetric encryption with Fernet (key derived from JWT_SECRET_KEY)
- **Data isolation**: each user has a separate directory identified by UUID
- **JWT tokens**: stateless authentication with expiration (24h access, 30d refresh)
- **Communication**: HTTPS/TLS 1.3 for all connections
- **Backups**: encrypted and accessible only to the owner user

### 6.2 Organizational Measures
- Server access limited to authorized personnel
- Security logging to detect anomalous access
- Regular security updates

## 7. Your Rights (GDPR)

As a data subject, you have the following rights:

### 7.1 Main Rights
1. **Right of access** (Art. 15): obtain a copy of your personal data
2. **Right to rectification** (Art. 16): correct inaccurate data
3. **Right to erasure** (Art. 17): request removal of your data
4. **Right to restriction** (Art. 18): limit processing in certain circumstances
5. **Right to data portability** (Art. 20): receive data in structured format (JSON/ZIP)
6. **Right to object** (Art. 21): object to processing based on legitimate interest
7. **Right not to be subject to automated decision-making** (Art. 22)

### 7.2 How to Exercise Your Rights
Send a request to: **welcome@reminor.it**

- Response time: 30 days
- Identification required: email associated with the account
- Export format: JSON or ZIP (as available in the app)

### 7.3 Complaints
You have the right to lodge a complaint with the Italian Data Protection Authority:
- **Website**: [www.garanteprivacy.it](https://www.garanteprivacy.it)
- **Email**: garante@gpdp.it

## 8. Export and Backup

Reminor offers integrated **data portability** tools:

- **ZIP Backup**: download entire diary, emotions, and knowledge base
- **JSON Backup**: complete machine-readable format
- **.mv2 File**: backup of semantic memory

All backups are accessible by the user at any time through the web interface.

## 9. Cookies and Similar Technologies

### 9.1 Technical Cookies (Necessary)
| Cookie | Purpose | Duration |
|--------|---------|----------|
| `access_token` | JWT authentication | Session / 24h |
| `refresh_token` | Authentication refresh | 30 days |
| `language` | Language preference | Persistent |

### 9.2 Third-Party Cookies
- **None**: Reminor does not use tracking, analytics, or advertising cookies

## 10. AI Service and Specific Considerations

### 10.1 AI Data Transmission
When you use AI features (emotional analysis or chat):
- Diary content is sent to LLM providers
- Data may be processed outside the EU (USA, China for DeepSeek)
- Providers may retain data according to their own policies

### 10.2 Privacy Recommendations
- **Do not enter sensitive data** about third parties in the diary without consent
- **Check the privacy policy** of the chosen LLM provider
- **Use EU providers** (e.g., Mistral) for greater GDPR protection
- **Do not enter**: tax codes, credit card numbers, sensitive health data

## 11. Changes to Privacy Policy

We reserve the right to update this Privacy Policy. Changes will be:
- Published on this page with updated date
- Communicated via email for substantial changes
- Effective 30 days after publication

## 12. Contact

For privacy questions or to exercise your rights:

**Data Controller:** Affinity Srl  
**Privacy Email:** welcome@reminor.it  
**Business Email:** info@affinitylab.it  
**VAT:** 06221050658  
**Data Protection Officer (DPO):** Not designated (not required for this type of processing)

---

## Summary for Users

✅ **Your data is:**
- Isolated by user (UUID)
- Encrypted when sensitive (password, API key)
- Never sold or shared for commercial purposes
- Exportable at any time
- Deletable upon request

⚠️ **Remember:**
- Using AI features involves sending data to LLM providers
- You control which provider to use through your API key
- If you don't configure an LLM, data remains only on our servers

🛡️ **Recommended:**
- Use a strong and unique password
- Do not share your API key
- Export your data regularly
- Read the privacy policy of your chosen LLM provider
