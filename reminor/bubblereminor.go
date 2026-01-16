package main

import (
	"fmt"
	"os"
	"runtime"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	// Colori adattivi per tema chiaro/scuro
	primaryColor   = lipgloss.AdaptiveColor{Light: "#7D56F4", Dark: "#9D7BF0"}
	secondaryColor = lipgloss.AdaptiveColor{Light: "#F25D94", Dark: "#FF6B9D"}
	accentColor    = lipgloss.AdaptiveColor{Light: "#04B575", Dark: "#00D787"}
	textColor      = lipgloss.AdaptiveColor{Light: "#1A1A1A", Dark: "#FAFAFA"}
	subtleColor    = lipgloss.AdaptiveColor{Light: "#666666", Dark: "#999999"}

	// Stili principali
	titleStyle = lipgloss.NewStyle().
			Foreground(primaryColor).
			Bold(true).
			Align(lipgloss.Center)

	logoStyle = lipgloss.NewStyle().
			Foreground(primaryColor).
			Bold(true).
			Align(lipgloss.Center).
			Border(lipgloss.RoundedBorder()).
			BorderForeground(secondaryColor).
			Padding(1, 2).
			Margin(1, 0)

	normalStyle = lipgloss.NewStyle().
			Foreground(textColor).
			Padding(0, 2)

	selectedStyle = lipgloss.NewStyle().
			Foreground(secondaryColor).
			Background(primaryColor).
			Bold(true).
			Padding(0, 2).
			Margin(0, 1)

	subtitleStyle = lipgloss.NewStyle().
			Foreground(subtleColor).
			Italic(true).
			Align(lipgloss.Center).
			Margin(1, 0)

	menuContainerStyle = lipgloss.NewStyle().
				Border(lipgloss.NormalBorder()).
				BorderForeground(accentColor).
				Padding(2, 4).
				Margin(1, 0)

	helpStyle = lipgloss.NewStyle().
			Foreground(subtleColor).
			Align(lipgloss.Center).
			Margin(1, 0)
)

type switchToPagerMsg struct {
	date string
}
type switchToChatMsg struct{}
type switchToCalendarMsg struct{}

type mainModel struct {
	currentView string
	menu        model
	pager       pagerModel
	chat        chatModel
	calendar    calendarModel
}

type model struct {
	choices  []string
	cursor   int
	selected int
	width    int
	height   int
}

func initialModel() model {
	return model{
		choices: []string{
			"📝 Nuova pagina",
			"📅 Calendario",
			"💭 Chat con i tuoi pensieri",
			"🌈 Emozioni",
		},
		selected: -1,
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			return m, tea.Quit

		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}

		case "down", "j":
			if m.cursor < len(m.choices)-1 {
				m.cursor++
			}

		case "enter", " ":
			m.selected = m.cursor
			switch m.cursor {
			case 0: // Nuova pagina
				return m, func() tea.Msg {
					return switchToPagerMsg{date: ""}
				}
			case 1: // Calendario
				return m, func() tea.Msg {
					return switchToCalendarMsg{}
				}
			case 2: // Chat con i tuoi pensieri
				return m, func() tea.Msg {
					return switchToChatMsg{}
				}
			default:
				return m, tea.Quit
			}
		}
	}

	return m, nil
}

func (m model) View() string {
	asciiArt := `██████╗  ███████╗ ███╗   ███╗ ██╗ ███╗   ██╗  ██████╗  ██████╗
 ██╔══██╗ ██╔════╝ ████╗ ████║ ██║ ████╗  ██║ ██╔═══██╗ ██╔══██╗
 ██████╔╝ █████╗   ██╔████╔██║ ██║ ██╔██╗ ██║ ██║   ██║ ██████╔╝
 ██╔══██╗ ██╔══╝   ██║╚██╔╝██║ ██║ ██║╚██╗██║ ██║   ██║ ██╔══██╗
 ██║  ██║ ███████╗ ██║ ╚═╝ ██║ ██║ ██║ ╚████║ ╚██████╔╝ ██║  ██║
 ╚═╝  ╚═╝ ╚══════╝ ╚═╝     ╚═╝ ╚═╝ ╚═╝  ╚═══╝  ╚═════╝  ╚═╝  ╚═╝`

	// Logo con bordo elegante
	logo := logoStyle.Width(m.width - 4).Render(asciiArt)

	// Sottotitolo con stile migliorato
	subtitle := subtitleStyle.Width(m.width).Render("Il tuo diario digitale nel terminale")

	// Menu con stili migliorati
	var menuItems strings.Builder
	for i, choice := range m.choices {
		if m.cursor == i {
			menuItems.WriteString(selectedStyle.Render(fmt.Sprintf("▶ %s", choice)) + "\n")
		} else {
			menuItems.WriteString(normalStyle.Render(fmt.Sprintf("  %s", choice)) + "\n")
		}
	}

	// Container del menu con bordo
	menuContainer := menuContainerStyle.Width(m.width - 8).Render(menuItems.String())

	// Testo di aiuto
	help := helpStyle.Width(m.width).Render("Naviga con ↑/↓ o j/k • Seleziona con Enter • Esci con Esc")

	// Assembla tutto verticalmente
	content := lipgloss.JoinVertical(
		lipgloss.Center,
		logo,
		subtitle,
		menuContainer,
		help,
	)

	return lipgloss.Place(
		m.width,
		m.height,
		lipgloss.Center,
		lipgloss.Center,
		content,
	)
}

func newMainModel() mainModel {
	return mainModel{
		currentView: "menu",
		menu:        initialModel(),
		pager:       newPagerModel(),
		chat:        newChatModel(),
		calendar:    newCalendarModel(),
	}
}

func (m mainModel) Init() tea.Cmd {
	return m.menu.Init()
}

func (m mainModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case switchToPagerMsg:
		m.currentView = "pager"
		if msg.date != "" {
			m.pager = newPagerModelWithDate(msg.date)
		} else {
			m.pager = newPagerModel()
		}
		return m, m.pager.Init()

	case switchToChatMsg:
		m.currentView = "chat"
		return m, m.chat.Init()

	case switchToCalendarMsg:
		m.currentView = "calendar"
		return m, m.calendar.Init()

	case tea.KeyMsg:
		if msg.String() == "esc" {
			switch m.currentView {
			case "pager":
				m.currentView = "menu"
				// Non resettare il pager, così mantiene lo stato
				return m, nil
			case "chat":
				m.currentView = "menu"
				m.chat = newChatModel()
				return m, nil
			case "calendar":
				m.currentView = "menu"
				m.calendar = newCalendarModel()
				return m, nil
			}
		}
	}

	switch m.currentView {
	case "pager":
		var cmd tea.Cmd
		m.pager, cmd = m.pager.Update(msg)
		return m, cmd

	case "chat":
		var cmd tea.Cmd
		m.chat, cmd = m.chat.Update(msg)
		return m, cmd

	case "calendar":
		var cmd tea.Cmd
		m.calendar, cmd = m.calendar.Update(msg)
		return m, cmd

	default:
		newMenu, cmd := m.menu.Update(msg)
		m.menu = newMenu.(model)
		return m, cmd
	}
}

func (m mainModel) View() string {
	switch m.currentView {
	case "pager":
		return m.pager.View()
	case "chat":
		return m.chat.View()
	case "calendar":
		return m.calendar.View()
	default:
		return m.menu.View()
	}
}

func main() {
	// Configura l'encoding UTF-8 su Windows
	setupWindowsUTF8()

	// Abilita il supporto per l'output UTF-8, specialmente su Windows
	opts := []tea.ProgramOption{
		tea.WithAltScreen(),
		tea.WithOutput(os.Stdout), // Assicura l'output standard
	}

	// Su WSL, potrebbe essere utile disabilitare il mouse che a volte causa problemi
	if isWSL() {
		opts = append(opts, tea.WithMouseCellMotion())
	}

	p := tea.NewProgram(newMainModel(), opts...)
	if _, err := p.Run(); err != nil {
		fmt.Printf("Errore: %v", err)
		os.Exit(1)
	}
}

func isWSL() bool {
	// Controlla se siamo in WSL
	if _, err := os.Stat("/proc/version"); err == nil {
		content, err := os.ReadFile("/proc/version")
		if err == nil {
			return strings.Contains(strings.ToLower(string(content)), "microsoft")
		}
	}
	return false
}

func setupWindowsUTF8() {
	// Su Windows, configura l'encoding UTF-8 per il terminale
	if runtime.GOOS == "windows" {
		// Imposta variabili di ambiente per UTF-8
		os.Setenv("PYTHONUTF8", "1")
		os.Setenv("PYTHONIOENCODING", "utf-8")

		// Per PowerShell, forza l'encoding UTF-8
		os.Setenv("POWERSHELL_UPDATECHECK", "Off")

		// Configura Go per utilizzare UTF-8
		os.Setenv("GOOS", "windows")
		os.Setenv("GOARCH", "amd64")
	}
}
