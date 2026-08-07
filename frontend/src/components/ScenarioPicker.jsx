import { useEffect, useState } from "react";
import { getScenarios, startSession } from "../lib/api.js";

const MOOD_LABELS = {
  friendly: { title: "Friendly", desc: "Warm and patient. A good place to start." },
  neutral: { title: "Everyday", desc: "Ordinary and polite, like real life." },
};

export default function ScenarioPicker({ onStart }) {
  const [scenarios, setScenarios] = useState([]);
  const [selected, setSelected] = useState(null);
  const [mood, setMood] = useState("friendly");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getScenarios()
      .then((d) => setScenarios(d.scenarios))
      .catch(() => setError("The server is not reachable. Check the backend is running."));
  }, []);

  async function begin() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      const info = await startSession(selected, mood);
      onStart(info);
    } catch (e) {
      setError("Could not start the session. Try once more in a moment.");
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-xl font-semibold">Choose a conversation to practice</h1>
      <p className="mt-1 text-clay">Nothing is recorded to an account. This space is yours.</p>

      <div className="mt-6 grid gap-4">
        {scenarios.map((s) => (
          <button
            key={s.id}
            onClick={() => setSelected(s.id)}
            aria-pressed={selected === s.id}
            className={`focusable rounded-xl2 border-2 p-5 text-left transition-colors ${
              selected === s.id
                ? "border-fern bg-fernsoft"
                : "border-mist bg-white hover:border-fern/50"
            }`}
          >
            <div className="font-display text-lg font-medium">{s.title}</div>
            <div className="mt-1 text-clay">{s.blurb}</div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="mt-8">
          <h2 className="font-display font-medium">How should the other person act?</h2>
          <div className="mt-3 flex gap-3">
            {Object.entries(MOOD_LABELS).map(([key, m]) => (
              <button
                key={key}
                onClick={() => setMood(key)}
                aria-pressed={mood === key}
                className={`focusable flex-1 rounded-xl2 border-2 p-4 text-left ${
                  mood === key ? "border-fern bg-fernsoft" : "border-mist bg-white"
                }`}
              >
                <div className="font-medium">{m.title}</div>
                <div className="text-sm text-clay">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {error && <p className="mt-6 rounded-lg bg-calmsoft p-4 text-ink">{error}</p>}

      <div className="mt-10">
        <button
          onClick={begin}
          disabled={!selected || busy}
          className="focusable w-full rounded-xl2 bg-fern px-6 py-4 font-display text-lg font-semibold text-white disabled:opacity-40 sm:w-auto"
        >
          {busy ? "Setting things up..." : "Start practicing"}
        </button>
        <p className="mt-3 text-sm text-clay">
          You can pause, slow things down, or stop at any moment. Those buttons never move.
        </p>
      </div>
    </div>
  );
}
