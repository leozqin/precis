/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./**/*.html"],
  theme: {
    extend: {},
  },
  plugins: [require("@tailwindcss/typography"), require("daisyui"), require("@tailwindcss/forms")],
  daisyui: {
    themes: ["pastel", "black", "coffee", "dark", "fantasy", "forest", "lemonade", "lofi", "luxury", "night", "nord", "synthwave", "winter"]
  }
}
