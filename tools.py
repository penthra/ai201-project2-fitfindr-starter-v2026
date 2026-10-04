"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

Search runs locally. Outfit suggestions and fit-card captions use the model.

The README Tool Inventory documents each tool's inputs, outputs, and empty cases.
"""

import re
import json
import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    Search steps:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    # Compare complete words, ignoring case and punctuation.
    keywords = set(re.findall(r"\w+", description.casefold()))
    if not keywords:
        return []

    # Keep decimal shoe sizes intact: US 8 must not match US 8.5.
    size_pattern = r"[a-z0-9]+(?:\.[0-9]+)?"
    requested_size = None
    if size is not None:
        requested_size = set(re.findall(size_pattern, size.casefold()))
        if not requested_size:
            return []

    matches = []
    for item in load_listings():
        if max_price is not None and item["price"] > max_price:
            continue

        if requested_size is not None:
            item_sizes = set(re.findall(size_pattern, item["size"].casefold()))
            if not requested_size.issubset(item_sizes):
                continue

        searchable_text = " ".join([
            item["title"],
            item["description"],
            item["category"],
            " ".join(item["style_tags"]),
            " ".join(item["colors"]),
            item["brand"] or "",
        ])
        item_words = set(re.findall(r"\w+", searchable_text.casefold()))
        score = len(keywords & item_words)
        if score > 0:
            matches.append((score, item))

    # Higher keyword scores first; cheaper items break ties.
    matches.sort(key=lambda match: (-match[0], match[1]["price"]))
    return [item for score, item in matches[:config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". The prompt explains that no wardrobe items
        are saved and requests two general outfit ideas.

    Steps:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    wardrobe_items = wardrobe["items"]
    item_text =json.dumps(new_item, ensure_ascii=False, indent=2)
    wardrobe_text = json.dumps(wardrobe_items,ensure_ascii=False, indent=2)
    if not wardrobe_items:
        wardrobe_instruction = (
            "The user has no wardrobe items saved. "
            "Explain this briefly and give two general outfit ideas "
            "around the selected item. Do not claim the user owns "
            "the clothes you recommend."
        )
    else:
        wardrobe_instruction = (
            "Create two outfit ideas around the selected item using "
            "pieces from the saved wardrobe. Copy the names of those "
            "pieces exactly as provided. Do not claim the user owns "
            "any additional clothes."
    )  
    prompt = f"""
    Suggest exactly two distinct outfits using the selected item.

    {wardrobe_instruction}

    For each outfit, describe the clothing combination and briefly explain
    why it works. Include the selected item in both outfits.
    Do not invent details about the selected item.

    Return plain text with two numbered outfit ideas.
    If the wardrobe is empty, put the explanation before the numbered ideas.

    Selected item:
    {item_text}

    Saved wardrobe items:
    {wardrobe_text}
    """ 
    response = generate(prompt)

    outfit_text = response.strip()


    if not outfit_text:
        raise ValueError("The model returned no outfit suggestions.")

    return outfit_text


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    Steps:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit.strip():
        return "An outfit suggestion is needed before creating a fit card."

    item_text = json.dumps(new_item, ensure_ascii=False, indent=2)
    prompt = f"""
        Write a short social media caption about this second-hand find.

        Requirements:
            - Write 2 to 4 sentences.
            - Name the selected item once, using its title or an accurate short description.
            - Include its correct price in digits once.
            - Mention its selling platform once.
            - Describe how to wear it using a combination from the outfit suggestion.
            - Describe the outfit's style or vibe.
            - Do not invent item details, including a brand if none is provided.
            - Return only the caption.
        Selected item:
            {item_text}

        Outfit suggestion:
            {outfit}
        """
    caption = generate(prompt).strip()

    if not caption:
        raise ValueError("The model returned no fit card.")

    return caption
