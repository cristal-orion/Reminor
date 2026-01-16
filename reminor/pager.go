package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/charmbracelet/bubbles/textarea"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	headerStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("170")).
		Background(lipgloss.Color("235")).
		Padding(0, 1).
		Bold(true)

	footerStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("240"))

	contentStyle = lipgloss.NewStyle().
		Padding(1, 2)
)

type pagerModel struct {
	viewport    viewport.Model
	textarea    textarea.Model
	content     string
	ready       bool
	editMode    bool
	width       int
	height      int
	savedStatus string
	date        string // formato YYYY-MM-DD
	filePath    string
}

func newPagerModel() pagerModel {
	model := newPagerModelWithDate("")
	model.editMode = true // Forza sempre modalità editing per "Nuova pagina"
	model.textarea.Focus()
	if model.content != "" {
		model.textarea.SetValue(model.content)
	}
	return model
}

func newPagerModelWithDate(date string) pagerModel {
	ta := textarea.New()
	ta.Placeholder = "Inizia a scrivere i tuoi pensieri..."
	ta.Focus()
	
	// Configurazione specifica per Windows UTF-8
	if runtime.GOOS == "windows" {
		// Configurazioni per migliorare l'input UTF-8 su Windows
		ta.CharLimit = 0 // Rimuovi limite caratteri per evitare problemi UTF-8
	}
	
	// Configurazione specifica per WSL
	if isWSL() {
		ta.SetValue("") // Reset esplicito
	}

	vp := viewport.New(80, 20) // Dimensioni iniziali temporanee
	
	// Se non viene fornita una data, usa oggi
	if date == "" {
		date = time.Now().Format("2006-01-02")
	}
	
	// Costruisci il percorso del file
	homeDir, _ := os.UserHomeDir()
	journalDir := filepath.Join(homeDir, ".mysoul_journal")
	filePath := filepath.Join(journalDir, date+".txt")
	
	// Crea la directory se non esiste
	os.MkdirAll(journalDir, 0755)
	
	// Leggi il contenuto se il file esiste
	content := ""
	editMode := true
	if data, err := os.ReadFile(filePath); err == nil {
		content = strings.TrimSpace(string(data))
		if content != "" {
			ta.SetValue(content)
			editMode = false // Se esiste già con contenuto, parti in modalità visualizzazione
			// Imposta subito il contenuto nel viewport
			vp.SetContent(contentStyle.Render(content))
		}
	}
	
	if editMode {
		vp.SetContent(contentStyle.Render(ta.View()))
	}

	return pagerModel{
		viewport: vp,
		textarea: ta,
		content:  content,
		editMode: editMode,
		ready:    true,
		date:     date,
		filePath: filePath,
	}
}

func (m pagerModel) Init() tea.Cmd {
	if m.editMode {
		return textarea.Blink
	}
	// Se parti in modalità visualizzazione, non serve comando speciale
	return nil
}

func (m pagerModel) Update(msg tea.Msg) (pagerModel, tea.Cmd) {
	var (
		taCmd tea.Cmd
		vpCmd tea.Cmd
	)

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height

		headerHeight := lipgloss.Height(m.headerView())
		footerHeight := lipgloss.Height(m.footerView())
		verticalMarginHeight := headerHeight + footerHeight

		m.viewport.Width = m.width
		m.viewport.Height = m.height - verticalMarginHeight

		m.textarea.SetWidth(m.width - 4)
		m.textarea.SetHeight(m.height - verticalMarginHeight - 2)

		if m.editMode {
			m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
		} else {
			// Se non c'è contenuto, mostra un messaggio
			if m.content == "" {
				m.viewport.SetContent(contentStyle.Render("Nessun contenuto per questa data. Premi 'e' per iniziare a scrivere."))
			} else {
				m.viewport.SetContent(contentStyle.Render(m.content))
			}
		}

	case tea.KeyMsg:
		// Gestione speciale per caratteri UTF-8 su Windows
		if runtime.GOOS == "windows" && m.editMode {
			// Gestione custom per caratteri accentati comuni
			switch msg.String() {
			case "alt+133": // à
				m.textarea.InsertString("à")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			case "alt+138": // è  
				m.textarea.InsertString("è")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			case "alt+141": // ì
				m.textarea.InsertString("ì")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			case "alt+149": // ò
				m.textarea.InsertString("ò")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			case "alt+151": // ù
				m.textarea.InsertString("ù")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			}
		}
		
		// Gestione prima del switch principale per debug
		if msg.String() == "d" && !m.editMode {
			// Debug: mostra info del file
			debugInfo := fmt.Sprintf("DEBUG:\nFile: %s\nContent length: %d\nContent preview: %.100s", 
				m.filePath, len(m.content), m.content)
			m.viewport.SetContent(contentStyle.Render(debugInfo))
			return m, nil
		}
		
		switch msg.String() {
		case "ctrl+a": // Scorciatoia per à
			if m.editMode {
				m.textarea.InsertString("à")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			}
		case "ctrl+e": // Scorciatoia per è
			if m.editMode {
				m.textarea.InsertString("è")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			}
		case "ctrl+i": // Scorciatoia per ì
			if m.editMode {
				m.textarea.InsertString("ì")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			}
		case "ctrl+o": // Scorciatoia per ò
			if m.editMode {
				m.textarea.InsertString("ò")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			}
		case "ctrl+u": // Scorciatoia per ù
			if m.editMode {
				m.textarea.InsertString("ù")
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, nil
			}
		case "esc":
			if m.editMode {
				return m, tea.Quit
			}
			m.editMode = true
			m.textarea.Focus()
			m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
			return m, textarea.Blink

		case "ctrl+s":
			m.content = m.textarea.Value()
			
			// Salva su file
			err := os.WriteFile(m.filePath, []byte(m.content), 0644)
			if err != nil {
				m.savedStatus = fmt.Sprintf("✗ Errore nel salvataggio: %s", err.Error())
			} else {
				timestamp := time.Now().Format("15:04:05")
				m.savedStatus = fmt.Sprintf("✓ Salvato alle %s", timestamp)
			}
			
			m.editMode = false
			m.textarea.Blur()
			formattedContent := contentStyle.Render(m.content)
			m.viewport.SetContent(formattedContent)
			m.viewport.GotoTop()
			return m, nil

		case "e":
			if !m.editMode {
				m.editMode = true
				m.textarea.SetValue(m.content)
				m.textarea.Focus()
				m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
				return m, textarea.Blink
			}
		}
	}

	if m.editMode {
		m.textarea, taCmd = m.textarea.Update(msg)
		m.viewport.SetContent(contentStyle.Render(m.textarea.View()))
	} else {
		m.viewport, vpCmd = m.viewport.Update(msg)
	}

	return m, tea.Batch(taCmd, vpCmd)
}

func (m pagerModel) View() string {
	if !m.ready {
		return "\n  Inizializzazione..."
	}

	return fmt.Sprintf("%s\n%s\n%s", m.headerView(), m.viewport.View(), m.footerView())
}

func (m pagerModel) headerView() string {
	// Formatta la data in modo leggibile
	if t, err := time.Parse("2006-01-02", m.date); err == nil {
		dateStr := t.Format("2 January 2006")
		title := fmt.Sprintf("📝 %s", dateStr)
		if !m.editMode && m.content != "" {
			title = fmt.Sprintf("📖 %s", dateStr)
		}
		line := strings.Repeat("─", max(0, m.width-lipgloss.Width(title)-2))
		return headerStyle.Render(title + " " + line)
	}
	
	// Fallback se la data non è valida
	title := "📝 NUOVA PAGINA"
	if !m.editMode && m.content != "" {
		title = "📖 VISUALIZZAZIONE"
	}
	line := strings.Repeat("─", max(0, m.width-lipgloss.Width(title)-2))
	return headerStyle.Render(title + " " + line)
}

func (m pagerModel) footerView() string {
	var info string
	if m.editMode {
		if runtime.GOOS == "windows" {
			info = "Ctrl+S: Salva • Esc: Esci • Accenti: Ctrl+A(à) E(è) I(ì) O(ò) U(ù)"
		} else {
			info = "Ctrl+S: Salva • Esc: Esci"
		}
	} else {
		info = "e: Modifica • ↑/↓: Scorri • Esc: Menu principale"
		if m.savedStatus != "" {
			info = m.savedStatus + " • " + info
		}
	}

	line := strings.Repeat("─", max(0, m.width-lipgloss.Width(info)-2))
	return footerStyle.Render(line + " " + info)
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

