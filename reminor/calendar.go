package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	// Colori adattivi per il calendario
	calendarPrimaryColor = lipgloss.AdaptiveColor{Light: "#7C3AED", Dark: "#A78BFA"}
	calendarSecondaryColor = lipgloss.AdaptiveColor{Light: "#059669", Dark: "#10B981"}
	calendarAccentColor = lipgloss.AdaptiveColor{Light: "#DC2626", Dark: "#EF4444"}
	calendarNeutralColor = lipgloss.AdaptiveColor{Light: "#6B7280", Dark: "#9CA3AF"}
	calendarBgColor = lipgloss.AdaptiveColor{Light: "#F9FAFB", Dark: "#111827"}

	calendarHeaderStyle = lipgloss.NewStyle().
		Background(calendarPrimaryColor).
		Foreground(lipgloss.Color("230")).
		Padding(0, 1).
		Bold(true).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(calendarPrimaryColor).
		MarginBottom(1)

	monthYearStyle = lipgloss.NewStyle().
		Foreground(calendarPrimaryColor).
		Bold(true).
		Align(lipgloss.Center).
		MarginBottom(1).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(calendarNeutralColor).
		Padding(1, 2)

	weekdayStyle = lipgloss.NewStyle().
		Foreground(calendarNeutralColor).
		Bold(true).
		Align(lipgloss.Center).
		Border(lipgloss.NormalBorder(), false, false, true, false).
		BorderForeground(calendarNeutralColor).
		PaddingBottom(1)

	normalDayStyle = lipgloss.NewStyle().
		Foreground(calendarNeutralColor).
		Align(lipgloss.Center).
		Width(4).
		Height(1).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.AdaptiveColor{Light: "#E5E7EB", Dark: "#374151"}).
		Margin(0, 1)

	todayStyle = lipgloss.NewStyle().
		Background(calendarSecondaryColor).
		Foreground(lipgloss.Color("230")).
		Bold(true).
		Align(lipgloss.Center).
		Width(4).
		Height(1).
		Border(lipgloss.ThickBorder()).
		BorderForeground(calendarSecondaryColor).
		Margin(0, 1)

	entryDayStyle = lipgloss.NewStyle().
		Background(calendarAccentColor).
		Foreground(lipgloss.Color("230")).
		Bold(true).
		Align(lipgloss.Center).
		Width(4).
		Height(1)

	selectedDayStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("205")).
		Bold(true).
		Underline(true)

	calendarInfoStyle = lipgloss.NewStyle().
		Foreground(lipgloss.Color("241")).
		Italic(true)
)

type calendarModel struct {
	currentDate  time.Time
	selectedDate time.Time
	entriesMap   map[string]bool
	journalDir   string
	width        int
	height       int
}

func newCalendarModel() calendarModel {
	homeDir, _ := os.UserHomeDir()
	journalDir := filepath.Join(homeDir, ".mysoul_journal")
	
	now := time.Now()
	
	return calendarModel{
		currentDate:  now,
		selectedDate: now,
		entriesMap:   make(map[string]bool),
		journalDir:   journalDir,
	}
}

func (m calendarModel) Init() tea.Cmd {
	return m.loadEntries
}

func (m calendarModel) loadEntries() tea.Msg {
	// Carica tutte le entries dal journal directory
	entries := make(map[string]bool)
	
	files, err := os.ReadDir(m.journalDir)
	if err != nil {
		return entries
	}
	
	for _, file := range files {
		if strings.HasSuffix(file.Name(), ".txt") && !strings.Contains(file.Name(), "_emotions") {
			// Estrai la data dal nome del file (YYYY-MM-DD.txt)
			dateStr := strings.TrimSuffix(file.Name(), ".txt")
			entries[dateStr] = true
		}
	}
	
	return entries
}

func (m calendarModel) Update(msg tea.Msg) (calendarModel, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		
	case map[string]bool:
		m.entriesMap = msg
		
	case tea.KeyMsg:
		switch msg.String() {
		case "esc":
			return m, tea.Quit
			
		case "left", "h":
			m.selectedDate = m.selectedDate.AddDate(0, 0, -1)
			
		case "right", "l":
			m.selectedDate = m.selectedDate.AddDate(0, 0, 1)
			
		case "up", "k":
			m.selectedDate = m.selectedDate.AddDate(0, 0, -7)
			
		case "down", "j":
			m.selectedDate = m.selectedDate.AddDate(0, 0, 7)
			
		case "pgup", "[":
			m.selectedDate = m.selectedDate.AddDate(0, -1, 0)
			
		case "pgdown", "]":
			m.selectedDate = m.selectedDate.AddDate(0, 1, 0)
			
		case "t":
			m.selectedDate = time.Now()
			
		case "enter":
			// Apri la pagina del giorno selezionato
			dateStr := m.selectedDate.Format("2006-01-02")
			return m, func() tea.Msg {
				return switchToPagerMsg{date: dateStr}
			}
		}
	}
	
	return m, nil
}

func (m calendarModel) View() string {
	var s strings.Builder
	
	// Header
	s.WriteString(m.headerView() + "\n\n")
	
	// Mese e anno
	monthYear := m.selectedDate.Format("January 2006")
	s.WriteString(monthYearStyle.Width(m.width).Render(monthYear) + "\n\n")
	
	// Giorni della settimana
	weekdays := []string{"Dom", "Lun", "Mar", "Mer", "Gio", "Ven", "Sab"}
	var weekdayRow strings.Builder
	for i, wd := range weekdays {
		weekdayRow.WriteString(weekdayStyle.Width(6).Render(wd))
		if i < 6 {
			weekdayRow.WriteString(" ")
		}
	}
	s.WriteString(lipgloss.Place(m.width, 1, lipgloss.Center, lipgloss.Top, weekdayRow.String()) + "\n\n")
	
	// Calendario
	firstDay := time.Date(m.selectedDate.Year(), m.selectedDate.Month(), 1, 0, 0, 0, 0, time.Local)
	lastDay := firstDay.AddDate(0, 1, -1)
	
	// Padding iniziale
	startPadding := int(firstDay.Weekday())
	currentDay := 1
	
	for week := 0; week < 6; week++ {
		var weekRow strings.Builder
		
		for day := 0; day < 7; day++ {
			if week == 0 && day < startPadding {
				weekRow.WriteString("      ") // 6 spazi per giorno vuoto
			} else if currentDay <= lastDay.Day() {
				date := time.Date(m.selectedDate.Year(), m.selectedDate.Month(), currentDay, 0, 0, 0, 0, time.Local)
				dateStr := date.Format("2006-01-02")
				dayStr := fmt.Sprintf(" %2d ", currentDay)
				
				// Determina lo stile del giorno
				style := normalDayStyle
				isSelected := date.Format("2006-01-02") == m.selectedDate.Format("2006-01-02")
				
				if m.entriesMap[dateStr] {
					style = entryDayStyle
				}
				
				if date.Format("2006-01-02") == time.Now().Format("2006-01-02") {
					style = todayStyle
				}
				
				if isSelected {
					// Applica lo stile di selezione sopra lo stile base
					if m.entriesMap[dateStr] {
						// Giorno con entry + selezionato
						weekRow.WriteString(" " + entryDayStyle.Copy().Inherit(selectedDayStyle).Render(dayStr) + " ")
					} else if date.Format("2006-01-02") == time.Now().Format("2006-01-02") {
						// Oggi + selezionato
						weekRow.WriteString(" " + todayStyle.Copy().Inherit(selectedDayStyle).Render(dayStr) + " ")
					} else {
						// Giorno normale + selezionato
						weekRow.WriteString(" " + selectedDayStyle.Render(dayStr) + " ")
					}
				} else {
					weekRow.WriteString(" " + style.Render(dayStr) + " ")
				}
				
				currentDay++
			} else {
				weekRow.WriteString("      ") // 6 spazi per giorno vuoto
			}
			
			if day < 6 {
				weekRow.WriteString(" ")
			}
		}
		
		s.WriteString(lipgloss.Place(m.width, 1, lipgloss.Center, lipgloss.Top, weekRow.String()) + "\n")
		
		if currentDay > lastDay.Day() {
			break
		}
	}
	
	// Legenda e istruzioni
	s.WriteString("\n\n")
	
	// Crea la legenda con gli stili effettivi
	legendItems := []string{
		todayStyle.Render("    ") + " Oggi",
		entryDayStyle.Render("    ") + " Con pagina",
		selectedDayStyle.Render(" ▼ ") + " Selezionato",
	}
	legend := strings.Join(legendItems, "   ")
	s.WriteString(lipgloss.Place(m.width, 1, lipgloss.Center, lipgloss.Top, legend) + "\n\n")
	
	instructions := "←/→: Naviga giorni • ↑/↓: Naviga settimane • [/]: Mese prec/succ • t: Oggi • Esc: Menu"
	s.WriteString(calendarInfoStyle.Width(m.width).Align(lipgloss.Center).Render(instructions))
	
	// Info giorno selezionato
	dateStr := m.selectedDate.Format("2006-01-02")
	if m.entriesMap[dateStr] {
		s.WriteString("\n\n")
		info := fmt.Sprintf("📝 %s - Pagina presente", m.selectedDate.Format("2 January 2006"))
		s.WriteString(lipgloss.NewStyle().
			Foreground(lipgloss.Color("120")).
			Width(m.width).
			Align(lipgloss.Center).
			Render(info))
	}
	
	return lipgloss.Place(m.width, m.height, lipgloss.Center, lipgloss.Center, s.String())
}

func (m calendarModel) headerView() string {
	title := "📅 CALENDARIO"
	line := strings.Repeat("─", max(0, m.width-lipgloss.Width(title)-2))
	return calendarHeaderStyle.Render(title + " " + line)
}