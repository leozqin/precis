/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./**/*.html"],
  theme: {
    extend: {},
  },
  plugins: [require("@tailwindcss/typography"), require("daisyui"), require("@tailwindcss/forms")],
  daisyui: {
    themes: ["light", "dark", "synthwave", "night", "forest"]
  }
}
