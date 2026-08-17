/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./pages/readmission/**/*.{js,jsx}",
    "./pages/LandingPage.jsx"
  ],
  corePlugins: {
    preflight: false
  },
  theme: {
    extend: {}
  }
}
