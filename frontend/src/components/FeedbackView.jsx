import { useEffect, useState } from "react";
import { getFeedback } from "../lib/api.js";

export default function FeedbackView({ scenarioId, transcript, onAgain, onHome }) {
  const [feedback, setFeedback] = useState(null);
  const [showTranscript, setShowTranscript] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!scenarioId) return;
    getFeedback(scenarioId, transcript)
      .then(setFeedback)
      .catch(() => setError("Feedback is taking a moment. Your practice still counts."));
  }, [scenarioId, transcript]);

  return (
    <div>
      <h1 className="font-display text-xl font-semibold">Nice work. You practiced out loud.</h1>
      <p className="mt-1 text-clay">That is the whole point, and you did it.</p>

      {!feedback && !error && (
        <p className="mt-8 text-clay">Putting your feedback together...</p>
      )}
      {error && <p className="mt-8 rounded-lg bg-calmsoft p-4">{error}</p>}

      {feedback && (
        <div className="mt-8 grid gap-4">
          <div className="rounded-xl2 border-2 border-fern bg-fernsoft p-6">
            <h2 className="font-display font-semibold text-fern">What went well</h2>
            <ul className="mt-3 grid gap-2">
              {feedback.went_well.map((line, i) => (
                <li key={i} className="flex gap-3">
                  <span aria-hidden="true" className="text-fern">
                    +
                  </span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl2 border-2 border-mist bg-white p-6">
            <h2 className="font-display font-semibold">Something to try, only if you want</h2>
            <p className="mt-3">{feedback.try_next[0]}</p>
          </div>
        </div>
      )}

      {transcript.length > 0 && (
        <div className="mt-6">
          <button
            onClick={() => setShowTranscript((v) => !v)}
            className="focusable text-fern underline underline-offset-4"
            aria-expanded={showTranscript}
          >
            {showTranscript ? "Hide the transcript" : "Read the transcript"}
          </button>
          {showTranscript && (
            <div className="mt-3 grid gap-2 rounded-xl2 border-2 border-mist bg-white p-5">
              {transcript.map((t, i) => (
                <p key={i}>
                  <span className="font-medium">{t.speaker}: </span>
                  {t.text}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <button
          onClick={onAgain}
          className="focusable rounded-xl2 bg-fern px-6 py-4 font-display font-semibold text-white"
        >
          Practice this again
        </button>
        <button
          onClick={onHome}
          className="focusable rounded-xl2 border-2 border-mist bg-white px-6 py-4 font-display font-semibold"
        >
          Choose another conversation
        </button>
      </div>
    </div>
  );
}
