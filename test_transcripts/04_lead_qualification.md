# Scenario 4 - Lead Qualification

**Test**: Customer has a simple FAQ question, then the AI transitions to qualification and collects all three fields.
**Expected behaviour**: AI asks one question at a time, collects name/contact, service interest, and urgency. Produces a qualification summary at the end.

---

```
══════════════════════════════════════════════════════════════
  BLOOM AESTHETICS CLINIC - AI Customer Support (Aria)
══════════════════════════════════════════════════════════════

Aria: Hello and welcome to Bloom Aesthetics Clinic! I'm Aria,
      your virtual assistant. How can I help you today?

You: What services do you offer?

Aria: We offer three services at Bloom Aesthetics:
      • Botox - from £200, for smoothing fine lines and wrinkles
      • Dermal Fillers - from £250, for volume and contouring
      • Free Initial Consultation - a no-cost assessment before any treatment
      Would you like more details on any of these?

You: The Botox sounds interesting.

Aria: Great choice - Botox is one of our most popular
      treatments! To help us get you booked in, may I take
      your name and best contact number?

You: Sure, I'm Sarah. My number is 07700 900 123.

Aria: Lovely to meet you, Sarah! Just to confirm, are you
      most interested in Botox, or would you also like to
      consider Fillers or start with a free consultation first?

You: Botox for sure, just the forehead area.

Aria: Perfect. And how soon are you looking to come in -
      is this something you'd like to arrange within the
      next week or two, or are you planning a bit further
      ahead?

You: Ideally within the next two weeks.

Aria: Wonderful, Sarah! I've noted everything down. One of
      our team will be in touch shortly to confirm your
      appointment. In the meantime, do remember that we
      operate Monday to Saturday, 9 am to 7 pm, and we
      kindly ask for 24 hours' notice if you need to cancel.
      Is there anything else I can help with?

You: No, that's everything, thanks!

Aria: It was a pleasure chatting with you, Sarah! We look
      forward to welcoming you to Bloom Aesthetics. Have a
      lovely day!

──────────────────────────────────────────────────────────────
SESSION SUMMARY
──────────────────────────────────────────────────────────────
{
  "customer_intent": "Customer is interested in Botox treatment for the forehead area and wants to book within two weeks",
  "key_details": {
    "name": "Sarah",
    "contact": "07700 900 123",
    "service_interest": "Botox - forehead area",
    "urgency": "Within the next two weeks"
  },
  "sop_gaps": [],
  "escalation": {
    "occurred": false,
    "reason": null
  },
  "recommended_next_action": "Assign to booking team to call Sarah on 07700 900 123 and schedule a Botox appointment within the next two weeks. Consider sending a confirmation via WhatsApp."
}
──────────────────────────────────────────────────────────────
```

---

## Verification

- **Natural transition**: AI moved from FAQ to qualification organically after 2 exchanges - not abruptly.
- **One question at a time**: Each qualification question appeared in a separate turn, not all at once.
- **All three fields collected**: name + contact (`Sarah`, `07700 900 123`), service interest (`Botox - forehead`), urgency (`within two weeks`).
- **No escalation**: Session completed cleanly without triggering any escalation conditions.
- **Actionable summary**: `recommended_next_action` gives the booking team a clear task.
- **SOP accuracy**: Hours and cancellation policy quoted correctly in the closing message.
