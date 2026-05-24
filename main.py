#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bloom Aesthetics Clinic - AI Customer Support Workflow
Powered by Anthropic Claude (Aria)

Stages: FAQ Answering -> Lead Qualification -> Escalation Detection -> Conversation Summary
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from mock_client import MockAI

try:
    from anthropic import Anthropic as _Anthropic
except ImportError:
    _Anthropic = None

# --- Load SOP ------------------------------------------------------------------

SOP_PATH = Path(__file__).parent / "sop.json"
with open(SOP_PATH, encoding="utf-8") as f:
    SOP = json.load(f)


def build_sop_text(sop: dict) -> str:
    """Convert the SOP dict into a plain-text block for the system prompt."""
    services = "\n".join(
        "  - {name}: {price} -- {desc}".format(
            name=v["name"],
            price=v.get("price_from", v.get("price", "N/A")),
            desc=v["description"],
        )
        for v in sop["services"].values()
    )
    triggers = "\n".join("  - " + t for t in sop["escalation_triggers"])
    channels = ", ".join(sop["booking"]["channels"])
    return (
        "BUSINESS: {business}\n"
        "HOURS: {hours} (Closed {closed})\n\n"
        "SERVICES & PRICING:\n{services}\n\n"
        "BOOKING:\n"
        "  - Channels: {channels}\n"
        "  - Cancellation: {cancel}\n"
        "  - Walk-ins: {walkins}\n\n"
        "ESCALATE IMMEDIATELY IF:\n{triggers}"
    ).format(
        business=sop["business"],
        hours=sop["hours"],
        closed=sop["closed"],
        services=services,
        channels=channels,
        cancel=sop["booking"]["cancellation_policy"],
        walkins=sop["booking"]["walk_ins"],
        triggers=triggers,
    )


SOP_TEXT = build_sop_text(SOP)

# --- System Prompt -------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are Aria, a warm and professional AI assistant for Bloom Aesthetics Clinic.\n"
    "You handle inbound customer enquiries via chat on behalf of the clinic.\n\n"
    "==================================================\n"
    "SOP DATA -- YOUR ONLY KNOWLEDGE SOURCE\n"
    "==================================================\n"
    + SOP_TEXT
    + "\n"
    "==================================================\n\n"
    "STRICT RULES:\n"
    '1. Answer ONLY from the SOP data above. Never invent facts, prices, or details not in the SOP.\n'
    '2. If asked something not covered by the SOP, say clearly: "I don\'t have that information."\n'
    "   Do NOT guess or make anything up.\n"
    "3. Track unanswered questions internally. After 2 questions you cannot answer, escalate.\n"
    "4. Use warm, professional British English. Keep replies concise (2-4 sentences max).\n"
    "5. Never provide medical advice under any circumstances.\n\n"
    "CONVERSATION STAGES:\n"
    "Stage 1 -- FAQ: Answer questions directly from SOP data.\n"
    "Stage 2 -- QUALIFICATION: After 1-2 FAQ exchanges, transition naturally and collect info\n"
    "  one question at a time:\n"
    '  Q1: "May I take your name and best contact number?"\n'
    '  Q2: "Which service are you most interested in -- Botox, Fillers, or a free consultation?"\n'
    '  Q3: "How soon are you looking to book?"\n'
    "Stage 3 -- SUMMARY: When all qualification questions are answered or the customer is done.\n\n"
    'ESCALATION TRIGGERS -- set "escalate": true immediately if ANY of these occur:\n'
    '- Complaint, dissatisfaction, or anger (e.g. "not happy", "terrible", "ridiculous", "upset")\n'
    "- Any medical question (side effects, risks, allergies, medications, contraindications)\n"
    '- Price negotiation or discount request (e.g. "can you do it cheaper", "any deals")\n'
    "- 2 or more questions that cannot be answered from the SOP\n"
    "- Customer asks for a human, manager, or real person\n\n"
    "RESPONSE FORMAT -- return ONLY valid JSON. No markdown, no extra text, just the JSON object:\n"
    "{\n"
    '  "message": "Your reply to the customer",\n'
    '  "escalate": false,\n'
    '  "escalation_reason": null,\n'
    '  "confidence": "high",\n'
    '  "stage": "faq",\n'
    '  "qualification_data": {\n'
    '    "name": null,\n'
    '    "contact": null,\n'
    '    "service_interest": null,\n'
    '    "urgency": null\n'
    "  },\n"
    '  "unanswered_this_turn": false,\n'
    '  "session_complete": false\n'
    "}\n\n"
    "Field notes:\n"
    '- confidence: "high" = clear SOP answer | "medium" = partial info | "low" = must escalate\n'
    '- stage: "faq" | "qualification" | "summary" | "escalated"\n'
    "- unanswered_this_turn: true if the customer asked something not in the SOP this turn\n"
    "- session_complete: true when qualification is fully collected and customer seems satisfied\n"
    "- qualification_data: carry forward all collected values each turn (do not reset to null)\n"
)

# --- Helpers -------------------------------------------------------------------


def extract_json(text: str) -> dict:
    """Parse JSON from model response, handling markdown code blocks or surrounding text."""
    text = text.strip()
    # Strip markdown code fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract first JSON object found in text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No valid JSON found in model response: " + text[:200])


# --- Session -------------------------------------------------------------------


class SupportSession:
    """Manages a single customer support conversation."""

    def __init__(self):
        model = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
        if has_key and _Anthropic is not None:
            self.client = _Anthropic()
            self.demo_mode = False
        else:
            self.client = MockAI()
            self.demo_mode = True
        self.model = "demo-mode (no API key)" if self.demo_mode else model
        self.history: list[dict] = []
        self.stage = "faq"
        self.escalated = False
        self.escalation_reason: str | None = None
        self.qualification_data = {
            "name": None,
            "contact": None,
            "service_interest": None,
            "urgency": None,
        }
        self.unanswered_count = 0
        self.log: list[dict] = []

    def chat(self, user_message: str) -> dict:
        """Send a user message and return the parsed AI response."""
        self.history.append({"role": "user", "content": user_message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=self.history,
        )

        raw = response.content[0].text

        try:
            parsed = extract_json(raw)
        except (ValueError, json.JSONDecodeError):
            # Graceful fallback: treat raw text as the reply message
            parsed = {
                "message": raw,
                "escalate": False,
                "escalation_reason": None,
                "confidence": "medium",
                "stage": self.stage,
                "qualification_data": {},
                "unanswered_this_turn": False,
                "session_complete": False,
            }

        self.history.append({"role": "assistant", "content": raw})

        # Update session state
        if parsed.get("escalate"):
            self.escalated = True
            self.stage = "escalated"
            self.escalation_reason = parsed.get("escalation_reason")
        elif parsed.get("stage"):
            self.stage = parsed["stage"]

        if parsed.get("unanswered_this_turn"):
            self.unanswered_count += 1

        # Merge qualification data (preserve previously collected values)
        qd = parsed.get("qualification_data") or {}
        for key, value in qd.items():
            if value and key in self.qualification_data:
                self.qualification_data[key] = value

        self.log.append(
            {
                "ts": datetime.now().isoformat(),
                "user": user_message,
                "aria": parsed.get("message", ""),
                "stage": self.stage,
                "confidence": parsed.get("confidence"),
                "escalate": parsed.get("escalate", False),
                "escalation_reason": parsed.get("escalation_reason"),
            }
        )

        return parsed

    def generate_summary(self) -> dict:
        """Generate a structured end-of-session summary."""
        prompt = (
            "The session has ended. Generate a structured summary. "
            "Qualification data collected so far: "
            + json.dumps(self.qualification_data)
            + ". Session escalated: "
            + str(self.escalated)
            + ". Escalation reason: "
            + str(self.escalation_reason)
            + ". Total customer messages: "
            + str(len(self.log))
            + ". Unanswered questions count: "
            + str(self.unanswered_count)
            + ".\n"
            "Return ONLY valid JSON in this exact format:\n"
            "{\n"
            '  "customer_intent": "...",\n'
            '  "key_details": {"name": null, "contact": null, "service_interest": null, "urgency": null},\n'
            '  "sop_gaps": [],\n'
            '  "escalation": {"occurred": false, "reason": null},\n'
            '  "recommended_next_action": "..."\n'
            "}"
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=self.history + [{"role": "user", "content": prompt}],
        )

        try:
            return extract_json(response.content[0].text)
        except (ValueError, json.JSONDecodeError):
            return {"raw_summary": response.content[0].text}


# --- CLI -----------------------------------------------------------------------


def print_bar(char: str = "-", width: int = 62) -> None:
    print(char * width)


def print_summary(data: dict) -> None:
    print()
    print_bar()
    print("SESSION SUMMARY")
    print_bar()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print_bar()


def main() -> None:
    session = SupportSession()

    print()
    print_bar("=")
    print("  BLOOM AESTHETICS CLINIC -- AI Customer Support")
    if session.demo_mode:
        print("  Powered by Aria  |  *** DEMO MODE (no API key) ***")
    else:
        print("  Powered by Aria  |  Model: " + session.model)
    print_bar("=")
    print("  Commands: 'summary' -- view session summary | 'quit' -- end session")
    print_bar()
    print()

    # Opening greeting
    opening = session.chat("Hello, I'd like some information about your clinic.")
    print("Aria: " + opening["message"] + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession interrupted.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            data = session.generate_summary()
            print_summary(data)
            break

        if user_input.lower() == "summary":
            data = session.generate_summary()
            print_summary(data)
            continue

        result = session.chat(user_input)
        print("\nAria: " + result["message"] + "\n")

        if result.get("escalate"):
            reason = result.get("escalation_reason") or "Not specified"
            print("*** ESCALATION TRIGGERED ***")
            print("    Reason  : " + reason)
            print("    Action  : Flagging session and routing to human agent.\n")
            data = session.generate_summary()
            print_summary(data)
            break

        if result.get("session_complete"):
            data = session.generate_summary()
            print_summary(data)
            break


if __name__ == "__main__":
    main()
