import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        abyss: {
          950: "#050914",
          900: "#071a2b",
          800: "#0d0a24",
        },
        tealglow: "#3ee8c3",
        violetglow: "#9b6bd6",
      },
      fontFamily: {
        sans: ["Vazirmatn", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
