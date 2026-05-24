#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock Claude client for testing without an API key.
Simulates all four workflow stages using rule-based keyword matching.
"""

import json
import re

# ---------------------------------------------------------------------------
# Common English words that should never be treated as customer names
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were", "be",
    "do", "does", "did", "will", "would", "shall", "should", "may", "might",
    "can", "could", "what", "which", "who", "how", "when", "where", "why",
    "this", "that", "these", "those", "my", "your", "his", "her", "its",
    "yes", "no", "not", "so", "very", "also", "just", "much", "any",
    "some", "all", "both", "each", "other", "same", "than", "then",
    "i", "me", "you", "he", "she", "we", "they", "it", "about",
    "hi", "hello", "hey", "ok", "okay", "sure", "great", "good", "nice",
    "please", "thanks", "thank", "sorry", "excuse",
}

# ---------------------------------------------------------------------------
# Keyword groups
# ---------------------------------------------------------------------------

# Use word-boundary matching for escalation triggers (avoids "deal" matching "ideally")
_COMPLAINT = [
    "not happy", "unhappy", "terrible", "awful", "ridiculous",
    "upset", "angry", "complaint", "unacceptable", "disgusting",
    "disappointed", "horrible", "furious",
]
_MEDICAL = [
    "side effect", "allerg", "contraindic", "safe for",
    "blood thin", "pregnant", "health condition", "health risk",
    "injection risk",
]
_NEGOTIATE = [
    "cheaper", "discount", "any deal", "better price", "negotiate",
    "lower price", "any offer", "can you do it for",
]
_HUMAN = [
    "human", "real person", "manager", "speak to someone",
    "actual person", "real agent", "supervisor",
]

# Services not covered by the SOP (checked before generic FAQ keywords)
_OUT_OF_SCOPE = [
    "laser", "hair removal", "skin peel", "tattoo", "piercing",
    "massage", "waxing", "threading", "tanning", "microdermabrasion",
    "teeth whitening",
]

# ---------------------------------------------------------------------------
# Matching helpers
# ---------------------------------------------------------------------------


def _hit(text: str, keywords: list) -> bool:
    """Word-boundary aware match - safe for escalation triggers."""
    for kw in keywords:
        if " " in kw:
            # Multi-word phrase: substring match is specific enough
            if kw in text:
                return True
        else:
            # Single word: require boundaries so "deal" won't match "ideally"
            if re.search(r"\b" + re.escape(kw) + r"\b", text):
                return True
    return False


def _sub(text: str, keywords: list) -> bool:
    """Simple substring match - used for FAQ topic detection."""
    return any(kw in text for kw in keywords)


def _extract_name(raw: str) -> str | None:
    """Extract a probable customer name from free text, ignoring stop words."""
    # Explicit "my name is X" or "I'm X" patterns are most reliable
    m = re.search(
        r"(?:i'm|i am|name is|call me|it's)\s+([A-Za-z]+)", raw, re.IGNORECASE
    )
    if m:
        word = m.group(1).capitalize()
        if word.lower() not in _STOPWORDS:
            return word

    # Otherwise: first capitalised word that isn't a stop word
    for word in raw.split():
        clean = word.strip(".,!?\"'")
        if (
            clean
            and clean[0].isupper()
            and not clean[0].isdigit()
            and len(clean) > 1
            and clean.lower() not in _STOPWORDS
        ):
            return clean
    return None


def _extract_phone(raw: str) -> str | None:
    m = re.search(r"(\d[\d\s\-]{8,14}\d)", raw)
    return m.group(1).strip() if m else None


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


class _Content:
    def __init__(self, text: str) -> None:
        self.text = text


class _Response:
    def __init__(self, text: str) -> None:
        self.content = [_Content(text)]


def _make(
    message: str,
    escalate: bool = False,
    escalation_reason: str | None = None,
    confidence: str = "high",
    stage: str = "faq",
    name=None,
    contact=None,
    service=None,
    urgency=None,
    unanswered: bool = False,
    complete: bool = False,
) -> _Response:
    data = {
        "message": message,
        "escalate": escalate,
        "escalation_reason": escalation_reason,
        "confidence": confidence,
        "stage": "escalated" if escalate else stage,
        "qualification_data": {
            "name": name,
            "contact": contact,
            "service_interest": service,
            "urgency": urgency,
        },
        "unanswered_this_turn": unanswered,
        "session_complete": complete,
    }
    return _Response(json.dumps(data))


# ---------------------------------------------------------------------------
# MockMessages (mimics anthropic client.messages interface)
# ---------------------------------------------------------------------------


class MockMessages:
    def __init__(self, state: "MockAI") -> None:
        self._s = state

    def create(self, model, max_tokens, system, messages) -> _Response:
        last = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
        )
        return self._s._respond(last, messages)


# ---------------------------------------------------------------------------
# MockAI
# ---------------------------------------------------------------------------


class MockAI:
    """
    Drop-in replacement for anthropic.Anthropic() when no API key is available.
    Returns rule-based JSON responses in the same shape as the real Claude.
    """

    def __init__(self) -> None:
        self.messages = MockMessages(self)
        self._faq_count = 0
        self._qa_step = 0      # 0=not started 1=name/contact 2=service 3=urgency 4=done
        self._unanswered = 0
        self._name: str | None = None
        self._contact: str | None = None
        self._service: str | None = None
        self._urgency: str | None = None

    # ------------------------------------------------------------------
    # Internal shortcuts
    # ------------------------------------------------------------------

    def _q(self, **kwargs) -> _Response:
        """Return a response carrying the current qualification state."""
        return _make(
            name=self._name,
            contact=self._contact,
            service=self._service,
            urgency=self._urgency,
            **kwargs,
        )

    def _ask_name(self, preamble: str = "") -> _Response:
        self._qa_step = 1
        prefix = preamble.rstrip() + " " if preamble else ""
        return self._q(
            message=prefix + "May I take your name and best contact number so we can follow up?",
            stage="qualification",
        )

    def _ask_service(self) -> _Response:
        self._qa_step = 2
        greeting = ("Lovely to meet you, " + self._name + "! ") if self._name else ""
        return self._q(
            message=(
                greeting
                + "Which service are you most interested in -- "
                "Botox, Dermal Fillers, or would you like to start with a free consultation?"
            ),
            stage="qualification",
        )

    def _ask_urgency(self) -> _Response:
        self._qa_step = 3
        return self._q(
            message=(
                "Great choice! And how soon are you looking to come in -- "
                "within the next week or two, or are you planning a bit further ahead?"
            ),
            stage="qualification",
        )

    def _wrap_up(self) -> _Response:
        self._qa_step = 4
        greeting = ("Wonderful, " + self._name + "! ") if self._name else "Wonderful! "
        return self._q(
            message=(
                greeting
                + "I've noted everything down. One of our team will be in touch shortly "
                "to confirm your appointment. Do remember we're open Mon-Sat 9 am-7 pm "
                "and we ask for 24 hours' notice for cancellations. "
                "Is there anything else I can help with?"
            ),
            stage="qualification",
        )

    # ------------------------------------------------------------------
    # Main responder
    # ------------------------------------------------------------------

    def _respond(self, raw: str, messages: list) -> _Response:
        txt = raw.lower()

        # Summary prompt (called internally by generate_summary)
        if "session has ended" in txt or "generate a structured summary" in txt:
            return self._build_summary()

        # Opening greeting
        if txt.strip() in (
            "hello, i'd like some information about your clinic.",
            "hello", "hi", "hey", "good morning", "good afternoon",
        ):
            return self._q(
                message=(
                    "Hello and welcome to Bloom Aesthetics Clinic! "
                    "I'm Aria, your virtual assistant. "
                    "I can help with questions about our services, pricing, or booking. "
                    "What can I do for you today?"
                ),
                stage="faq",
            )

        # ---- Escalation triggers (highest priority) ------------------
        if _hit(txt, _COMPLAINT):
            return self._q(
                message=(
                    "I'm so sorry to hear that -- your experience matters greatly to us. "
                    "I'm going to connect you with a member of our team right away."
                ),
                escalate=True,
                escalation_reason="Customer expressed dissatisfaction or lodged a complaint",
            )

        if _hit(txt, _MEDICAL):
            return self._q(
                message=(
                    "That's an important question and your safety is our top priority. "
                    "I'm not able to give medical advice, so let me connect you with "
                    "one of our qualified practitioners who can answer that properly."
                ),
                escalate=True,
                escalation_reason="Customer asked a medical question",
            )

        if _hit(txt, _NEGOTIATE):
            return self._q(
                message=(
                    "I understand pricing is an important factor! "
                    "Pricing decisions aren't something I'm able to discuss directly, "
                    "but I'll connect you with our team who can help further."
                ),
                escalate=True,
                escalation_reason="Customer requested a discount or price negotiation",
            )

        if _hit(txt, _HUMAN):
            return self._q(
                message="Of course! Let me connect you with one of our team members right away.",
                escalate=True,
                escalation_reason="Customer explicitly requested a human agent",
            )

        # ---- Qualification state machine ----------------------------
        if self._qa_step == 1:
            self._name = _extract_name(raw) or self._name
            self._contact = _extract_phone(raw) or self._contact
            return self._ask_service()

        if self._qa_step == 2:
            if _sub(txt, ["botox"]):
                self._service = "Botox"
            elif _sub(txt, ["filler"]):
                self._service = "Dermal Fillers"
            elif _sub(txt, ["consult"]):
                self._service = "Free Consultation"
            else:
                self._service = raw.strip()
            return self._ask_urgency()

        if self._qa_step == 3:
            self._urgency = raw.strip()
            return self._wrap_up()

        # ---- Goodbye / done ----------------------------------------
        if _hit(txt, ["bye", "goodbye"]) or _sub(
            txt, ["that's all", "that's everything", "nope", "nothing else", "no, that", "thank you, bye"]
        ):
            greeting = ("It was a pleasure chatting with you, " + self._name + "! ") if self._name else "It was a pleasure! "
            return self._q(
                message=(
                    greeting
                    + "We look forward to welcoming you to Bloom Aesthetics. "
                    "Have a lovely day!"
                ),
                stage="summary",
                complete=True,
            )

        # ---- Out-of-scope services (before generic FAQ keywords) ----
        if _sub(txt, _OUT_OF_SCOPE):
            self._unanswered += 1
            if self._unanswered >= 2:
                return self._q(
                    message=(
                        "I'm afraid I don't have information on that either. "
                        "That's now two questions I haven't been able to answer, "
                        "so let me connect you with a member of our team who can help properly."
                    ),
                    escalate=True,
                    escalation_reason="2 or more questions could not be answered from the SOP",
                    confidence="low",
                    unanswered=True,
                )
            return self._q(
                message=(
                    "I'm afraid that service isn't listed in the details I have. "
                    "I can help with Botox (from £200), Dermal Fillers (from £250), "
                    "and our free Initial Consultation. Can I help with any of those?"
                ),
                confidence="low",
                unanswered=True,
                stage="faq",
            )

        # ---- FAQ answers (substring match is fine here) -------------
        if _sub(txt, ["botox", "anti-wrinkle", "wrinkle"]):
            self._faq_count += 1
            if self._faq_count >= 2 and self._qa_step == 0:
                return self._ask_name(
                    "Our Botox treatments start from £200 -- the exact price depends on "
                    "the areas and units required."
                )
            return self._q(
                message=(
                    "Our Botox treatments start from £200. "
                    "The exact price depends on the areas being treated and the units required. "
                    "A free initial consultation lets our practitioner give you a personalised plan. "
                    "Would you like to know how to book?"
                ),
                stage="faq",
            )

        if _sub(txt, ["filler", "lip", "cheek", "jaw", "volume"]):
            self._faq_count += 1
            if self._faq_count >= 2 and self._qa_step == 0:
                return self._ask_name(
                    "Dermal Fillers start from £250 -- great for volume and contouring."
                )
            return self._q(
                message=(
                    "Dermal Fillers start from £250. "
                    "They're excellent for volume restoration and contouring -- "
                    "popular for the lips, cheeks, and jaw area. "
                    "We always recommend starting with a free consultation. "
                    "Would you like more details on booking?"
                ),
                stage="faq",
            )

        if _sub(txt, ["consult", "free appoint"]):
            self._faq_count += 1
            return self._q(
                message=(
                    "Great news -- our initial consultation is completely free! "
                    "It's a full assessment with one of our qualified practitioners, "
                    "with no commitment required. You can book via WhatsApp or our website."
                ),
                stage="faq",
            )

        if _sub(txt, ["hour", "open", "close", "sunday", "weekend", "timing", "when are"]):
            self._faq_count += 1
            return self._q(
                message=(
                    "We're open Monday to Saturday, 9:00 AM to 7:00 PM. "
                    "We're closed on Sundays. Plenty of flexibility for most schedules!"
                ),
                stage="faq",
            )

        if _sub(txt, ["how to book", "how do i book", "book", "appointment", "reserve", "schedule"]):
            self._faq_count += 1
            return self._q(
                message=(
                    "You can book via WhatsApp or our website -- whichever is easiest. "
                    "We ask for 24 hours' notice if you ever need to cancel. "
                    "Would you like help getting booked in?"
                ),
                stage="faq",
            )

        if _sub(txt, ["cancel", "cancellation"]):
            self._faq_count += 1
            return self._q(
                message=(
                    "We require 24 hours' notice for any cancellations. "
                    "This helps us offer the slot to other clients. "
                    "Is there anything else I can help with?"
                ),
                stage="faq",
            )

        if _sub(txt, ["service", "offer", "treatment", "what do you", "price", "cost", "pricing"]):
            self._faq_count += 1
            return self._q(
                message=(
                    "We offer three services at Bloom Aesthetics:\n"
                    "  - Botox from £200 (anti-wrinkle injections)\n"
                    "  - Dermal Fillers from £250 (volume and contouring)\n"
                    "  - Free Initial Consultation (no commitment required)\n"
                    "Would you like more details on any of these?"
                ),
                stage="faq",
            )

        # ---- Transition to qualification after at least 1 FAQ -------
        if self._faq_count >= 1 and self._qa_step == 0:
            # If the customer already volunteered name/contact, jump to service question
            n = _extract_name(raw)
            p = _extract_phone(raw)
            if n or p:
                self._name = n or self._name
                self._contact = p or self._contact
                return self._ask_service()
            return self._ask_name()

        # ---- Out-of-scope (generic) ---------------------------------
        self._unanswered += 1
        if self._unanswered >= 2:
            return self._q(
                message=(
                    "I'm afraid I don't have information on that either. "
                    "That's now two questions I haven't been able to answer, "
                    "so let me connect you with a member of our team who can help properly."
                ),
                escalate=True,
                escalation_reason="2 or more questions could not be answered from the SOP",
                confidence="low",
                unanswered=True,
            )
        return self._q(
            message=(
                "I'm afraid I don't have that information available. "
                "I can help with Botox, Fillers, free consultations, booking, and opening hours. "
                "Is there anything along those lines I can assist with?"
            ),
            confidence="low",
            unanswered=True,
            stage="faq",
        )

    # ------------------------------------------------------------------
    # Summary builder
    # ------------------------------------------------------------------

    def _build_summary(self) -> _Response:
        intent = "Customer enquired about " + (self._service or "clinic services")
        contact_str = self._contact or "[contact not collected]"
        name_str = self._name or "customer"
        service_str = self._service or "treatment"
        action = (
            "Call " + name_str + " on " + contact_str
            + " to book a " + service_str + " appointment."
        )
        summary = {
            "customer_intent": intent,
            "key_details": {
                "name": self._name,
                "contact": self._contact,
                "service_interest": self._service,
                "urgency": self._urgency,
            },
            "sop_gaps": [],
            "escalation": {"occurred": False, "reason": None},
            "recommended_next_action": action,
        }
        return _Response(json.dumps(summary))
