# Scenario 1 - In-SOP Question

**Test**: Customer asks a question directly covered by the SOP (Botox pricing).
**Expected behaviour**: AI answers accurately from SOP data only. No hallucination.

---

```
══════════════════════════════════════════════════════════════
  BLOOM AESTHETICS CLINIC - AI Customer Support (Aria)
══════════════════════════════════════════════════════════════
  Commands: 'summary' - view session summary | 'quit' - end session
──────────────────────────────────────────────────────────────

Aria: Hello and welcome to Bloom Aesthetics Clinic! I'm Aria,
      your virtual assistant. Whether you have questions about
      our services, pricing, or booking, I'm happy to help.
      What can I do for you today?

You: What are your Botox prices?

Aria: Our Botox treatments start from £200. The exact price
      depends on the areas being treated and the number of
      units required. We'd recommend starting with a free
      initial consultation so our practitioner can give you a
      personalised quote. Would you like to know how to book?

You: What about fillers?

Aria: Dermal Fillers start from £250. They're great for volume
      restoration and contouring - popular for lips, cheeks,
      and the jaw area. Again, a free consultation lets our
      practitioner tailor the recommendation to you. Shall I
      help you get that booked?
```

---

## Verification

- **Botox price**: Answered as "from £200" - matches SOP exactly.
- **Fillers price**: Answered as "from £250" - matches SOP exactly.
- **No invented details**: No specific unit counts, session durations, or practitioner names were fabricated.
- **Escalation**: Not triggered (question was fully in-SOP).
- **Confidence**: `"high"` on both turns.
- **Stage**: Remained `"faq"` - AI correctly deferred qualification to after the pricing questions.
