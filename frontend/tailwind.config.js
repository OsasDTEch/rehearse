/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F4F4EF",
        mist: "#E7E9E2",
        ink: "#26302C",
        fern: "#3F6B5E",
        fernsoft: "#DCE8E2",
        clay: "#8C8578",
        calm: "#6E6893",
        calmsoft: "#E6E4F0",
      },
      fontFamily: {
        display: ["Outfit", "system-ui", "sans-serif"],
        body: ["'Atkinson Hyperlegible'", "system-ui", "sans-serif"],
      },
      borderRadius: { xl2: "1.25rem" },
    },
  },
  plugins: [],
};
