import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

// No StrictMode: it double-mounts LiveKitRoom in dev, which connects and
// tears down the room twice and produces phantom connect/disconnect errors.
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
