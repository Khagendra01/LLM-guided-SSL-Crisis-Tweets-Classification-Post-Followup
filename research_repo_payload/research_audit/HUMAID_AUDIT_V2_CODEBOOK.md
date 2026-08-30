# HumAID Audit V2 codebook

Choose exactly one **primary label** based on the tweet's primary communicative intent. An optional **secondary label** may record a genuinely plausible alternative. Do not use the hidden HumAID or GPT-4o labels while annotating.

## Labels

- `caution_and_advice` — warnings, threat-status alerts, instructions, safety guidance, tips, or behavioral advice. An active official threat/warning can qualify even without an imperative.
- `displaced_people_and_evacuations` — evacuation, relocation, displaced people, or sheltering as movement/accommodation of affected people.
- `infrastructure_and_utility_damage` — physical damage or service/access disruption involving buildings, roads, bridges, power, water, communications, housing, or other infrastructure.
- `injured_or_dead_people` — injuries, casualties, fatalities, death tolls, or bodies.
- `missing_or_found_people` — people explicitly reported missing, unaccounted for, found, located, or reunited.
- `requests_or_urgent_needs` — direct survival/SOS needs of affected people: rescue, food, water, medicine, shelter, supplies, or services needed now.
- `rescue_volunteering_or_donation_effort` — offering/organizing aid, rescues, volunteers, donations, fundraisers, supply collections, relief delivery, or calls directed at would-be donors/helpers.
- `sympathy_and_support` — prayers, condolences, encouragement, solidarity, or emotional support without a concrete aid action.
- `other_relevant_information` — real disaster-related information that does not fit a more specific impact/action class.
- `not_humanitarian` — genuinely unrelated, metaphorical, entertainment, spam-like, or contextless use that is not conveying information about the real disaster/humanitarian situation.

## Tie-break rules

1. **Specific beats generic.** If a concrete impact/action class clearly applies, prefer it over `other_relevant_information`.
2. **Warning vs infrastructure.** A road/power/water closure or outage is infrastructure; use caution when the central point is what people should do or an active warning/threat status.
3. **Evacuation vs caution.** Explicit instructions to evacuate may be primarily caution; reports that people are evacuating, relocated, or using shelters are displaced/evacuations. Use the other as secondary when both are central.
4. **Urgent need vs donation/volunteering.** Affected people saying "we need water/rescue now" → urgent needs. Appeals aimed at donors/volunteers or organized aid → rescue/volunteering/donation.
5. **Donation CTA beats background impact.** If a tweet contains impact statistics but culminates in a concrete donation/aid call, the aid action can be primary and the impact class secondary.
6. **Generic "help/support" is not automatically aid logistics.** Without a concrete mechanism, use sympathy/support or other relevant information as appropriate.
7. **Stranded is not automatically displaced.** Use displaced/evacuations when movement, relocation, sheltering, or displacement is explicit.
8. **Broad destruction can count as infrastructure damage** when the statement clearly describes physical disaster impact.
9. **Real-event misinformation/conspiracy remains on-topic unless purely unrelated/metaphorical.** Do not use `not_humanitarian` merely because the claim appears false.
10. **Mixed-impact summaries.** Choose the impact/action that dominates the tweet; record a close second class as secondary and mark ambiguity when reasonable annotators could differ.

## Confidence and ambiguity

- `confidence=3`: clear primary label.
- `confidence=2`: plausible alternative exists, but one label is preferred.
- `confidence=1`: text is truncated/context-poor or two+ labels are nearly tied.
- `ambiguous=yes`: at least two taxonomy labels are genuinely plausible under the visible text.
- `ambiguous=no`: one label is clearly preferred.

Reasons should be short, factual, and based only on the visible tweet/event context.
