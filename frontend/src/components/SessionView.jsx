import { useCallback, useEffect, useRef, useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useRoomContext,
  useVoiceAssistant,
  BarVisualizer,
} from "@livekit/components-react";
import { RoomEvent } from "livekit-client";

/* The pace bar is the product promise made visible: the same four controls,
   in the same order, in the same place, on every screen, for the whole session. */
function PaceBar({ paused, onPause, onSlower, onRestart, onEnd, slowed }) {
  const base =
    "focusable rounded-xl2 border-2 px-4 py-3 font-display font-medium transition-colors";
  return (
    <div
      className="fixed inset-x-0 bottom-0 border-t-2 border-mist bg-paper/95 backdrop-blur"
      role="toolbar"
      aria-label="Session controls"
    >
      <div className="mx-auto flex max-w-3xl gap-3 px-6 py-4">
        <button onClick={onPause} className={`${base} flex-1 border-mist bg-white`}>
          {paused ? "Resume" : "Pause"}
        </button>
        <button
          onClick={onSlower}
          disabled={slowed}
          className={`${base} flex-1 border-mist bg-white disabled:opacity-40`}
        >
          {slowed ? "Slowed down" : "Slower, please"}
        </button>
        <button onClick={onRestart} className={`${base} flex-1 border-mist bg-white`}>
          Start over
        </button>
        <button
          onClick={onEnd}
          className={`${base} flex-1 border-fern bg-fern text-white`}
        >
          End &amp; get feedback
        </button>
      </div>
    </div>
  );
}

function SessionInner({ scenario, onEnd }) {
  const room = useRoomContext();
  const { state: agentState, audioTrack } = useVoiceAssistant();
  const [paused, setPaused] = useState(false);
  const [slowed, setSlowed] = useState(false);
  const [safeMode, setSafeMode] = useState(false);
  const [userStarted, setUserStarted] = useState(false);
  const transcriptRef = useRef([]);
  const [lastLine, setLastLine] = useState(null);

  const sendControl = useCallback(
    (action) => {
      const payload = new TextEncoder().encode(JSON.stringify({ action }));
      room.localParticipant.publishData(payload, { topic: "control", reliable: true });
    },
    [room]
  );

  // Capture transcriptions for the feedback step, and surface the latest line.
  useEffect(() => {
    function onTranscription(segments, participant) {
      const isAgent = participant?.identity !== room.localParticipant.identity;
      for (const seg of segments) {
        if (!seg.final) continue;
        const turn = { speaker: isAgent ? "Them" : "You", text: seg.text };
        transcriptRef.current = [...transcriptRef.current, turn];
        setLastLine(turn);
      }
    }
    room.on(RoomEvent.TranscriptionReceived, onTranscription);
    return () => room.off(RoomEvent.TranscriptionReceived, onTranscription);
  }, [room]);

  // Agent state messages (safe mode) arrive on the "state" topic.
  useEffect(() => {
    function onData(payload, _participant, _kind, topic) {
      if (topic !== "state") return;
      try {
        const msg = JSON.parse(new TextDecoder().decode(payload));
        if (msg.type === "safe_mode") setSafeMode(!!msg.active);
      } catch {
        /* ignore */
      }
    }
    room.on(RoomEvent.DataReceived, onData);
    return () => room.off(RoomEvent.DataReceived, onData);
  }, [room]);

  function handlePause() {
    if (paused) {
      sendControl("resume");
      setPaused(false);
    } else {
      sendControl("pause");
      setPaused(true);
    }
  }

  function handleSlower() {
    sendControl("slower");
    setSlowed(true);
  }

  function handleRestart() {
    transcriptRef.current = [];
    setLastLine(null);
    setSafeMode(false);
    setSlowed(false);
    sendControl("restart");
  }

  function handleEnd() {
    onEnd(transcriptRef.current);
  }

  function handleAgentStart() {
    setUserStarted(true);
    sendControl("agent_start");
  }

  const statusText = safeMode
    ? "Paused the scenario. No rush at all."
    : paused
    ? "Paused. Your microphone is off until you resume."
    : agentState === "listening"
    ? "Listening. Take all the time you need."
    : agentState === "thinking"
    ? "Thinking..."
    : agentState === "speaking"
    ? "Speaking..."
    : "Connecting...";

  return (
    <div className="pb-32">
      <div
        className={`rounded-xl2 border-2 p-6 ${
          safeMode ? "border-calm bg-calmsoft" : "border-mist bg-white"
        }`}
      >
        <div className="flex items-center justify-between">
          <h1 className="font-display text-lg font-semibold">{scenario.title}</h1>
          <span className="rounded-full bg-mist px-3 py-1 text-sm text-ink">{statusText}</span>
        </div>

        <p className="mt-2 text-clay">{scenario.opening_hint}</p>

        <div className="mt-6 flex h-24 items-center justify-center rounded-xl bg-paper">
          {audioTrack ? (
            <BarVisualizer
              trackRef={audioTrack}
              barCount={7}
              options={{ minHeight: 8 }}
              className="h-16 w-48 text-fern"
            />
          ) : (
            <span className="text-clay">Connecting audio...</span>
          )}
        </div>

        {!userStarted && !lastLine && (
          <div className="mt-6 text-center">
            <p className="text-clay">Speak whenever you're ready, or:</p>
            <button
              onClick={handleAgentStart}
              className="focusable mt-2 rounded-xl2 border-2 border-fern bg-white px-5 py-2 font-display font-medium text-fern"
            >
              Let them start
            </button>
          </div>
        )}

        {lastLine && (
          <div className="mt-6 rounded-xl bg-paper p-4" aria-live="polite">
            <span className="font-medium">{lastLine.speaker}: </span>
            <span>{lastLine.text}</span>
          </div>
        )}

        {safeMode && (
          <p className="mt-4 text-ink">
            The scenario has stopped. You can sit for a moment, start over, or end and
            head to feedback. Every one of those is a fine choice.
          </p>
        )}
      </div>

      <RoomAudioRenderer />
      <PaceBar
        paused={paused}
        slowed={slowed}
        onPause={handlePause}
        onSlower={handleSlower}
        onRestart={handleRestart}
        onEnd={handleEnd}
      />
    </div>
  );
}

export default function SessionView({ session, onEnd }) {
  return (
    <LiveKitRoom
      serverUrl={session.livekit_url}
      token={session.token}
      connect
      audio
      video={false}
    >
      <SessionInner scenario={session.scenario} onEnd={onEnd} />
    </LiveKitRoom>
  );
}
