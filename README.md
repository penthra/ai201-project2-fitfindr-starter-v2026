# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> The three tools and planning loop are implemented. The search runs locally;
> outfit suggestions and captions use the model through `generate()`.
>
> **The rest of this file is your submission.** Fill it in as you go.

---
Peng Wu

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

This project helps a user find second-hand clothes in a local catalogue by entering a description, an optional size, and a budget, such as "vintage graphic tee under $30, size M". It selects the highest-ranked match and asks a model for two outfit ideas using the saved example wardrobe, or general ideas when the wardrobe is empty. It then generates one short fit-card caption about the item, its price, its selling platform, and how to wear it. If no listings match, it stops and suggests changing the keywords, size, or budget.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Finds clothes in the local catalogue using keywords from the description. The user can also filter by size and budget. Sizes are matched without worrying about uppercase or lowercase, using complete size tokens: `M` matches `S/M`, but `L` does not match `XL`. Items priced exactly at the budget are included.
- **Inputs:** `description` (`str`) is what the user is looking for. `size` (`str | None`, default `None`) and `max_price` (`float | None`, default `None`) are optional filters. `None` means that filter is skipped.
- **Returns:** A list of matching listing dictionaries with details such as `title`, `price`, `size`, and `platform`. Better keyword matches come first. If two listings have the same score, the cheaper one comes first. The list contains at most `config.SEARCH_RESULT_LIMIT` items.
- **When it has nothing:** Returns an empty list (`[]`) if no listings match.

### `suggest_outfit`

- **What it does:** Puts together two outfit ideas around the selected clothing item. It uses clothes from the user's wardrobe when they have items saved.
- **Inputs:** `new_item` (`dict`) contains the selected listing. `wardrobe` (`dict`) contains an `items` list of the user's saved clothes.
- **Returns:** A non-empty string (`str`) with two outfit suggestions. When using saved wardrobe pieces, it keeps their names exactly as they appear in the wardrobe so the user can tell which clothes to use.
- **When it has nothing:** If the wardrobe is empty, it still gives two general outfit ideas and explains that they are general because the user has no wardrobe items saved.

### `create_fit_card`

- **What it does:** Writes a short caption about the second-hand item and how to wear it, like something the user could post on social media.
- **Inputs:** `outfit` (`str`) is the outfit suggestion text. `new_item` (`dict`) contains the selected listing and its details.
- **Returns:** A string (`str`) with two to four sentences. The caption includes the item's price written in digits and the platform where it is being sold.
- **When it has nothing:** If `outfit` is empty or only contains spaces or other whitespace, it returns a helpful message explaining that an outfit suggestion is needed. It does not call the model or raise an exception in this case.

---

## Planning Loop

**Branch rule:**

1. **`search_listings`:** The agent calls `search_listings` with the parsed description, size, and maximum price, then saves the returned list in `session["search_results"]`. If the list is empty, it saves a message in `session["error"]` suggesting different keywords, a different size, or a higher budget, and stops. Otherwise, it selects the first listing, saves it in `session["selected_item"]`, and continues to `suggest_outfit`.
2. **`suggest_outfit`:** The agent calls `suggest_outfit` with the selected item from `session["selected_item"]` and the saved wardrobe from `session["wardrobe"]`. If the wardrobe contains items, the tool uses them to suggest two outfits around the selected item. If the wardrobe is empty, it suggests two general outfit ideas and explains that no wardrobe items are saved. The agent saves the returned text in `session["outfit_suggestion"]` and continues to `create_fit_card`.
3. **`create_fit_card`:** The agent calls `create_fit_card` with the outfit suggestion from `session["outfit_suggestion"]` and the selected item from `session["selected_item"]`. If the outfit suggestion is empty or contains only whitespace, the tool returns a helpful message explaining that an outfit suggestion is needed. Otherwise, it writes a two-to-four-sentence caption about the item and how to wear it, including its price in digits and the platform where it is sold. The agent saves the returned text in `session["fit_card"]` and returns the completed session.

**Where it lives:** `agent.py::run_agent`.

**How the query is parsed:** The agent uses regular expressions (regex), without a model call, to extract a price after "under" and a size after "size". The dollar sign is optional, prices are converted to `float`, and matching ignores letter case. It removes those phrases, replaces commas with spaces, and tidies whitespace to form the search description. For example, "vintage graphic tee under $30, size M" becomes description="vintage graphic tee", size="M", and max_price=30.0. Missing size or budget filters are `None`. This parser handles these patterns, not every natural-language phrasing; for example, "under thirty dollars" is not recognized as a budget.

**What moves through the session:** `new_session` starts with `query` and `wardrobe`. The agent fills `parsed`, then `search_results`, then saves the first result in `selected_item`. It passes that selected dictionary and the wardrobe to `suggest_outfit`, saving the returned text in `outfit_suggestion`. It passes that text and the same selected item to `create_fit_card`, saves the caption in `fit_card`, and returns the session. If search returns `[]`, it sets `error` and returns early; `selected_item`, `outfit_suggestion`, and `fit_card` remain `None`.

The loop has three stages: `search`, `outfit`, and `card`. It increments a counter and calls `trace.check_iterations(count)` before each stage. Both the empty-search path and the completed-card path end with `return session`. Model exceptions are not yet caught by this loop.

---

## Sample Run

These are actual outputs from the current code, run with the project's virtual environment. Commands below assume that environment is activated. The full run reused two cached responses, as the printed usage line shows; this is a functional example, not five independent model evaluation trials.

**One full query**

```text
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white sneakers, and the Black crossbody bag. This combination works because the fitted crop length of the baby tee balances out the voluminous silhouette of the baggy, high-waisted dark denim jeans, capturing an authentic Y2K streetwear aesthetic while keeping the accessories and footwear casual and functional.

2. Outfit 2 pairs the Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers, Vintage black denim jacket, Black combat boots, and the Brown leather belt. This combination works because layering the slightly cropped black denim jacket over the pink, purple, and white butterfly graphic adds edge and contrast, while the wide-leg khaki trousers and combat boots ground the playful top with earthy tones and grunge elements.

  Fit card: Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, chunky white sneakers, and a black crossbody bag. You can grab this adorable crop top for just $18.00 on Depop.

0 model calls this session, 2 served from cache
```

**The three tools, tested one at a time**

**`search_listings`**

```text
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

**`suggest_outfit`**

```text
$ python -c "from tools import suggest_outfit; from utils.data_loader import load_listings, get_example_wardrobe; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
1. Outfit Idea 1
Combination: Vintage Levi's 501 Jeans — Medium Wash paired with the White ribbed tank top, Black cropped zip hoodie, Chunky white sneakers, and Black crossbody bag.
Why it works: This combination plays into a classic streetwear look. The fitted white tank top balances the straight-leg fit of the jeans, while the cropped zip hoodie and chunky white sneakers add casual, athletic layers that complement the vintage feel of the denim.

2. Outfit Idea 2
Combination: Vintage Levi's 501 Jeans — Medium Wash paired with the Oversized grey crewneck sweatshirt, Vintage black denim jacket, Black combat boots, and Brown leather belt.
Why it works: This outfit leans into a grunge-inspired, cozy aesthetic. Tucking or layering with the oversized grey crewneck and throwing on the vintage black denim jacket creates a cool contrast against the medium wash jeans, while the black combat boots and brown leather belt anchor the heavier textures of the look.
```

**`create_fit_card`**

```text
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('Pair with a white T-shirt and sneakers for a casual look.', load_listings()[0]))"
Scored these amazing Vintage Levi's 501 Jeans — Medium Wash for just $38.00 on depop! Pair them with a white T-shirt and sneakers for an effortlessly casual look.
```

---

## How I Used AI

**Moment 1 — implementing search**

- *What I asked for:* I asked Codex to explain how catalogue search works, clarify terms such as keyword scoring and tie-breaking, and guide me through implementing search_listings using the rules in my README.
- *What came back:* Codex explained keyword scoring, optional size and budget filters, price-based tie-breaking, and the result limit. It explained why checking whether "L" is a substring of "XL" would give the wrong size match.
- *What I changed:* With Codex's guidance, I replaced the search stub with an implementation. The tool now matches complete size tokens, includes items priced exactly at the budget, and returns [] when nothing matches. Codex also helped check size matching, sorting, and budget boundaries.

**Moment 2 — turning a user's query into search inputs**

- *What I asked for:* I asked for step-by-step guidance on implementing `run_agent` from my README rules. I did not understand how `re.search` differed from `search_listings`, what the regex symbols meant, or how `.start()` and `.end()` were used to remove matched text.
- *What came back:* Codex explained that regex reads the user's sentence to extract filters, while `search_listings` searches the catalogue. It showed how to turn "under $30" into the number `30.0`, extract "M" from "size M", and remove those phrases so the remaining text becomes the clothing description. It also explained that asking a model to extract the fields was an alternative, but would require parsing and validating its response.
- *What I changed:* I used the guidance to add regex parsing in `agent.py` and save the description, size, and maximum price in `session["parsed"]`. I converted the captured price to a `float`, kept missing filters as `None`, and removed the matched filter phrases before searching. This separates the user's budget and size from the clothing keywords instead of treating the entire sentence as a search description.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
