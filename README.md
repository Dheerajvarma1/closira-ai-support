# Bloom Aesthetics Clinic: AI Customer Support Workflow
### SOP-Grounded Conversational Agent with Structured Escalation and Lead Qualification

---

## TL;DR

A Python CLI that handles inbound customer enquiries for an aesthetics clinic end-to-end across four stages: FAQ answering, lead qualification, escalation detection, and conversation summary.

- **7/7 scenario pass rate** across all 5 required behaviours (plus 2 sub-scenarios) verified by an automated test runner.
- **0% hallucination by design** - the AI is architecturally forbidden from answering outside the SOP; all facts are served from `sop.json`, not model weights.
- **4 escalation types** reliably detected and logged with reasons: complaint/anger, medical questions, price negotiation, and repeated out-of-scope queries.
- **Works without an API key** - a built-in demo mode (rule-based mock) runs all scenarios locally at zero cost.
- Stack: Python 3.10+, Anthropic Claude (`claude-haiku-4-5-20251001` default), no database, no framework, single file workflow.

---

## Overview

This system is built for **Closira's AI Engineering Intern assignment**. It simulates a real inbound customer support workflow for **Bloom Aesthetics Clinic** - a fictional UK aesthetics SMB offering Botox, Dermal Fillers, and free consultations.

The AI persona is **Aria** - a warm, professional front-desk assistant. Every response Aria gives is grounded strictly in `sop.json`. If a customer asks something not in the SOP, Aria says so honestly rather than inventing an answer. After two such gaps, the session escalates automatically to a human agent.

The system was designed around a core principle found in real SMB deployments: **the AI should never be the last line of defence.** It answers what it can, qualifies the lead, and hands off cleanly when it cannot help.

---

## Project Structure

```
Breakout/
|-- main.py                      # CLI entry point - all four stages in one file
|-- mock_client.py               # Demo mode: rule-based mock, no API key needed
|-- run_tests.py                 # Automated test runner for all 5 scenarios
|-- sop.json                     # The AI's only knowledge source (editable)
|-- prompt_design.md             # Full system prompt + design decisions
|-- README.md                    # This file
|-- .gitignore
|-- test_transcripts/
|   |-- 01_in_sop_question.md    # Scenario 1: Botox price answered from SOP
|   |-- 02_out_of_scope.md       # Scenario 2: OOS question triggers escalation
|   |-- 03_escalation_trigger.md # Scenario 3: Complaint / medical / negotiation
|   |-- 04_lead_qualification.md # Scenario 4: Full qualification flow
|   `-- 05_conversation_summary.md # Scenario 5: Complete session + summary
```

---

## SOP Data

The AI operates exclusively from `sop.json`. Nothing outside this file is ever used to answer a customer. This is the source of truth:

```json
{
  "business": "Bloom Aesthetics Clinic",
  "hours": "Monday to Saturday, 9:00 AM - 7:00 PM",
  "closed": "Sundays",
  "services": {
    "botox":        { "name": "Botox",                 "price_from": "from £200", "description": "Anti-wrinkle injections" },
    "fillers":      { "name": "Dermal Fillers",         "price_from": "from £250", "description": "Volume restoration and contouring" },
    "consultation": { "name": "Initial Consultation",   "price": "Free",           "description": "Full assessment before any treatment" }
  },
  "booking": {
    "channels": ["WhatsApp", "website"],
    "cancellation_policy": "24-hour notice required",
    "walk_ins": "Not guaranteed; appointments are preferred"
  },
  "escalation_triggers": [
    "Customer complaint or expressed dissatisfaction",
    "Medical questions (side effects, health risks, allergies, medications, contraindications)",
    "Pricing negotiation or discount request",
    "More than 2 questions that cannot be answered from this SOP",
    "Customer explicitly requests a human agent, manager, or real person"
  ]
}
```

**What the system derives from this file at runtime:**
- A plain-text SOP block injected verbatim into every Claude prompt
- The authoritative list of escalation trigger conditions
- All service names, prices, and descriptions used in responses

Edit `sop.json` to update the clinic. The AI picks up changes on the next run - no code changes needed.

---

## System Specifications

| Parameter | Value |
|:---|:---|
| Primary Architecture | Single-prompt conversational agent with structured JSON output |
| AI Model (default) | `claude-haiku-4-5-20251001` (overridable via `CLAUDE_MODEL`) |
| Hallucination Prevention | SOP injected inline; model instructed to use "I don't have that information" for gaps |
| Escalation Mechanism | Structured `"escalate": true` flag in every JSON response + reason string |
| Qualification Collection | State-tracked across turns; three fields: name/contact, service, urgency |
| Demo Mode | `mock_client.py` - rule-based, zero cost, zero API calls |
| Dependencies | `anthropic` only (standard library for everything else) |
| Python Version | 3.10+ (uses `str | None` union syntax) |
| Supported OS | Windows / macOS / Linux |

---

## Workflow Pipeline

> The AI returns structured JSON on every turn. Stage, escalation state, and qualification data are embedded in each response - no separate classifier call is needed.

**Stage 1 - FAQ Answering**
```
Customer message arrives
    -> Claude reads SOP block in system prompt
    -> Answers using only SOP facts
    -> Sets "confidence": "high" | "medium" | "low"
    -> If unanswered: sets "unanswered_this_turn": true
    -> After 2 unanswered turns: sets "escalate": true automatically
```

**Stage 2 - Lead Qualification**
```
After 1-2 FAQ exchanges, Claude transitions to "stage": "qualification"
    -> Q1: Name and contact number
    -> Q2: Service of interest (Botox / Fillers / Consultation)
    -> Q3: Urgency / preferred booking timeframe
    -> One question per turn (natural conversation flow)
    -> Collected fields merge into qualification_data dict across turns
```

**Stage 3 - Escalation Detection**
```
Every message is checked against 5 trigger categories (before answering):
    -> Complaint / anger       -> escalate, reason logged, handoff summary generated
    -> Medical question        -> escalate, reason logged
    -> Price negotiation       -> escalate, reason logged
    -> 2+ out-of-scope gaps    -> escalate, reason logged
    -> Explicit human request  -> escalate, reason logged
```

**Stage 4 - Conversation Summary**
```
Triggered by: session end ("quit"), customer farewell, or post-escalation handoff
    -> Separate Claude call with full conversation history
    -> Returns structured JSON: intent, key_details, sop_gaps, escalation, next_action
    -> In demo mode: built from collected qualification_data fields
```

### Response Format

Every Claude turn returns this JSON structure - no plain text, no markdown:

```json
{
  "message": "Aria's reply to the customer",
  "escalate": false,
  "escalation_reason": null,
  "confidence": "high",
  "stage": "faq",
  "qualification_data": {
    "name": null,
    "contact": null,
    "service_interest": null,
    "urgency": null
  },
  "unanswered_this_turn": false,
  "session_complete": false
}
```

This format means the orchestrator (`main.py`) reads one field to know what to do next - no regex parsing of natural language, no ambiguity.

---

## Sample Output

### Scenario 4 - Full Lead Qualification

```
================================================================
SCENARIO: 4 -- Lead Qualification (full flow)
================================================================
Aria : Hello and welcome to Bloom Aesthetics Clinic! I'm Aria, your virtual
       assistant. I can help with questions about our services, pricing, or
       booking. What can I do for you today?

You  : What services do you offer?
Aria : We offer three services at Bloom Aesthetics:
         - Botox from £200 (anti-wrinkle injections)
         - Dermal Fillers from £250 (volume and contouring)
         - Free Initial Consultation (no commitment required)
       Would you like more details on any of these?

You  : I'm interested in Botox.
Aria : Our Botox treatments start from £200 -- the exact price depends on the
       areas and units required. May I take your name and best contact number?

You  : I'm Sarah, my number is 07700 900 123
Aria : Lovely to meet you, Sarah! Which service are you most interested in --
       Botox, Dermal Fillers, or would you like to start with a free consultation?

You  : Botox please
Aria : Great choice! And how soon are you looking to come in -- within the next
       week or two, or are you planning a bit further ahead?

You  : Within the next two weeks
Aria : Wonderful, Sarah! I've noted everything down. One of our team will be in
       touch shortly to confirm your appointment.

--------------------------------------------------------------
SESSION SUMMARY
--------------------------------------------------------------
{
  "customer_intent": "Customer enquired about Botox",
  "key_details": {
    "name": "Sarah",
    "contact": "07700 900 123",
    "service_interest": "Botox",
    "urgency": "Within the next two weeks"
  },
  "sop_gaps": [],
  "escalation": { "occurred": false, "reason": null },
  "recommended_next_action": "Call Sarah on 07700 900 123 to book a Botox appointment."
}
```

### Scenario 3a - Complaint Escalation (immediate, first message)

```
You  : I came in last week and I'm really not happy with the results. This is unacceptable.
Aria : I'm so sorry to hear that -- your experience matters greatly to us.
       I'm going to connect you with a member of our team right away.

*** ESCALATION TRIGGERED ***
    Reason : Customer expressed dissatisfaction or lodged a complaint
    Action : Flagging session and routing to human agent.
```

### Scenario 2 - Out-of-Scope (escalation after 2 gaps)

```
You  : Do you offer laser hair removal?
Aria : I'm afraid that service isn't listed in the details I have. I can help
       with Botox (from £200), Dermal Fillers (from £250), and our free Initial
       Consultation. Can I help with any of those?

You  : What about skin peels?
Aria : I'm afraid I don't have information on that either. That's now two
       questions I haven't been able to answer, so let me connect you with a
       member of our team who can help properly.

*** ESCALATION TRIGGERED ***
    Reason : 2 or more questions could not be answered from the SOP
```

---

## Test Results

All 5 required assignment scenarios plus 2 sub-scenarios verified by `run_tests.py`:

| # | Scenario | What Should Happen | Result |
|:---|:---|:---|:---|
| 1 | In-SOP question (Botox + filler pricing) | Answer from SOP, no escalation | PASS |
| 2 | Out-of-scope x2 (laser, skin peels) | Escalate after 2 unanswered gaps | PASS |
| 3a | Customer complaint ("not happy", "unacceptable") | Escalate immediately | PASS |
| 3b | Medical question (blood thinners + Botox) | Escalate immediately | PASS |
| 3c | Price negotiation ("can you do it cheaper") | Escalate immediately | PASS |
| 4 | Full lead qualification (name, service, urgency) | Collect all 3 fields, no escalation | PASS |
| 5 | Complete session with structured summary (James, Dermal Fillers) | Full session + JSON summary, no escalation | PASS |

**7 / 7 PASS - 0 failures**

Run it yourself (no API key needed):
```bash
python run_tests.py
```

---

## Escalation Logic

Escalation is detected in two ways and is never missed:

### Trigger 1 - Explicit flag in JSON output

Claude sets `"escalate": true` with a populated `"escalation_reason"` string whenever a trigger condition is detected. The orchestrator checks this field on every single turn. It does not parse the message text for escalation - it reads one boolean field.

| Trigger Category | Example Phrase | Action |
|:---|:---|:---|
| Complaint / anger | "not happy", "terrible", "unacceptable", "upset" | Immediate escalation |
| Medical question | "side effects", "blood thinners", "allergic", "safe for me" | Immediate escalation |
| Price negotiation | "can you do it cheaper", "any discount", "better price" | Immediate escalation |
| Out-of-scope (x2) | Two questions not answerable from SOP | Escalation on second gap |
| Human requested | "speak to a real person", "manager", "human" | Immediate escalation |

### Trigger 2 - Unanswered question counter

The `"unanswered_this_turn": true` flag increments a counter in `SupportSession`. After 2 increments, the next response forces `escalate: true` regardless of what the model returns. This is a code-level safety net - the model cannot loop indefinitely on out-of-scope questions.

### On escalation

1. The conversation halts immediately - no further customer messages are processed
2. The escalation reason is printed clearly in the CLI
3. `generate_summary()` is called automatically to produce a handoff context for the human agent
4. The session log contains every turn with timestamps, stage, confidence, and escalation fields

---

## Hallucination Prevention

Three layers work together to ensure Aria never invents facts:

**Layer 1 - Hard instruction**

The system prompt opens with:

> "Answer ONLY from the SOP data above. Never invent facts, prices, or details not in the SOP. If asked something not covered by the SOP, say clearly: 'I don't have that information.' Do NOT guess."

The word "ONLY" and absolute negatives ("Never", "Do NOT") are deliberate. Softer language ("prefer to", "try to") leaves the model room to rationalise exceptions.

**Layer 2 - Prescribed fallback phrase**

Rather than leaving Claude to improvise a gap response, the prompt specifies the exact phrase: *"I don't have that information."* A concrete fallback removes the incentive to fill gaps with plausible-sounding guesses.

**Layer 3 - Escalation after 2 gaps**

The system does not allow the model to keep deflecting indefinitely. After two unanswered questions, the session escalates. This means the model is never in a position where deflecting forever becomes a tempting alternative to hallucinating.

---

## Design Decisions

### Why structured JSON output instead of plain text?

Every Claude response is a JSON object. The orchestrator reads fields, not sentences. This means:
- Escalation is a boolean check, not sentiment parsing
- Stage transitions are explicit, not inferred
- Qualification data is carried forward reliably across turns
- No fragile regex or NLP is needed in `main.py`

The tradeoff: Claude must be reliably prompted to return only JSON. `extract_json()` in `main.py` handles the rare case where the model wraps the output in markdown code fences.

### Why embed the SOP inline in the system prompt?

The SOP is under 300 tokens - small enough to embed directly. This means:
- The model sees the SOP on every single turn with no retrieval step
- No vector search, no database, no failure modes from retrieval
- The boundary between "what I can answer" and "what I cannot" is always in context

For a larger SOP (hundreds of pages), the right approach would be RAG + citation requirement. At SMB scale, inline embedding is simpler and more reliable.

### Why a staged conversation flow (FAQ -> Qualification -> Summary)?

Rather than letting Claude decide when to qualify, the prompt defines explicit stages. This ensures:
- Qualification always happens - it cannot be skipped if the customer asks many questions
- The AI does not pivot to sales before establishing trust through FAQ exchanges
- The orchestrator always knows which stage it is in from the `"stage"` field

### Why British English?

The clinic is UK-based (prices in GBP). The prompt specifies British English - "enquiry" not "inquiry", "practitioner" not "provider", "colour" not "color". Small detail, but it signals attention to the product context the assignment asks for.

---

## Architecture

```
main.py (CLI + SupportSession)
    |
    |-- SupportSession.chat()
    |       |-- Appends user message to history
    |       |-- Calls client.messages.create() with full history + system prompt
    |       |-- Parses JSON response via extract_json()
    |       |-- Updates stage, unanswered_count, qualification_data
    |       |-- Logs every turn with timestamp and metadata
    |       `-- Returns parsed dict to main loop
    |
    |-- SupportSession.generate_summary()
    |       |-- Sends full conversation history + summary prompt
    |       `-- Returns structured JSON summary dict
    |
    `-- client (one of two):
            |-- Anthropic()         <- when ANTHROPIC_API_KEY is set
            `-- MockAI()            <- when no key is present (demo mode)

sop.json -> loaded once at startup -> build_sop_text() -> injected into SYSTEM_PROMPT constant
```

### Demo Mode vs Real Mode

`main.py` selects the client at startup based on one environment variable:

```python
has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
if has_key and _Anthropic is not None:
    self.client = _Anthropic()   # real Claude API
else:
    self.client = MockAI()       # local rule-based mock
```

`MockAI` in `mock_client.py` implements the same interface as the Anthropic client (`client.messages.create(...)`). No other code in `main.py` changes. Switching between modes is a single environment variable - not a code change.

---

## Installation

**1. Clone / download the repository**

**2. Install the one dependency:**
```bash
pip install anthropic
```

**3. (Optional) Set your API key for real Claude responses:**

Windows PowerShell:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

Mac / Linux:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

If you skip step 3, the system runs in demo mode automatically - no error, no prompt.

**4. (Optional) Choose a different Claude model:**
```powershell
$env:CLAUDE_MODEL = "claude-sonnet-4-6"
```

Default is `claude-haiku-4-5-20251001` - fast and cost-effective for a support workflow.

---

## How to Verify the System is Working

**Check 1 - Run all 5 scenarios automatically (no API key needed)**
```bash
python run_tests.py
```
Expected: 7 scenarios complete, all print `Result: PASS`. Takes under 2 seconds.

**Check 2 - Run the interactive CLI (demo mode)**
```bash
python main.py
```
Expected: Aria greets you, answers questions from SOP, transitions to qualification, escalates on trigger phrases. Try typing "I'm not happy with my last visit" and watch it escalate immediately.

**Check 3 - Run the interactive CLI (real Claude)**
```bash
# Set ANTHROPIC_API_KEY first, then:
python main.py
```
Expected: Same behaviour as demo mode but responses are generated by Claude. Type `quit` to end and see the structured JSON summary.

**Check 4 - Quick syntax check (no dependencies needed)**
```bash
python -c "import ast; ast.parse(open('main.py', encoding='utf-8').read()); print('OK')"
python -c "import json; json.load(open('sop.json', encoding='utf-8')); print('OK')"
```
Expected: Both print `OK`.

---

## Performance Expectations

| Operation | Time | Notes |
|:---|:---|:---|
| Demo mode (all 7 scenarios) | < 2 seconds | Rule-based, no API, no network |
| Real Claude (per turn, haiku) | 1-3 seconds | Depends on network and Anthropic load |
| Real Claude (summary generation) | 2-4 seconds | Larger prompt due to full history |
| Startup / SOP loading | < 0.1 seconds | JSON file read + string formatting |

There is no caching layer in this implementation. Identical questions in the same session will make fresh API calls. For a production system, SHA-256 prompt caching would reduce repeat costs to zero.

---

## Trade-offs and Known Limitations

| Area | Limitation | What a Production Version Would Do |
|:---|:---|:---|
| SOP size | Inline embedding works at < 1,000 tokens. A multi-page SOP would overflow context. | RAG over a vector-indexed SOP with citation requirement |
| Qualification state | State lives in `SupportSession` memory only. Closing the terminal loses it. | Persist session to SQLite or Redis with a session ID |
| Demo mode accuracy | Mock uses keyword matching - it can be fooled by rephrasing. | Not relevant once a real API key is used |
| No streaming | Responses arrive in full. On slow connections, there is a pause before each reply. | `client.messages.stream()` for character-by-character output |
| English only | System prompt and SOP are English. Customers writing in other languages get English responses. | Translated system prompts per locale |
| Single-pane CLI | No UI, no WhatsApp integration, no email connector. | Wrap `SupportSession` in a webhook handler for Twilio / WhatsApp Business API |
| No test for hallucination at runtime | Demo mode can't hallucinate by design. Real Claude hallucination would require a grounding checker on each response. | Value-level field checker: verify every fact Claude cites against `sop.json` |

---

## What This System Does Not Do (Intentionally)

- It does not answer medical questions. Ever. This is a hard rule, not a soft suggestion.
- It does not negotiate prices. Pricing decisions belong to a human.
- It does not make promises about treatment outcomes.
- It does not guess. If it does not know, it says so.

These are not limitations - they are deliberate constraints that make the system safe to deploy in a real customer-facing role without supervision.

---

## Files Reference

| File | Purpose |
|:---|:---|
| `main.py` | Entry point. `SupportSession` class, CLI loop, `extract_json()` helper. |
| `mock_client.py` | `MockAI` class. Implements `messages.create()` with rule-based responses. Used when no API key is set. |
| `run_tests.py` | Automated test runner. Replays all 7 scenarios and prints PASS / FAIL per scenario. |
| `sop.json` | The clinic's SOP data. The AI's only allowed knowledge source. |
| `prompt_design.md` | Full system prompt text + reasoning for every major design decision. |
| `test_transcripts/` | One markdown file per required scenario. Shows expected input, output, escalation behaviour, and a verification checklist. |
