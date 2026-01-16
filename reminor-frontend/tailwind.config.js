/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{svelte,js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#ffffff",
        "background-dark": "#000000",
        "background-light": "#f4f4f4",
        "terminal-border": "#333333",
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "monospace"],
        display: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        DEFAULT: "0px",
        lg: "0px",
        xl: "0px",
        full: "0px",
      },
    },
  },
  plugins: [],
}
