# Scenario 2 - Out-of-Scope Question

**Test**: Customer asks something not covered in the SOP (laser hair removal, parking).
**Expected behaviour**: AI honestly acknowledges the gap rather than guessing. After 2 unanswered questions, escalation is triggered.

---

```
══════════════════════════════════════════════════════════════
  BLOOM AESTHETICS CLINIC - AI Customer Support (Aria)
══════════════════════════════════════════════════════════════

Aria: Hello and welcome to Bloom Aesthetics Clinic! I'm Aria,
      your virtual assistant. How can I help you today?

You: Do you offer laser hair removal?

Aria: I'm afraid I don't have that information - laser hair
      removal isn't listed in the services I have details on.
      I can tell you about Botox (from £200), Dermal Fillers
      (from £250), and free initial consultations. Would any
      of those be of interest?

You: What about skin peels?

Aria: I'm sorry, I don't have information about skin peels
      either. That's now two questions I haven't been able to
      answer from the details I have available. To make sure
      you get accurate information, I'm going to connect you
      with a member of our team who can help properly.

*** ESCALATION TRIGGERED ***
    Reason  : 2 or more questions could not be answered from the SOP
    Action  : Flagging session and routing to human agent.

──────────────────────────────────────────────────────────────
SESSION SUMMARY
──────────────────────────────────────────────────────────────
{
  "customer_intent": "Customer is enquiring about services not listed in the SOP (laser hair removal, skin peels)",
  "key_details": {
    "name": null,
    "contact": null,
    "service_interest": "Laser hair removal, skin peels (not in SOP)",
    "urgency": null
  },
  "sop_gaps": [
    "Laser hair removal - not listed in SOP",
    "Skin peels - not listed in SOP"
  ],
  "escalation": {
    "occurred": true,
    "reason": "2 or more questions could not be answered from the SOP"
  },
  "recommended_next_action": "Human agent to confirm whether the clinic offers laser hair removal or skin peels, and update the SOP if so."
}
──────────────────────────────────────────────────────────────
```

---

## Verification

- **No hallucination**: AI did not invent pricing or availability for out-of-scope services.
- **Graceful acknowledgement**: Used the prescribed phrase "I don't have that information."
- **Escalation count**: Correctly escalated after the 2nd unanswered question.
- **SOP gaps logged**: Both missing topics appear in the summary's `sop_gaps` array.
- **Recommended action**: Summary suggests updating the SOP - useful operational insight.
