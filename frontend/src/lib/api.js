const BASE = import.meta.env.VITE_API_BASE || "";

export async function getScenarios() {
  const r = await fetch(`${BASE}/api/scenarios`);
  if (!r.ok) throw new Error("Could not load scenarios");
  return r.json();
}

export async function startSession(scenarioId, mood) {
  const r = await fetch(`${BASE}/api/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId, mood }),
  });
  if (!r.ok) throw new Error("Could not start the session");
  return r.json();
}

export async function getFeedback(scenarioId, transcript) {
  const r = await fetch(`${BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId, transcript }),
  });
  if (!r.ok) throw new Error("Could not generate feedback");
  return r.json();
}
