package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/joho/godotenv"
)

var (
	// Colori adattivi per la chat
	chatPrimaryColor = lipgloss.AdaptiveColor{Light: "#7C3AED", Dark: "#A78BFA"}
	chatSecondaryColor = lipgloss.AdaptiveColor{Light: "#059669", Dark: "#10B981"}
	chatAccentColor = lipgloss.AdaptiveColor{Light: "#DC2626", Dark: "#EF4444"}
	chatNeutralColor = lipgloss.AdaptiveColor{Light: "#6B7280", Dark: "#9CA3AF"}

	chatHeaderStyle = lipgloss.NewStyle().
		Background(chatPrimaryColor).
		Foreground(lipgloss.Color("230")).
		Padding(0, 1).
		Bold(true).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(chatPrimaryColor).
		MarginBottom(1)

	userMessageStyle = lipgloss.NewStyle().
		Foreground(chatSecondaryColor).
		Bold(true).
		Border(lipgloss.ThickBorder(), false, false, false, true).
		BorderForeground(chatSecondaryColor).
		PaddingLeft(1).
		MarginTop(1)

	aiMessageStyle = lipgloss.NewStyle().
		Foreground(chatPrimaryColor).
		Border(lipgloss.ThickBorder(), false, false, false, true).
		BorderForeground(chatPrimaryColor).
		PaddingLeft(1).
		MarginTop(1)

	chatInfoStyle = lipgloss.NewStyle().
		Foreground(chatNeutralColor).
		Italic(true)

	errorStyle = lipgloss.NewStyle().
		Foreground(chatAccentColor).
		Bold(true)

	chatContainerStyle = lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(chatNeutralColor).
		Padding(1)

	inputBoxStyle = lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(chatPrimaryColor).
		Padding(0, 1)
)

type chatMsg struct {
	role    string
	content string
}

type aiResponseMsg struct {
	content string
	err     error
}

type semanticContext struct {
	RelevantEntries string   `json:"relevant_entries"`
	Keywords        []string `json:"keywords"`
	Emotions        map[string]float64 `json:"emotions"`
	Query          string   `json:"query"`
}

type chatModel struct {
	viewport     viewport.Model
	messages     []chatMsg
	textarea     textarea.Model
	cursor       CursorModel
	width        int
	height       int
	ready        bool
	waiting      bool
	spinner      spinner.Model
	apiKey       string
	conversation []map[string]string
	err          error
}

func newChatModel() chatModel {
	// Carica il file .env
	envPath := filepath.Join("..", ".env")
	godotenv.Load(envPath)
	
	ta := textarea.New()
	ta.Placeholder = "Scrivi un messaggio..."
	ta.Focus()
	ta.Prompt = "┃ "
	ta.CharLimit = 2000
	ta.SetHeight(3)
	ta.ShowLineNumbers = false
	ta.FocusedStyle.CursorLine = lipgloss.NewStyle()
	ta.KeyMap.InsertNewline.SetEnabled(false)
	
	// Crea cursore personalizzato
	cursor := NewCursor()
	
	// Configurazione specifica per Windows UTF-8
	if runtime.GOOS == "windows" {
		ta.SetValue("")
	}

	s := spinner.New()
	s.Spinner = spinner.Dot  // Spinner semplice ma sicuramente funzionante
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("205")).Bold(true)

	// Leggi API key da variabile d'ambiente o file .env
	apiKey := os.Getenv("GROQ_API_KEY")
	
	vp := viewport.New(80, 10) // Dimensioni iniziali temporanee
	
	return chatModel{
		viewport: vp,
		textarea: ta,
		cursor:   cursor,
		messages: []chatMsg{
			{role: "system", content: "Benvenuto nella chat con i tuoi pensieri! Scrivi /exit per uscire."},
		},
		spinner: s,
		apiKey:  apiKey,
		ready:   true, // Impostiamo ready a true di default
	}
}

func (m chatModel) Init() tea.Cmd {
	return tea.Batch(
		spinner.Tick, 
		textarea.Blink,
		func() tea.Msg { return CursorBlinkCmd() },
	)
}

func (m chatModel) Update(msg tea.Msg) (chatModel, tea.Cmd) {
	var (
		taCmd tea.Cmd
		vpCmd tea.Cmd
		cursorCmd tea.Cmd
	)

	// Aggiorna il cursore
	m.cursor, cursorCmd = m.cursor.Update(msg)

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height

		headerHeight := lipgloss.Height(m.headerView())
		footerHeight := m.textarea.Height() + 2 // +1 per il footer con le scorciatoie
		availableHeight := m.height - headerHeight - footerHeight

		m.viewport.Width = m.width
		m.viewport.Height = availableHeight

		m.textarea.SetWidth(m.width - 2)
		m.updateViewport()

	case tea.KeyMsg:
		if m.waiting {
			return m, nil
		}

		switch msg.String() {
		case "esc":
			return m, tea.Quit

		case "ctrl+a":
			// Inserisci carattere à
			if runtime.GOOS == "windows" {
				currentText := m.textarea.Value()
				newText := currentText + "à"
				m.textarea.SetValue(newText)
			}

		case "ctrl+e":
			// Inserisci carattere è
			if runtime.GOOS == "windows" {
				currentText := m.textarea.Value()
				newText := currentText + "è"
				m.textarea.SetValue(newText)
			}

		case "ctrl+i":
			// Inserisci carattere ì
			if runtime.GOOS == "windows" {
				currentText := m.textarea.Value()
				newText := currentText + "ì"
				m.textarea.SetValue(newText)
			}

		case "ctrl+o":
			// Inserisci carattere ò
			if runtime.GOOS == "windows" {
				currentText := m.textarea.Value()
				newText := currentText + "ò"
				m.textarea.SetValue(newText)
			}

		case "ctrl+u":
			// Inserisci carattere ù
			if runtime.GOOS == "windows" {
				currentText := m.textarea.Value()
				newText := currentText + "ù"
				m.textarea.SetValue(newText)
			}

		case "enter":
			userMsg := strings.TrimSpace(m.textarea.Value())
			if userMsg == "" {
				return m, nil
			}

			if strings.ToLower(userMsg) == "/exit" || strings.ToLower(userMsg) == "/esci" {
				return m, tea.Quit
			}

			// Aggiungi messaggio utente
			m.messages = append(m.messages, chatMsg{role: "user", content: userMsg})
			m.conversation = append(m.conversation, map[string]string{"role": "user", "content": userMsg})
			
			// Aggiungi messaggio di attesa temporaneo
			m.messages = append(m.messages, chatMsg{role: "thinking", content: ""})
			
			m.textarea.Reset()
			m.waiting = true
			m.updateViewport() // Aggiorna vista con spinner

			// Invia richiesta all'AI
			return m, tea.Batch(
				m.sendToAI(userMsg),
				spinner.Tick,
			)
		}

	case aiResponseMsg:
		m.waiting = false
		
		// Rimuovi messaggio di "thinking" temporaneo
		if len(m.messages) > 0 && m.messages[len(m.messages)-1].role == "thinking" {
			m.messages = m.messages[:len(m.messages)-1]
		}
		
		if msg.err != nil {
			m.messages = append(m.messages, chatMsg{role: "error", content: msg.err.Error()})
		} else {
			m.messages = append(m.messages, chatMsg{role: "ai", content: msg.content})
			m.conversation = append(m.conversation, map[string]string{"role": "assistant", "content": msg.content})
			
			// Mantieni solo ultimi 6 messaggi nella conversazione
			if len(m.conversation) > 6 {
				m.conversation = m.conversation[len(m.conversation)-6:]
			}
		}
		m.updateViewport()
		return m, nil

	case spinner.TickMsg:
		if m.waiting {
			var cmd tea.Cmd
			m.spinner, cmd = m.spinner.Update(msg)
			m.updateViewport() // Aggiorna la vista per mostrare l'animazione
			return m, cmd
		}

	}

	if !m.waiting {
		m.textarea, taCmd = m.textarea.Update(msg)
	}
	m.viewport, vpCmd = m.viewport.Update(msg)

	return m, tea.Batch(taCmd, vpCmd, cursorCmd)
}

func (m *chatModel) updateViewport() {
	if m.viewport.Width <= 0 {
		return // Non aggiornare se il viewport non è stato ridimensionato
	}
	
	var content strings.Builder
	
	// Usa larghezza dinamica e lascia più margine
	wrapWidth := max(40, m.viewport.Width-4)
	wrapStyle := lipgloss.NewStyle().Width(wrapWidth)
	
	for i, msg := range m.messages {
		switch msg.role {
		case "system":
			wrapped := wrapStyle.Render(chatInfoStyle.Render(msg.content))
			content.WriteString(wrapped)
		case "user":
			userText := userMessageStyle.Render("Tu: ") + msg.content
			wrapped := wrapStyle.Render(userText)
			content.WriteString(wrapped)
		case "ai":
			aiText := aiMessageStyle.Render("AI: ") + msg.content
			wrapped := wrapStyle.Render(aiText)
			content.WriteString(wrapped)
		case "thinking":
			// Messaggio di attesa con spinner
			spinnerText := lipgloss.NewStyle().
				Foreground(lipgloss.Color("159")).
				Italic(true).
				Render("Reminor sta pensando")
			thinkingText := fmt.Sprintf("   %s %s...", m.spinner.View(), spinnerText)
			wrapped := wrapStyle.Render(thinkingText)
			content.WriteString(wrapped)
		case "error":
			errorText := errorStyle.Render("Errore: ") + msg.content
			wrapped := wrapStyle.Render(errorText)
			content.WriteString(wrapped)
		}
		
		// Aggiungi spazio tra i messaggi, ma non dopo l'ultimo
		if i < len(m.messages)-1 {
			content.WriteString("\n\n")
		}
	}

	m.viewport.SetContent(content.String())
	m.viewport.GotoBottom()
}

func (m chatModel) sendToAI(userMessage string) tea.Cmd {
	return func() tea.Msg {
		if m.apiKey == "" {
			return aiResponseMsg{err: fmt.Errorf("GROQ_API_KEY non configurata")}
		}

		// Ottieni contesto dal server Python
		context := m.getSemanticContext(userMessage)

		systemPrompt := fmt.Sprintf(`Sei un assistente spirituale empatico che analizza e discute il diario personale dell'utente.

CONTESTO DAL DIARIO:
%s

PAROLE CHIAVE RILEVANTI: %s

Le tue risposte devono essere:
- Empatiche e supportive
- Basate sul contesto del diario quando rilevante
- Brevi e concise (max 2-3 frasi)
- In italiano
- Orientate alla crescita personale`, context.RelevantEntries, strings.Join(context.Keywords, ", "))

		messages := []map[string]string{
			{"role": "system", "content": systemPrompt},
		}
		messages = append(messages, m.conversation...)

		payload := map[string]interface{}{
			"model":       "deepseek-r1-distill-llama-70b",
			"messages":    messages,
			"temperature": 0.7,
			"max_tokens":  2000,
		}

		jsonData, err := json.Marshal(payload)
		if err != nil {
			return aiResponseMsg{err: err}
		}

		req, err := http.NewRequest("POST", "https://api.groq.com/openai/v1/chat/completions", bytes.NewBuffer(jsonData))
		if err != nil {
			return aiResponseMsg{err: err}
		}

		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer "+m.apiKey)

		client := &http.Client{Timeout: 30 * time.Second}
		resp, err := client.Do(req)
		if err != nil {
			return aiResponseMsg{err: err}
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return aiResponseMsg{err: err}
		}

		if resp.StatusCode != http.StatusOK {
			return aiResponseMsg{err: fmt.Errorf("API error: %s", string(body))}
		}

		var result map[string]interface{}
		if err := json.Unmarshal(body, &result); err != nil {
			return aiResponseMsg{err: err}
		}

		choices, ok := result["choices"].([]interface{})
		if !ok || len(choices) == 0 {
			return aiResponseMsg{err: fmt.Errorf("risposta API non valida")}
		}

		firstChoice := choices[0].(map[string]interface{})
		message := firstChoice["message"].(map[string]interface{})
		content := message["content"].(string)
		
		// Rimuovi i tag <think> e </think>
		content = removeThinkTags(content)

		return aiResponseMsg{content: content}
	}
}

func (m chatModel) View() string {
	if !m.ready {
		return "\n  Inizializzazione chat..."
	}

	var footer string
	if runtime.GOOS == "windows" {
		footer = lipgloss.NewStyle().
			Foreground(chatNeutralColor).
			Italic(true).
			Render("Caratteri accentati: Ctrl+A(à) Ctrl+E(è) Ctrl+I(ì) Ctrl+O(ò) Ctrl+U(ù) • ESC: esci")
	} else {
		footer = lipgloss.NewStyle().
			Foreground(chatNeutralColor).
			Italic(true).
			Render("ESC: esci")
	}

	// Input area con bordo e più spazio
	inputArea := inputBoxStyle.Render(m.textarea.View())
	
	// Spaziatura maggiore tra viewport e input
	spacing := lipgloss.NewStyle().Height(2).Render("")

	return lipgloss.JoinVertical(
		lipgloss.Left,
		m.headerView(),
		m.viewport.View(),
		spacing, // Aggiunge spazio extra
		inputArea,
		footer,
	)
}

func (m chatModel) headerView() string {
	title := "💭 CHAT CON I TUOI PENSIERI"
	line := strings.Repeat("─", max(0, m.width-lipgloss.Width(title)-2))
	return chatHeaderStyle.Render(title + " " + line)
}

func (m chatModel) getSemanticContext(userMessage string) semanticContext {
	// Fallback di default
	defaultContext := semanticContext{
		Query: userMessage,
		RelevantEntries: "Nessun contesto disponibile dal diario.",
		Keywords: []string{},
		Emotions: map[string]float64{},
	}
	
	// Chiama il server Python per ottenere contesto semantico
	contextReq := map[string]interface{}{
		"query": userMessage,
		"days_back": 30,
	}
	
	jsonData, err := json.Marshal(contextReq)
	if err != nil {
		return defaultContext
	}
	
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Post("http://127.0.0.1:8080/context", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		// Se il server Python non è disponibile, restituisci contesto vuoto
		return defaultContext
	}
	defer resp.Body.Close()
	
	if resp.StatusCode != http.StatusOK {
		// Leggi l'errore se possibile per debug
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("Server error: %s\n", string(body))
		return defaultContext
	}
	
	var context semanticContext
	if err := json.NewDecoder(resp.Body).Decode(&context); err != nil {
		return defaultContext
	}
	
	return context
}

func removeThinkTags(content string) string {
	// Rimuovi tutto ciò che è tra <think> e </think>
	re := regexp.MustCompile(`(?s)<think>.*?</think>`)
	cleaned := re.ReplaceAllString(content, "")
	
	// Rimuovi spazi extra e righe vuote
	cleaned = strings.TrimSpace(cleaned)
	
	return cleaned
}


