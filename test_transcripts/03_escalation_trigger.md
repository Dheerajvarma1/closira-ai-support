# Scenario 3 - Escalation Trigger (Complaint / Anger)

**Test**: Customer expresses frustration or makes a complaint.
**Expected behaviour**: AI immediately detects negative sentiment, empathises briefly, and escalates to a human agent with a logged reason. No attempt to resolve the complaint itself.

---

```
══════════════════════════════════════════════════════════════
  BLOOM AESTHETICS CLINIC - AI Customer Support (Aria)
══════════════════════════════════════════════════════════════

Aria: Hello and welcome to Bloom Aesthetics Clinic! I'm Aria,
      your virtual assistant. How can I help you today?

You: I came in last week for fillers and I'm really not happy
     with the results. This is completely unacceptable.

Aria: I'm so sorry to hear you're not satisfied with your
      experience - that's not at all what we want for you.
      I'm going to connect you with a member of our team
      right away so they can look into this properly for you.

*** ESCALATION TRIGGERED ***
    Reason  : Customer expressed dissatisfaction and lodged a complaint about treatment results
    Action  : Flagging session and routing to human agent.

──────────────────────────────────────────────────────────────
SESSION SUMMARY
──────────────────────────────────────────────────────────────
{
  "customer_intent": "Customer is unhappy with the results of a recent dermal filler treatment and wants the issue resolved",
  "key_details": {
    "name": null,
    "contact": null,
    "service_interest": "Dermal Fillers (follow-up complaint)",
    "urgency": "Immediate - complaint about recent visit"
  },
  "sop_gaps": [],
  "escalation": {
    "occurred": true,
    "reason": "Customer expressed dissatisfaction and lodged a complaint about treatment results"
  },
  "recommended_next_action": "Human agent to contact customer urgently, review treatment notes, and offer a follow-up consultation or resolution."
}
──────────────────────────────────────────────────────────────
```

---

## Verification

- **Immediate escalation**: Triggered on first message containing complaint language ("not happy", "unacceptable").
- **No attempt to resolve**: AI did not try to advise on the treatment outcome or make promises.
- **Empathetic message**: Response acknowledged the customer's frustration before handing off.
- **Reason logged**: `"Customer expressed dissatisfaction and lodged a complaint about treatment results"` - specific and actionable for the human agent.
- **No medical advice**: AI did not comment on why the results may have appeared suboptimal.

---

## Additional Sub-Scenario: Medical Question Escalation

```
You: I want Botox but I'm on blood thinners - is it safe for me?

Aria: That's an important question, and your safety is our
      top priority. I'm not able to give medical advice, so
      I'd like to connect you with a qualified member of our
      team who can answer that properly.

*** ESCALATION TRIGGERED ***
    Reason  : Customer asked a medical question regarding drug interactions and treatment safety
    Action  : Flagging session and routing to human agent.
```

## Additional Sub-Scenario: Price Negotiation Escalation

```
You: £200 for Botox seems expensive - can you do it for £150?

Aria: I understand pricing is an important factor! Pricing
      decisions aren't something I'm able to discuss, but
      I'll connect you with our team who can help further.

*** ESCALATION TRIGGERED ***
    Reason  : Customer requested a discount or price negotiation
    Action  : Flagging session and routing to human agent.
```
