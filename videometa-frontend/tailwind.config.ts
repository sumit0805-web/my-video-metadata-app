import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#8b5cf6",
        surface: "#1a1a1a",
        bg: "#0f0f0f",
      },
    },
  },
  plugins: [],
};

export default config;
