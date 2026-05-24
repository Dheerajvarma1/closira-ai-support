#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated test runner -- no API key required.
Replays all 5 assignment scenarios and prints the results.
"""

import json
import os

# Force demo mode so no API key is needed
os.environ.pop("ANTHROPIC_API_KEY", None)

from mock_client import MockAI
from main import SupportSession, extract_json, print_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def bar(char="=", w=64):
    print(char * w)


def run_scenario(title: str, turns: list[str], expect_escalation: bool = False) -> None:
    bar()
    print("SCENARIO: " + title)
    bar()

    session = SupportSession()

    # Opening
    opening = session.chat("Hello, I'd like some information about your clinic.")
    print("Aria : " + opening["message"])
    print()

    escalated = False
    for user_msg in turns:
        print("You  : " + user_msg)
        result = session.chat(user_msg)
        print("Aria : " + result["message"])

        if result.get("escalate"):
            print()
            print("*** ESCALATION TRIGGERED ***")
            print("    Reason : " + (result.get("escalation_reason") or "N/A"))
            escalated = True
            print()
            break

        if result.get("session_complete"):
            print()
            break

        print()

    # Summary
    summary = session.generate_summary()
    print_summary(summary)

    # Pass / Fail
    if expect_escalation:
        status = "PASS" if escalated else "FAIL (expected escalation, none triggered)"
    else:
        status = "PASS" if not escalated else "FAIL (unexpected escalation)"
    print("Result: " + status)
    bar("-")
    print()


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

def main():
    print()
    bar("*")
    print("  BLOOM AESTHETICS CLINIC -- Automated Test Suite (Demo Mode)")
    bar("*")
    print()

    # 1. In-SOP question
    run_scenario(
        title="1 -- In-SOP Question (Botox & Filler pricing)",
        turns=[
            "What are your Botox prices?",
            "And what about fillers?",
        ],
        expect_escalation=False,
    )

    # 2. Out-of-scope question -> escalation after 2 gaps
    run_scenario(
        title="2 -- Out-of-Scope Question (triggers escalation after 2 gaps)",
        turns=[
            "Do you offer laser hair removal?",
            "What about skin peels?",
        ],
        expect_escalation=True,
    )

    # 3a. Complaint escalation
    run_scenario(
        title="3a -- Escalation Trigger: Customer Complaint",
        turns=[
            "I came in last week and I'm really not happy with the results. This is unacceptable.",
        ],
        expect_escalation=True,
    )

    # 3b. Medical question escalation
    run_scenario(
        title="3b -- Escalation Trigger: Medical Question",
        turns=[
            "Is Botox safe for me? I'm on blood thinners.",
        ],
        expect_escalation=True,
    )

    # 3c. Price negotiation escalation
    run_scenario(
        title="3c -- Escalation Trigger: Price Negotiation",
        turns=[
            "What are your Botox prices?",
            "200 pounds seems expensive, can you do it cheaper?",
        ],
        expect_escalation=True,
    )

    # 4. Full lead qualification flow
    run_scenario(
        title="4 -- Lead Qualification (full flow)",
        turns=[
            "What services do you offer?",
            "I'm interested in Botox.",
            "I'm Sarah, my number is 07700 900 123",
            "Botox please",
            "Within the next two weeks",
            "No, that's everything, thanks!",
        ],
        expect_escalation=False,
    )

    # 5. Complete session -> conversation summary
    run_scenario(
        title="5 -- Full Session with Conversation Summary",
        turns=[
            "How much do fillers cost?",
            "Is the consultation free?",
            "What are your opening hours?",
            "My name is James and my number is 07911 234 567",
            "Fillers please",
            "Next month",
            "No, that covers it. Thank you!",
        ],
        expect_escalation=False,
    )

    bar("*")
    print("  All scenarios complete.")
    bar("*")
    print()


if __name__ == "__main__":
    main()
