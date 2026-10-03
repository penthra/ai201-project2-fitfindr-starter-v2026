# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
A matching query should usually produce a complete result. I allow one
failed try because the run depends on two model calls, and a temporary model
service failure could prevent it from finishing even when search finds an item.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
Without a matching item, the agent cannot give an outfit based on a search
result. I require 5 of 5 because Python can check for an empty list and return
a helpful message without calling the model.

---

## 3. The selected item reaches the next tool unchanged

Given a query that matches at least one listing, the item received by
`suggest_outfit` matches the selected search result stored in
`session["selected_item"]`, with all fields unchanged — 5 of 5 tries.

**Why this target:**
Passing the wrong item would produce outfit ideas for the wrong clothes.
I require 5 of 5 because this step uses fixed Python code, not model output.

---

## 4. The fit card includes the right details

Given a selected item and a non-empty outfit suggestion, the fit card meets
all the following requirements — in at least 4 of 5 tries:

- Names the selected item once, using its title or an accurate short description.
- Includes the item's correct price in digits once, such as "$25".
- Names the correct selling platform once, such as "Depop".
- Describes at least one way to wear the item using clothing combinations from the supplied outfit suggestion.
- Describes the outfit's style or vibe, such as casual or vintage, consistently with the item and outfit suggestion.
- Contains 2 to 4 sentences written as a social media caption.
- Does not invent item details, such as a brand that is missing from the listing.

The wording can vary. A try passes only if it meets every requirement above.

**Why this target:**
The caption should tell the user what the find is, what it costs, where it is
sold, and how to wear it without making up details. I allow one failed try
because the model may occasionally miss a content or length instruction.

---

## 5. An empty wardrobe still produces outfit ideas

Given a selected item and an empty wardrobe, `suggest_outfit` returns two
general outfit ideas and explains that no wardrobe items are saved — in at
least 4 of 5 tries.

**Why this target:**
Users should get styling help even without a saved wardrobe. I allow one
failed try because the model may occasionally miss the requested number of
ideas or the explanation.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
