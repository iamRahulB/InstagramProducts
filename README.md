# InstagramProducts

## Phase 1

Phase 1 creates one validated, calendar-aware outfit specification for India and writes it to `data/research/`.

Install the project and development tools:

```bash
python -m pip install -e '.[dev]'
```

Run the calendar-driven outfit pipeline:

```bash
python -m phase1
```

Copy `.env.example` to `.env` when configuring Gemini. Phase 1 requires Gemini for current fashion reasoning; it does not use Google Search, scrape the web, search product listings, call SerpApi, or generate affiliate links.

Indian calendar dates and eligible occasions are loaded through the `holidays` package and passed to the replaceable outfit AI provider as temporal facts. Occasions must have at least 10 days of lead time. The planner uses previous JSON reports for deterministic male/female balancing and outfit variation. The AI chooses one outfit, only the item categories that outfit needs, and accessories that coordinate with the clothing.

The report contains one `outfit` with stable `research_id` and `outfit_id`, controlled item categories, visual requirements, and one concise `search_query` per item for Phase 2. Queries are lowercase, use `men`/`women`, omit India (configured separately in Phase 2), and include colour when useful. Material and other attributes are included only when relevant.

Gemini retries only transient or rate-limit responses with bounded exponential backoff, controlled by `PHASE1_GEMINI_MAX_ATTEMPTS` and `PHASE1_GEMINI_RETRY_BASE_SECONDS`.