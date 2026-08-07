import { useState } from "react";
import ScenarioPicker from "./components/ScenarioPicker.jsx";
import SessionView from "./components/SessionView.jsx";
import FeedbackView from "./components/FeedbackView.jsx";

export default function App() {
  // stage: "pick" -> "session" -> "feedback"
  const [stage, setStage] = useState("pick");
  const [sessionInfo, setSessionInfo] = useState(null);
  const [transcript, setTranscript] = useState([]);

  function handleStart(info) {
    setTranscript([]);
    setSessionInfo(info);
    setStage("session");
  }

  function handleEnd(finalTranscript) {
    setTranscript(finalTranscript);
    setStage("feedback");
  }

  function handleHome() {
    setSessionInfo(null);
    setTranscript([]);
    setStage("pick");
  }

  return (
    <div className="min-h-screen font-body">
      <header className="mx-auto max-w-3xl px-6 pt-10 pb-4">
        <button
          onClick={handleHome}
          className="focusable font-display text-2xl font-semibold tracking-tight text-fern"
          aria-label="Rehearse home"
        >
          Rehearse
        </button>
        <p className="mt-1 text-clay">
          Practice a conversation out loud, at your pace. You are always in control.
        </p>
      </header>

      <main className="mx-auto max-w-3xl px-6 pb-24">
        {stage === "pick" && <ScenarioPicker onStart={handleStart} />}
        {stage === "session" && sessionInfo && (
          <SessionView session={sessionInfo} onEnd={handleEnd} />
        )}
        {stage === "feedback" && (
          <FeedbackView
            scenarioId={sessionInfo?.scenario?.id}
            transcript={transcript}
            onAgain={() => handleStart(sessionInfo)}
            onHome={handleHome}
          />
        )}
      </main>
    </div>
  );
}
