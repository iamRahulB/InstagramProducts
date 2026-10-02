# AI Fashion Discovery & Affiliate Commerce System

## Project Goal

Build a modular, production-ready AI-powered fashion discovery and affiliate-commerce system for Instagram.

The system will eventually:

1. Understand current date, seasonal context, occasions and relevant fashion context.
2. Generate one complete, internally coordinated fashion outfit.
3. Break that outfit into individual purchasable products.
4. Generate one commercially useful search query for every product.
5. Find real products, primarily from **Myntra, Amazon India and Flipkart**, using SerpApi.
6. Filter and rank those real products against the intended outfit.
7. Generate or retrieve verified affiliate links.
8. Generate a professional fashion image using the actual selected product references.
9. Publish the content to Instagram.
10. Store the relationship between the Instagram post, outfit and exact products.
11. Detect comments such as `LINK`.
12. Return the exact product/affiliate links associated with that post.
13. Track engagement, clicks, conversions and commission.
14. Eventually use historical performance data to improve future outfit generation.

Core principle:

> AI decides WHAT outfit/products are needed.
> Product-search APIs determine WHERE real products can be found.
> The system owns real product data, URLs, prices, IDs and affiliate links.

The LLM must never invent real product URLs, prices, retailers, product IDs or affiliate links.

---

## Current Development Status

### Phase 1 — COMPLETED

Phase 1 is already implemented.

It is the **Fashion Context & Outfit Planner**.

It currently generates one complete outfit with:

- `research_id`
- `outfit_id`
- `generated_at`
- `country`
- calendar/date context
- occasion
- fashion direction
- reasoning
- gender
- outfit concept
- individual outfit items
- visual requirements for every item
- one `search_query` for every item
- warnings

The current Phase 1 implementation and approach are the source of truth.

### IMPORTANT

Do **not** redesign or rewrite Phase 1 merely because this document describes the overall future architecture.

Phase 1 has already been implemented and tested.

Future phases must consume the existing Phase 1 output.

If an improvement to Phase 1 becomes genuinely necessary later, make it only when required by a concrete integration problem and preserve backward compatibility wherever practical.

The current goal is to move forward phase-by-phase.

---

## Development Strategy — VERY IMPORTANT

The project must be developed **one phase at a time**.

This document describes the complete future system for context. It is NOT an instruction to implement every phase now.

When the developer explicitly says to start a phase:

- implement only that phase
- make it consume the previous phase's output
- update `main.py` only as necessary to run the implemented chain
- test the chain from Phase 1 through the newly implemented phase
- do NOT implement later phases

Example:

If asked to start Phase 2:

```text
Phase 1 → Phase 2
```

Do NOT implement Phase 3, affiliate logic, image generation, Instagram automation, analytics, or learning.

---

## Main.py Execution Model

For now, `main.py` can act as the phase runner/orchestrator.

Example:

```text
main.py
   ↓
Phase 1
   ↓
Phase 1 output
   ↓
Phase 2
   ↓
Phase 2 output
```

Later:

```text
main.py
   ↓
Phase 1
   ↓
Phase 2
   ↓
Phase 3
   ↓
Phase 4
   ↓
...
```

Each phase must still have a clean input/output contract.

Do not make a phase depend on another phase's internal implementation details. A phase should consume the previous phase's output.

When developing Phase 2, running the application should actually execute Phase 1 first and pass its real output into Phase 2. Do not test Phase 2 only with fabricated Phase 1 input.

---

## Complete Future Pipeline

```text
PHASE 1
Fashion Context & Outfit Planner
        ↓
PHASE 2
Real Product Discovery
        ↓
PHASE 3
Product Filtering & Outfit Matching
        ↓
PHASE 4
Affiliate Link Generation
        ↓
PHASE 5
AI Fashion Image Generation
        ↓
PHASE 6
Image Post-Processing
        ↓
PHASE 7
Instagram Publishing
        ↓
PHASE 8
Post / Outfit / Product Mapping
        ↓
PHASE 9
Instagram Comment Detection
        ↓
PHASE 10
Automated Product Link Response
        ↓
PHASE 11
Analytics
        ↓
PHASE 12
Learning & Optimization
```

Only implement the phase explicitly requested.

---

# PHASE 1 — Fashion Context & Outfit Planner

## Status

COMPLETED.

## Responsibility

Determine:

> WHAT should the outfit contain?

Phase 1 uses calendar/date context and AI reasoning to create one complete outfit.

It does not discover real products, generate affiliate links, or generate the final fashion image.

### Outfit relationship rules

One run produces one complete outfit.

The outfit can be male or female.

Male and female outfits are independent. They may share broad external context such as Dussehra, Diwali, festive season, monsoon, winter, etc., but they are not coordinated with each other.

Products within one outfit ARE coordinated.

Example:

```text
Male:
Kurta
  ↓
Pants
  ↓
Loafers
  ↓
Watch
```

The pants should complement the kurta, shoes should complement the outfit, and the watch should complement the overall styling.

Likewise:

```text
Female:
Crop top
  ↓
Lehenga
  ↓
Earrings
  ↓
Heels
  ↓
Clutch
```

All items should work together in color, style, silhouette, formality, occasion, material and overall visual direction.

### Phase 1 search queries

Every item contains one commercially useful `search_query`.

Example:

```json
{
  "category": "pants",
  "subcategory": "chinos",
  "visual_requirements": {
    "color": "olive green",
    "fit": "slim fit",
    "material": "cotton twill"
  },
  "search_query": "men olive green chinos slim fit cotton twill"
}
```

Queries should be specific and commercially searchable, but not unnecessarily long.

### Calendar rule

Calendar/date information is the source of truth for dates, occasions and days remaining until known occasions.

AI may interpret the supplied context but must not fabricate calendar facts.

Conceptually:

```text
Calendar/date source
        ↓
Known context
        ↓
AI interpretation
        ↓
Fashion direction
        ↓
One outfit
```

### India market

The initial target market is India.

Do not introduce unnecessary state/city-specific assumptions.

---

# PHASE 2 — Real Product Discovery

## Status

NOT IMPLEMENTED YET.

This is the next phase to implement when explicitly requested.

## Responsibility

Determine:

> WHERE can we find real products matching the Phase 1 requirements?

Phase 2 consumes the Phase 1 output.

For every Phase 1 item:

```text
Phase 1 item
    ↓
search_query
    ↓
SerpApi
    ↓
real product candidates
```

### Target retailers

The primary target retailers are:

1. **Myntra**
2. **Amazon India**
3. **Flipkart**

SerpApi product discovery should filter or prioritize results from these target domains.

Primary domains:

```text
myntra.com
amazon.in
flipkart.com
```

The architecture must remain extensible so additional retailers can be added later.

Use configurable retailer/domain definitions where practical.

### Product information

Where available, preserve:

- product title
- product URL
- retailer
- retailer/domain
- price
- currency
- rating
- review count
- product image
- thumbnail
- product ID
- source
- availability
- original search query
- original Phase 1 item/category

Never invent missing information.

### Phase 2 must NOT

- invent products
- invent prices
- invent product URLs
- invent retailer names
- generate affiliate links
- generate the final fashion image
- implement Phase 3 ranking
- implement Instagram logic

Phase 2 is responsible for discovery only.

### Phase 2 output

Preserve the relationship:

```text
research_id
    ↓
outfit_id
    ↓
item/category
    ↓
search_query
    ↓
discovered products
```

The exact schema can be improved by the engineer if necessary, but this traceability must remain.

---

# PHASE 3 — Product Filtering & Outfit Matching

## Status

NOT IMPLEMENTED.

Do not implement while working on Phase 2.

## Responsibility

Determine:

> WHICH discovered real products form the best coordinated version of the Phase 1 outfit?

Phase 2 may return many candidates per item.

Phase 3 evaluates them as an outfit, not independently.

Consider:

- color compatibility
- style compatibility
- silhouette
- material
- fit
- occasion
- formality
- visual consistency
- similarity to Phase 1 requirements
- product relevance
- availability
- commercial usefulness

The goal is a coordinated real-product outfit.

---

# PHASE 4 — Affiliate Link Generation

## Status

NOT IMPLEMENTED.

Potential sources:

- Myntra
- Amazon
- Flipkart
- other supported affiliate networks

Affiliate integrations should use provider/adaptor interfaces.

Critical rule:

> The LLM must never invent affiliate URLs.

The system owns verified product and affiliate data.

---

# PHASE 5 — AI Fashion Image Generation

## Status

NOT IMPLEMENTED.

Use the actual selected product images as references.

```text
Selected real products
        ↓
Product reference images
        ↓
AI image generation
        ↓
Professional fashion image
```

Preserve actual product characteristics such as color, pattern, material appearance, shape, silhouette, construction and hardware where possible.

Do not replace real selected products with fictional alternatives.

Image generation must be provider-agnostic.

---

# PHASE 6 — Image Post-Processing

## Status

NOT IMPLEMENTED.

Potential operations:

- crop
- resize
- Instagram formatting
- quality optimization
- product callouts
- retailer labels
- price labels
- arrows
- branding
- layout adjustments

Do not alter the identity of selected products.

---

# PHASE 7 — Instagram Publishing

## Status

NOT IMPLEMENTED.

Publish the final image and caption to Instagram.

Possible CTA:

```text
Want the links?
Comment "LINK"
```

The Instagram `media_id` becomes the identifier for downstream mapping.

---

# PHASE 8 — Post / Outfit / Product Mapping

## Status

NOT IMPLEMENTED.

Maintain:

```text
Instagram media_id
        ↓
outfit_id
        ↓
selected products
        ↓
affiliate URLs
```

This mapping is essential for the automated LINK workflow.

---

# PHASE 9 — Instagram Comment Detection

## Status

NOT IMPLEMENTED.

Use Instagram API/webhooks to detect comments.

Example:

```text
User comments:
LINK
```

Then:

```text
comment
   ↓
media_id
   ↓
outfit_id
```

Never guess which outfit the user means. The Instagram media/post ID is the source of truth.

---

# PHASE 10 — Automated Product Link Response

## Status

NOT IMPLEMENTED.

Flow:

```text
Comment
   ↓
media_id
   ↓
outfit_id
   ↓
selected products
   ↓
verified affiliate URLs
   ↓
DM/private response
```

URLs must come from stored verified affiliate data.

LLM may format the response but must not fabricate URLs.

---

# PHASE 11 — Analytics

## Status

NOT IMPLEMENTED.

Potential Instagram metrics:

- impressions
- reach
- likes
- comments
- saves
- shares
- profile visits
- follows

Potential commerce metrics:

- LINK requests
- affiliate clicks
- product clicks
- conversions
- orders
- commission
- revenue

Maintain:

```text
post
 ↓
outfit
 ↓
product
 ↓
affiliate link
 ↓
click
 ↓
conversion
 ↓
commission
```

---

# PHASE 12 — Learning & Optimization

## Status

NOT IMPLEMENTED.

Eventually use actual performance data to improve future outfit generation.

Potential signals:

```text
Outfit
 ↓
Impressions
 ↓
Engagement
 ↓
LINK requests
 ↓
Affiliate clicks
 ↓
Conversions
 ↓
Commission
```

Possible optimization targets:

- colors
- styles
- outfit concepts
- product categories
- accessories
- gender-specific patterns
- occasions
- image styles
- captions
- posting strategies

Use actual collected data rather than unsupported assumptions.

---

# Data Ownership Rules

## AI may decide

- fashion direction
- outfit concept
- gender
- product categories
- visual requirements
- search queries
- styling
- descriptive text
- captions

## System/external APIs must provide

- real product
- product URL
- product image
- retailer
- price
- product ID
- affiliate URL
- Instagram media ID
- analytics data

Never hallucinate commerce data.

---

# Provider-Agnostic Architecture

Use provider/adaptor abstractions where practical.

Examples:

```text
AIProvider
 ├── AWS implementation
 └── Gemini implementation
```

Potential future interfaces:

```text
ProductSearchProvider
AffiliateProvider
ImageGenerationProvider
InstagramProvider
NotificationProvider
```

Providers should be replaceable without rewriting core business logic.

---

# Configuration

Use `.env` for:

- API keys
- secrets
- credentials
- runtime configuration

Provide `.env.example`.

Never commit secrets.

Do not use Google Sheets as the primary configuration system.

Static configuration may use YAML/JSON where appropriate.

---

# Discord

Discord is a private notification/logging channel.

It may receive:

- research results
- discovered products
- selected products
- generated images
- affiliate links
- Instagram post information
- errors
- warnings
- pipeline status

Discord must not be a hard dependency for the core pipeline.

---

# Ubuntu / Scheduling

The target runtime is an Ubuntu server.

For now, phases must be runnable manually.

Later, Ubuntu cron can execute the main application.

Cron is only the scheduler. The application must remain independently runnable.

---

# Persistence and Traceability

Important outputs should be persisted.

Possible structure:

```text
data/
├── research/
├── products/
├── outfits/
├── affiliate/
├── images/
├── instagram/
└── analytics/
```

Maintain:

```text
research_id
    ↓
outfit_id
    ↓
item_id
    ↓
product_id
    ↓
affiliate_link_id
    ↓
image_id
    ↓
instagram_media_id
    ↓
comment_id
    ↓
click/conversion
```

The entire lifecycle of an Instagram post should eventually be reconstructable.

---

# Error Handling

Every phase must handle failures safely.

Possible failures:

- AI timeout
- malformed JSON
- SerpApi failure
- no products found
- poor product results
- affiliate API failure
- image generation failure
- Instagram failure
- webhook failure

Use where appropriate:

- timeouts
- retries
- exponential backoff
- structured logging
- schema validation
- warnings
- graceful failure

Never silently propagate invalid data.

---

# Testing

Every phase should have tests.

External APIs should be mocked in unit tests.

Tests should cover:

- configuration
- schema validation
- date/calendar logic
- query generation
- gender handling
- outfit completeness
- internal outfit relationships
- product mapping
- SerpApi parsing
- retailer filtering
- provider adapters
- error handling
- retries
- persistence
- phase-to-phase contracts

---

# Modular Architecture

Do not build one giant script.

Use modular phase implementations, for example:

```text
phase1/
phase2/
phase3/
phase4/
phase5/
...
```

with shared infrastructure such as:

```text
providers/
models/
config/
storage/
logging/
utils/
```

The exact directory structure may be improved by the engineer.

The important requirement is loose coupling and clean phase boundaries.

---

# Development Rules for Copilot

Before implementing or modifying anything:

1. Read this `GOAL.md`.
2. Inspect the existing repository.
3. Understand which phases are already implemented.
4. Preserve the existing Phase 1 approach and behavior.
5. Do not redesign Phase 1 just because future architecture is described here.
6. Implement only the phase explicitly requested.
7. Make the new phase consume the previous phase's actual output.
8. Update `main.py` only as necessary to run the implemented chain.
9. Test the complete chain from Phase 1 through the newly implemented phase.
10. Do not implement future phases early.
11. Keep external services behind adapters/providers where practical.
12. Keep secrets out of source code.
13. Add validation and tests.
14. Use structured logging and meaningful errors.
15. You are free to improve architecture, interfaces, libraries or implementation when engineering judgment identifies a better solution.
16. Such improvements must preserve the existing Phase 1 contract and the overall business flow.
17. Do not reintroduce Google Search into Phase 1 unless explicitly requested.
18. Do not reintroduce Google Sheets as the primary configuration system.
19. Do not couple male and female outfits to each other.
20. Maintain strong internal coordination between products within one outfit.
21. Never hallucinate real products, prices, URLs, retailers or affiliate links.
22. Prefer system-owned verified data for commerce and Instagram mappings.
23. Every phase must be independently testable.
24. If a phase is run independently, it should produce its documented output or a clear actionable error.

---

# Current Next Step

Phase 1 is COMPLETED.

Phase 2 is the next phase to implement.

When explicitly asked to start Phase 2:

1. Inspect the existing Phase 1 implementation.
2. Do not rewrite Phase 1 unnecessarily.
3. Read the actual Phase 1 output produced by the current code.
4. Build only the Phase 2 module.
5. Use every Phase 1 item's `search_query`.
6. Use SerpApi for product discovery.
7. Prioritize/filter results for:
   - Myntra
   - Amazon India
   - Flipkart
8. Preserve:
   - research_id
   - outfit_id
   - item/category
   - search_query
   - discovered products
9. Normalize real product results.
10. Handle empty results and API failures safely.
11. Update `main.py` so it executes:
    **Phase 1 → Phase 2**
12. Run/test the complete chain.
13. Do NOT implement Phase 3 or any later phase.

---

# Final Business Principle

The system should transform:

> "I like this outfit."

into:

> "Here are the exact real products used in this outfit and where you can buy them."

while maintaining a machine-readable relationship between:

```text
fashion context
→ outfit
→ individual items
→ search queries
→ real products
→ selected products
→ affiliate links
→ generated image
→ Instagram post
→ user comment
→ exact product response
→ clicks
→ conversions
→ analytics
→ future optimization
```

The final system is a closed-loop AI fashion discovery and affiliate-commerce engine.
