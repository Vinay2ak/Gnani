/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        line: "var(--line)",
        muted: "var(--muted)",
        panel: "var(--panel)",
        text: "var(--text)",
        accent: "var(--accent)",
        link: "var(--link)",
        tag: "var(--tag)",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: "6px",
        chip: "4px",
      },
      borderWidth: {
        DEFAULT: "1px",
      },
    },
  },
  plugins: [],
}
