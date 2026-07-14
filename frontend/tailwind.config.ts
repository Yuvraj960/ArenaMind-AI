import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ArenaMind brand palette
        arena: {
          50:  "#eef2ff",
          100: "#dde4ff",
          200: "#bec9ff",
          300: "#94abff",
          400: "#6884fc",
          500: "#4566e8",
          600: "#2a4bdb",
          700: "#1d3abf",
          800: "#1b319c",
          900: "#0d1f47",
          950: "#080d1e",
        },
      },
    },
  },
  plugins: [],
};

export default config;