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
        s1: "var(--s1)",
        s2: "var(--s2)",
        hair: "var(--hair)",
        surface: "var(--s1)",
        line: "var(--hair)",
        text: "var(--text)",
        muted: "var(--muted)",
        panel: "var(--panel)",
        accent: "var(--accent)",
        "on-accent": "var(--on-accent)",
        link: "var(--link)",
        tag: "var(--tag)",
        "tag-text": "var(--tag-text)",
        hl: "var(--hl)",
      },
      fontFamily: {
        sans: ['"Instrument Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        devanagari: ['"Noto Sans Devanagari"', '"Instrument Sans"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        panel: "12px",
        block: "10px",
        control: "8px",
        chip: "6px",
        DEFAULT: "8px",
      },
    },
  },
  plugins: [],
}
