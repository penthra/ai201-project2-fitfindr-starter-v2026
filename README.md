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

The loop has three stages: `search`, `outfit`, and `card`. It increments a counter and calls `trace.check_iterations(count)` before each stage. Both the empty-search path and the completed-card path end with `return session`. The loop now catches `ModelUnavailable` and `MCPError`, saves a helpful message in `session["error"]`, records the failed step in the trace, and returns completed results without calling later tools.

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

Source: [original first run](results/run_2026-10-09_1747_before.md), produced by `run_eval.py::main` and `run_eval.py::write_report`. This is the first run actually performed, before adding the complete C3 receipt logging and fixing cache propagation.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5)* |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item reaches the next tool unchanged | 5 of 5 | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| 4. The fit card includes the right details | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5)* |
| 5. An empty wardrobe still produces outfit ideas | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5)* |

*The PASS cells reflect the recorded outputs. The model-dependent verdicts are provisional: the evaluation disabled caching only in its own process, while the separate MCP servers could still use their caches. Every repeated model response in this original run is identical. This run cannot establish five independent fresh model answers.

C3 is UNVERIFIED because the original trace abbreviates the received inputs to `dict with keys: new_item, wardrobe`. The report includes only the selected item's title, price, and platform; it does not record the full received dictionary or an all-fields comparison. Missing evidence is not evidence that the transfer failed, so no PASS/FAIL count is invented for C3.

**Real output from one try for each criterion**

The following excerpts are copied verbatim from Try 1 of each scenario in the original first run. Later receipts are not substituted into this Before section.

**Criterion 1 — matching query completes all three tools, Try 1**

Produced by: `agent.py::run_agent`; trace formatted by `trace.py::step`.

- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:

```
1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white sneakers, and the Black crossbody bag. This combination works because the fitted crop length of the baby tee balances out the voluminous silhouette of the baggy, high-waisted dark denim jeans, capturing an authentic Y2K streetwear aesthetic while keeping the accessories and footwear casual and functional.

2. Outfit 2 pairs the Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers, Vintage black denim jacket, Black combat boots, and the Brown leather belt. This combination works because layering the slightly cropped black denim jacket over the pink, purple, and white butterfly graphic adds edge and contrast, while the wide-leg khaki trousers and combat boots ground the playful top with earthy tones and grunge elements.
```

Fit card:

```
Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, chunky white sneakers, and a black crossbody bag. You can grab this adorable crop top for just $18.00 on Depop.
```

Trace:

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    select first item
[2] suggest_outfit (via MCP)
      in:  dict with keys: new_item, wardrobe
      out: 1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white…
[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jea…
```

**Criterion 2 — impossible query stops early, Try 1**

Produced by: `agent.py::run_agent`; trace formatted by `trace.py::step`.

- stopped early: yes — No matching items were found. Try different keywords, a different size, or a higher budget.
- selected_item: (none)
- search_results: 0

Trace:

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping
```

**Criterion 3 — selected item reaches next tool unchanged, Try 1**

Produced by: `agent.py::run_agent`; trace formatted by `trace.py::step`.

This is the original incomplete evidence; it cannot prove all fields reached the receiving tool unchanged.

- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:

```
1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white sneakers, and the Black crossbody bag. This combination works because the fitted crop length of the baby tee balances out the voluminous silhouette of the baggy, high-waisted dark denim jeans, capturing an authentic Y2K streetwear aesthetic while keeping the accessories and footwear casual and functional.

2. Outfit 2 pairs the Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers, Vintage black denim jacket, Black combat boots, and the Brown leather belt. This combination works because layering the slightly cropped black denim jacket over the pink, purple, and white butterfly graphic adds edge and contrast, while the wide-leg khaki trousers and combat boots ground the playful top with earthy tones and grunge elements.
```

Fit card:

```
Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, chunky white sneakers, and a black crossbody bag. You can grab this adorable crop top for just $18.00 on Depop.
```

Trace:

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    select first item
[2] suggest_outfit (via MCP)
      in:  dict with keys: new_item, wardrobe
      out: 1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white…
[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jea…
```

**Criterion 4 — fit card includes the right details, Try 1**

Produced by: `tools.py::create_fit_card`.

- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Outfit suggestion:

```
1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white sneakers, and the Black crossbody bag. This combination works because the fitted crop length of the baby tee balances out the voluminous silhouette of the baggy, high-waisted dark denim jeans, capturing an authentic Y2K streetwear aesthetic while keeping the accessories and footwear casual and functional.

2. Outfit 2 pairs the Y2K Baby Tee — Butterfly Print with Wide-leg khaki trousers, Vintage black denim jacket, Black combat boots, and the Brown leather belt. This combination works because layering the slightly cropped black denim jacket over the pink, purple, and white butterfly graphic adds edge and contrast, while the wide-leg khaki trousers and combat boots ground the playful top with earthy tones and grunge elements.
```

Fit card:

```
Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jeans, chunky white sneakers, and a black crossbody bag. You can grab this adorable crop top for just $18.00 on Depop.
```

Trace:

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    select first item
[2] suggest_outfit (via MCP)
      in:  dict with keys: new_item, wardrobe
      out: 1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white…
[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jea…
```

**Criterion 5 — empty wardrobe produces two general ideas, Try 1**

Produced by: `tools.py::suggest_outfit`.

- stopped early: no
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
- search_results: 7

Outfit suggestion:

```
You currently don't have any items saved in your digital wardrobe, so here are two general outfit ideas built around the Denim Jacket (Light Wash, Cropped) to inspire your styling.

1. Outfit Idea One: Pair the light wash cropped denim jacket with a classic white crewneck t-shirt, high-waisted black wide-leg trousers, and retro white leather sneakers.
Why it works: The structured shoulders and light wash of the jacket create a sharp contrast against the dark trousers, while the cropped length naturally emphasizes the high waist for a balanced, modern silhouette.

2. Outfit Idea Two: Layer the cropped denim jacket over a floral midi slip dress in a dark or neutral tone, paired with chunky black leather combat boots.
Why it works: The pairing plays on the contrast between feminine, fluid movement in the dress and the rugged, structured utility of the denim outerwear and boots, resulting in an effortless streetwear-inspired look.
```

Fit card:

```
Score this vintage-inspired streetwear look by grabbing this Denim Jacket — Light Wash, Cropped on Poshmark for just $42. Layer it over a floral midi slip dress and pair with chunky black leather combat boots for an effortless vibe.
```

Trace:

```
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 7 items: Denim Jacket — Light Wash, Cropped, High-Waisted Denim Shorts — Cutoff, Denim Vest — Medium Wash, Studded … +4 more
      →    select first item
[2] suggest_outfit (via MCP)
      in:  dict with keys: new_item, wardrobe
      out: You currently don't have any items saved in your digital wardrobe, so here are two general outfit ideas built …
      →    empty wardrobe: general advice
[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: Score this vintage-inspired streetwear look by grabbing this Denim Jacket — Light Wash, Cropped on Poshmark fo…
```

---

## Verdicts and Diagnoses

These baseline judgments use the [original first run](results/run_2026-10-09_1747_before.md) and the unchanged targets in `criteria.md`. Later results are reported separately under Run Log — After.

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5), provisional | Every saved trace shows the three tool calls and a non-empty fit card. The recorded outputs pass, but the server cache setting means this is not a verified five-fresh-answer evaluation. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | Every try has zero matches, only the search step, and a message suggesting different keywords, size, or budget. This path does not call the model. |
| 3 | The selected item reaches the next tool unchanged | 5 of 5 | UNVERIFIED | None of the five tries records the full received dictionary or a comparison with the full selected item. The abbreviated trace cannot establish the target. |
| 4 | The fit card includes the right details | 4 of 5 | MET (5/5), provisional | All five saved captions meet the seven requirements: the right item, price and platform, a supplied clothing combination, a consistent vibe, two sentences in caption style, and no unsupported item details. The cache limitation prevents treating them as five confirmed fresh answers. |
| 5 | An empty wardrobe still produces outfit ideas | 4 of 5 | MET (5/5), provisional | Each saved suggestion gives exactly two general outfit ideas and explains that no wardrobe items are saved. The model responses may have been reused from cache. |

**Diagnoses**

The first run did not demonstrate C3's target. The step was the handoff into `suggest_outfit`; the measurement mechanism was that `trace.py::_short` rendered the argument dictionary only as its key names, while `run_eval.py::write_report` saved only a summary of the selected item. There was no complete received-item snapshot to compare. This is an evaluation/logging gap, not proof that the agent changed any fields. C3 was already measurable as written, so its wording and 5-of-5 target remain unchanged.

A second pattern affected all model-dependent scenarios: their repeated outputs were identical. `run_eval.py::main` set `config.CACHE_ENABLED = False` only in the evaluation process, but the model tools ran in separate MCP server processes with their own cache settings. Those outputs could therefore be cached rather than independent tries. This is an evaluation configuration problem at the client/server boundary. It does not prove that the captions or outfit ideas violated their content criteria, but it limits the first run's evidence of consistency.

The remaining recorded outputs contain no observed content misses against the original criteria. The revised evaluation addresses both measurement gaps by capturing the item at the receiver and propagating the disabled cache setting. Its results appear in the After table. The first run remains preserved with its limitations.

---

## Loop Trace

These are actual Try 1 traces from the [original first run](results/run_2026-10-09_1747_before.md). The loop is `agent.py::run_agent`; trace output is produced by `trace.py::step`.

**Happy path**

Query: `vintage graphic tee under $30`, with the example wardrobe.

```text
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    select first item
[2] suggest_outfit (via MCP)
      in:  dict with keys: new_item, wardrobe
      out: 1. Outfit 1 combines the Y2K Baby Tee — Butterfly Print with Baggy straight-leg jeans, dark wash, Chunky white…
[3] create_fit_card (via MCP)
      in:  dict with keys: outfit, new_item
      out: Channel total Y2K streetwear energy by styling this Y2K Baby Tee — Butterfly Print with baggy straight-leg jea…
```

**Empty search**

Query: `designer ballgown size XXS under $5`, with the example wardrobe.

```text
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    branch: empty, stopping
```

Returned error from `agent.py::run_agent`:

```text
No matching items were found. Try different keywords, a different size, or a higher budget.
```

**On the MCP move:**

The loop now imports `call_tool` from `mcp_client.py` and calls the registered tools by name with argument dictionaries. `mcp_server.py` registers typed wrappers around the existing implementations in `tools.py`. All three tools were moved onto MCP, although the milestone only required moving search. `mcp_client.py::_call` starts the server over stdio, initializes a session, checks the registered tool names, calls the requested tool, and unwraps its response into a Python value.

In the current after-run, search still returns listing dictionaries, the highest-ranked item is still selected, and both later tools return text. The full path has three tool steps; the empty-search path has one because the loop stops before outfit generation. The C3 receipts also verify that the selected item's fields survive the MCP transfer unchanged in all five tries. These observations establish the behavior of the tested scenarios, rather than equality of all possible model responses before and after the move.

One issue introduced by using separate processes was that disabling caching in the evaluation process did not disable it in the servers. The client now passes the actual cache setting to each server. The evaluation also passes a per-try receipt path so the receiving outfit tool can record the full item for C3.

**Failure-mode evidence available so far**

- **Empty search:** Triggered and handled in all five C2 tries. Search returns no results, the loop stops, and the user receives suggestions for changing the query.
- **Empty wardrobe:** Triggered and handled in all five C5 tries. The outfit tool explains that no clothes are saved and returns two general ideas. The fit-card stage then completes.
- **Model unavailable / bad key:** Triggered using `python run_failure_check.py`, which sends an intentionally invalid key only to the test's MCP subprocesses, with caching off. It does not edit `.env` or the saved key. Before the improvement, the loop raised an unhandled `MCPError` during outfit generation. After the improvement, it returns a helpful error, keeps the search results and selected item, and stops before fit-card generation. Real output is saved in [failure_before.txt](results/failure_before.txt) and [failure_after.txt](results/failure_after.txt).

Bad-key output before the improvement, produced by `run_failure_check.py::main`:

```text
Failure check: real MCP calls with an intentionally invalid API key.
The saved .env and real key are unchanged; caching is disabled.
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    select first item
UNHANDLED: MCPError: Couldn't call 'suggest_outfit' over MCP: unhandled errors in a TaskGroup (1 sub-exception)
Check that mcp_server.py runs on its own first:
    python mcp_server.py
If it exits immediately with an error, fix that before coming back here.
```

Bad-key trace after the improvement, produced by `agent.py::run_agent` and `trace.py::step`, printed by `run_failure_check.py::main`:

```text
Failure check: real MCP calls with an intentionally invalid API key.
The saved .env and real key are unchanged; caching is disabled.
[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    select first item
[2] suggest_outfit (via MCP)
      out: Could not generate outfit suggestions. Check your model API key and internet connection, then try again.
      →    tool unavailable: stopping; completed results preserved
```

Selected fields from the returned session, copied from the saved after-check output:

```json
  "outfit_suggestion": null,
  "fit_card": null,
  "error": "Could not generate outfit suggestions. Check your model API key and internet connection, then try again."
```

```text
HANDLED: the agent returned an error message instead of raising.
```

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

Made the evaluation capture verifiable evidence across the MCP boundary. `mcp_server.py::suggest_outfit` now records the complete received item before model work. `run_eval.py::run_once` creates a fresh receipt location for each try, compares the complete received item with `session["selected_item"]`, and saves both dictionaries and `all_fields_match` in the report. `mcp_client.py::_call` passes the cache setting and receipt path to each server process, so evaluation runs disable caching where the model calls actually happen.

**Which failure it was meant to fix:**

The original first run did not have enough print/log evidence to score C3, and its repeated model answers were not established as fresh responses. The revision makes the existing criteria testable with complete item comparisons and correctly propagated evaluation settings. No criterion or target was lowered or rewritten.

The current version also handles model/MCP failures in the loop, as required by the failure-mode task. That separate fix is demonstrated by the bad-key before/after evidence under Loop Trace; it is not presented as proof that the first run's C3 transfer failed.

### Run Log — After

Source: [after-run report](results/run_2026-10-09_1826_after.md), produced by `run_eval.py::main` and `run_eval.py::write_report`. All five scenarios were run five times with caching off and the same scenarios, targets, model, and temperature as the original first run. Unlike the first run, the current evaluation propagates caching off to the servers and captures full C3 receipts.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item reaches the next tool unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card includes the right details | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. An empty wardrobe still produces outfit ideas | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

All five full-run tries completed their three tool steps. All five empty-search tries stopped after search with an actionable message. All five C3 receipts show equal selected and received dictionaries. Every C4 caption contains the correct item, price, and platform, a combination from its own suggestion, a consistent vibe, and two caption-style sentences without unsupported item details. Every C5 suggestion gives two general ideas and states that no wardrobe items are saved.

C4 Try 3 awkwardly writes "baggy straight-leg jeans, a dark wash, and black combat boots." The jeans and boots are from the supplied outfit, and dark wash is a supplied description of the jeans. The wording is clumsy, but it does not violate one of the seven written requirements, so this try remains PASS.

Real after-run caption from C4 Try 1, produced by `tools.py::create_fit_card`:

```text
Score this gorgeous Y2K Baby Tee — Butterfly Print for just $18.00 on Depop! Style it with wide-leg khaki trousers, a black cropped zip hoodie, and chunky white sneakers for a relaxed, casual vibe.
```

**Did it help, and how do I know:**

The first run's C3 inputs were abbreviated to dictionary key names, so all five tries were unverified. The current After report contains both full item dictionaries for every C3 try; all five comparisons report `all_fields_match: true`. C3 can now be scored MET (5/5). This is improved evidence, not a demonstrated increase from zero successful transfers to five.

The current evaluation passes the disabled cache setting into the server processes, and the saved model outputs vary across tries. The current five-scenario run meets all five unchanged targets with 5/5 passes. Because the first run had incomplete C3 evidence and a caching limitation, the two runs do not support claiming an increase in agent accuracy; they support a more trustworthy evaluation.

For the additional failure-mode fix, the same real bad-key check changed from an unhandled `MCPError` to a returned session with an actionable message. Search results and the selected item are preserved, and later tool calls stop. The five normal scenarios still pass, so there is no observed regression on those scenarios.

---

## What's Still Broken

None of the five original criteria remains missed in the after-run. The tests still cover only one repeated tee and one repeated jacket, so the passing results do not establish reliability across the whole catalogue or arbitrary queries.

There is a quality issue outside the written criteria. In the after-run's empty-wardrobe Try 4, `tools.py::suggest_outfit` says:

```text
You do not currently own these additional pieces, but they serve as great styling suggestions to complement the jacket.
```

An empty digital wardrobe means no items are saved; it does not establish what clothes the user owns in real life. The step is the outfit tool, and the mechanism is the model inferring ownership from missing saved data. This still passes criterion 5 because it supplies two general ideas and explains that no items are saved. A future prompt change could explicitly forbid inferring either ownership or non-ownership from the saved wardrobe, followed by repeated empty-wardrobe tests with an ownership requirement.

The C4 Try 3 phrase "a dark wash" also shows that passing the current content checks does not guarantee smooth grammar. A future caption test could include clarity and grammatical completeness, with an explicit scoring rule.

<!-- Personal reflection pending: ask the author for their actual stopping reason and next priority, and any real feedback from the verdict challenge. Do not invent these. -->

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

       [x] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---
