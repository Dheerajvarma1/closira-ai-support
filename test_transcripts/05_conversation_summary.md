# Scenario 5 - Conversation Summary

**Test**: A complete end-to-end session covering FAQ, qualification, and a clean close. Demonstrates the final structured summary output.
**Expected behaviour**: Summary contains all five fields - `customer_intent`, `key_details`, `sop_gaps`, `escalation`, and `recommended_next_action`.

---

```
══════════════════════════════════════════════════════════════
  BLOOM AESTHETICS CLINIC - AI Customer Support (Aria)
══════════════════════════════════════════════════════════════

Aria: Hello and welcome to Bloom Aesthetics Clinic! I'm Aria,
      your virtual assistant. How can I help you today?

You: Hi, I've been thinking about getting fillers. How much
     does it cost and how do I book?

Aria: Great to hear from you! Dermal Fillers start from £250
      at Bloom Aesthetics. You can book through WhatsApp or
      our website - whichever is easiest for you. We'd also
      recommend a free initial consultation first so our
      practitioner can tailor the treatment to you. Shall I
      help get that sorted?

You: Is there a consultation fee?

Aria: Great news - our initial consultation is completely free!
      It's a full assessment with one of our qualified
      practitioners, so there's no commitment involved.

You: That's reassuring. What are your opening hours?

Aria: We're open Monday to Saturday, 9:00 AM to 7:00 PM.
      We're closed on Sundays. Plenty of flexibility for
      most schedules! May I take your name and best contact
      number so we can follow up?

You: I'm James. You can reach me on 07911 234 567.

Aria: Lovely, James! And just to confirm - is it Dermal
      Fillers you're most interested in, or would you like to
      explore other treatments too?

You: Mainly fillers for my lips and cheeks.

Aria: Noted! And are you looking to book in soon, or are
      you still in the research phase?

You: I'd like to come in next month if possible.

Aria: Perfect, James. I've noted all of that down. One of
      our team will be in touch on 07911 234 567 to get
      your consultation booked in. Just a reminder - we ask
      for 24 hours' notice if you need to cancel. Is there
      anything else I can help with before we wrap up?

You: Nope, that covers it. Thanks!

Aria: You're very welcome, James! We look forward to
      welcoming you to Bloom Aesthetics. Have a wonderful day!

You: quit
```

---

## Session Summary Output

```json
{
  "customer_intent": "Customer is interested in dermal fillers for the lips and cheeks and would like to book a consultation for next month",
  "key_details": {
    "name": "James",
    "contact": "07911 234 567",
    "service_interest": "Dermal Fillers - lips and cheeks",
    "urgency": "Next month"
  },
  "sop_gaps": [],
  "escalation": {
    "occurred": false,
    "reason": null
  },
  "recommended_next_action": "Booking team to call James on 07911 234 567 to schedule a free initial consultation for dermal fillers, targeting a date in the next 4 weeks. WhatsApp follow-up recommended."
}
```

---

## Verification

**Summary fields:**
| Field | Status |
|---|---|
| `customer_intent` | Correctly identifies fillers interest and next-month timeline |
| `key_details.name` | `"James"` - collected in qualification |
| `key_details.contact` | `"07911 234 567"` - collected in qualification |
| `key_details.service_interest` | `"Dermal Fillers - lips and cheeks"` - specific and accurate |
| `key_details.urgency` | `"Next month"` - matches customer's stated preference |
| `sop_gaps` | Empty - all questions were answerable from SOP |
| `escalation.occurred` | `false` - no triggers fired during the session |
| `recommended_next_action` | Specific, actionable, includes contact detail |

**Conversation quality:**
- All pricing, hours, and booking info quoted accurately from SOP.
- Free consultation mentioned proactively - adds value without upselling pressure.
- Qualification collected across three natural turns, not in a single block.
- Closing message warm and professional.
