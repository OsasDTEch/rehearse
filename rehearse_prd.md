# PRD: Rehearse
### A judgment free voice practice space for real life conversations
**Track 2: AI for Connection and Wellbeing | IncludAI Neurodiversity Hackathon**
**Version 1.0 | Deadline: Saturday Aug 8, 2026, 11:59 PM PT**

---

## 1. Problem

Many autistic and socially anxious young people find everyday conversations (ordering food, asking a teacher for help, joining a group chat at lunch) stressful because the interaction is unpredictable, fast, and carries social cost if it goes wrong. There is no safe place to practice. Roleplay with a parent or therapist feels artificial and is not available on demand. Text based chatbots miss the hardest part: the real time pressure of speaking and listening.

## 2. Solution

A voice agent that plays the other person in a chosen scenario, at the user's pace, with zero judgment and zero social cost. The user can pause, slow down, restart, or bail out at any moment. After the roleplay, the agent gives short, concrete, kind feedback: one thing that went well, one thing to try next time.

The core design promise: **the user controls the pace of the conversation, always.** The tool adapts to the user, never the reverse.

## 3. Target users

Primary: autistic teens and young adults (13 to 22) who want to rehearse everyday social scenarios privately before doing them for real.
Secondary: anyone with social anxiety or ADHD related conversation difficulties (interrupting, losing thread mid sentence).

## 4. Core user flow (MVP)

1. **Pick a scenario** from a small curated list (no free text needed to start):
   - Ordering at a restaurant
   - Asking a teacher for an extension
   - Joining a conversation with classmates
   - Returning an item to a shop
   - Phone call to book an appointment
2. **Set the mood dial**: how does the other person act? Friendly / Neutral / A bit impatient. (Lets users gradually increase difficulty.)
3. **Voice roleplay.** The agent stays in character. Latency under 2 seconds so it feels like a real conversation.
4. **User controls, available at all times, on screen and by voice:**
   - Pause ("give me a second")
   - Slow down (agent speaks slower, uses shorter sentences)
   - Restart scenario
   - End and get feedback
5. **Feedback screen.** Two or three short bullets, always framed positively. Never a score, never a grade. Transcript available but collapsed by default.

## 5. Safety design (enforced in code, not left to the LLM)

- **Distress tripwire.** A keyword and pattern watcher runs on the user's transcript in code, before the LLM turn. Phrases indicating overload or distress ("stop", "I can't do this", "too much", extended silence after prompting) immediately switch the session into de escalation mode: agent drops the character, speaks slowly and briefly, offers to pause or end. The LLM never gets the chance to stay in character past a distress signal.
- **No character cruelty ceiling.** Even on "a bit impatient", the system prompt hard caps the persona: mild impatience only, no insults, no raised voice simulation. The mood dial changes realism, not hostility.
- **Session privacy.** No accounts required for the demo. Transcripts stay local to the session unless the user opts to save.

## 6. Accessibility requirements (this is the product, not a feature)

- Camera never required. Voice only, or voice plus minimal UI.
- Every voice control also has a visible button (motor and processing flexibility).
- Plain language everywhere. No idioms in UI copy.
- Predictability: the agent never opens with a surprise. The user always speaks first, or explicitly taps "you start".
- Sensory friendly UI: muted colors, no animation, no autoplay sounds, generous spacing, dyslexia friendly font option.
- Adjustable speech rate for the agent's voice.

## 7. Neurodivergent user involvement (hackathon hard requirement)

- Recruit at least one neurodivergent tester from the hackathon Discord on day one.
- Run one structured session before feature freeze: they pick a scenario, use it for real, think aloud.
- Capture verbatim quotes. Make at least two visible changes based on their feedback and document before/after in the submission.
- Invite the tester to appear (voice only is fine) in the demo video if they are comfortable.

## 8. Technical architecture

Reuse of existing production voice stack, adapted:

| Layer | Choice | Notes |
|---|---|---|
| Voice session | LiveKit Agents | Same pattern as HeatDesk |
| STT / TTS | Deepgram (Flux endpointing) | Endpointing already tuned |
| LLM | Ollama Cloud primary, fallback model configured | Persona prompt per scenario |
| Safety layer | Python keyword/pattern tripwire before LLM turn | Same pattern as HeatDesk emergency escalation |
| Backend | FastAPI + SQLite | Scenario configs stored as data, not code |
| Frontend | React (Vite, Tailwind) | Single page: scenario picker → session → feedback |
| Feedback generation | Separate LLM call on transcript at session end | Prompted for two positives max one suggestion |

Config as data: scenarios, personas, mood dials, and tripwire phrase lists live in config, so adding a scenario is a data change.

## 9. MVP scope for 48 hours

**In:**
- 3 scenarios fully working (restaurant, teacher, joining classmates)
- Mood dial with 2 settings (friendly, neutral)
- Pause, restart, end controls (buttons + voice)
- Distress tripwire with de escalation mode
- Feedback screen
- Deployed live at a public URL

**Out (say so in the README as roadmap):**
- Accounts, saved history, progress tracking
- Impatient mood setting (needs more tester validation first)
- Custom scenario builder
- Multiple languages

## 10. Success criteria (mapped to judging)

- **Impact (30%):** real tester used it, their words and the resulting changes are in the submission.
- **Innovation / usability by neurodivergent users (25%):** pace controls, predictability rules, sensory friendly UI, safety tripwire in code.
- **Technical execution (10%):** live deployed demo, clean public repo, working voice loop under 2s latency.
- **Presentation (10%):** 3 minute video showing a real session, ideally with the tester.

## 11. Deliverables checklist (due Sat 11:59 PM PT)

- [ ] Demo video, 3 min max, on YouTube, linked on Devpost
- [ ] Devpost description: problem, users, meaningful AI use, tester involvement story
- [ ] Public GitHub repo
- [ ] Live demo URL in the README

## 12. 48 hour timeline

**Today (Thu/Fri):** register correctly, join Discord, post for a tester, strip HeatDesk skeleton into scenario roleplay, one scenario working end to end by tonight.
**Saturday morning:** tester session, capture feedback, make two visible changes.
**Saturday afternoon:** remaining scenarios, feedback screen polish, deploy.
**Saturday evening:** record video, clean repo, write Devpost description, submit with buffer before 11:59 PM PT.
