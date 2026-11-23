# Graph Report - matglede  (2026-11-23)

## Corpus Check
- 29 files · ~49,841 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 2, .example 1, .webmanifest 1)

## Summary
- 420 nodes · 874 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `97968ac5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_core.py
- __main__.py
- external.py
- offers.py
- support.js
- db.py
- steps
- index.js
- score_product
- pantry.js
- getReact
- createExternalModules
- createRuntime
- package.json
- Mat-appen (Matglede): varedatabase for oppskrifter og handleliste
- ShoppingListTest
- auth.js
- boot
- createRegistry
- AI for «Min beholdning» og «Mine oppskrifter»

## God Nodes (most connected - your core abstractions)
1. `score_product()` - 21 edges
2. `createRuntime()` - 15 edges
3. `import_ingredient()` - 15 edges
4. `IngredientRule` - 15 edges
5. `pick_product()` - 14 edges
6. `main()` - 13 edges
7. `KassalClient` - 13 edges
8. `parse_package()` - 12 edges
9. `shopping_list()` - 11 edges
10. `ShoppingListTest` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Appen (app/)` --references--> `pick_product()`  [INFERRED]
  README.md → matglede/shopping.py
- `MatchingTest` --uses--> `IngredientRule`  [INFERRED]
  tests/test_core.py → matglede/matching.py
- `_candidates()` --uses--> `IngredientRule`  [INFERRED]
  matglede/app_export.py → matglede/matching.py
- `import_ingredient()` --uses--> `IngredientRule`  [INFERRED]
  matglede/importer.py → matglede/matching.py
- `build_offers()` --uses--> `KassalClient`  [INFERRED]
  matglede/offers.py → matglede/kassal.py

## Import Cycles
- None detected.

## Communities (23 total, 5 thin omitted)

### Community 0 - "test_core.py"
Cohesion: 0.09
Nodes (23): base_amount(), build(), _candidates(), _ingredients_csv(), previous_products(), write(), cmd_export_app(), excluded_name() (+15 more)

### Community 1 - "__main__.py"
Cohesion: 0.10
Nodes (19): _categories(), import_all(), import_ingredient(), link(), _now(), _price_date(), upsert_offer(), upsert_product() (+11 more)

### Community 2 - "external.py"
Cohesion: 0.11
Nodes (15): _base_units(), build(), build_recipe(), coverage(), slugify(), _contains_word(), _has(), is_heading() (+7 more)

### Community 3 - "offers.py"
Cohesion: 0.12
Nodes (14): coop(), coop_pages(), flyer_for(), _get(), norgesgruppen(), build_offers(), offer_from_product(), top_category() (+6 more)

### Community 4 - "support.js"
Cohesion: 0.10
Nodes (18): cdnScriptFor(), compileTemplate(), contentKey(), createPseudoSheet(), dcNameFromPath(), encodeCamelAttrs(), encodeCase(), findTopLevelEquality() (+10 more)

### Community 5 - "db.py"
Cohesion: 0.12
Nodes (9): connect(), create_meal_plan(), init_db(), load_ingredients(), load_recipes(), load(), cmd_init(), AppExportTest (+1 more)

### Community 6 - "steps"
Cohesion: 0.07
Nodes (27): concurrency, cancel-in-progress, group, env, APP_BRANCH, KASSAL_API_KEY, jobs, tilbud (+19 more)

### Community 7 - "index.js"
Cohesion: 0.10
Nodes (22): assert, KNOWN, lowRice, milk, pantry, R, R2, ranked (+14 more)

### Community 8 - "score_product"
Cohesion: 0.14
Nodes (9): _contains_anywhere(), _excluded(), IngredientRule, normalize(), score_product(), split_terms(), tag_offers(), MatchingTest (+1 more)

### Community 9 - "pantry.js"
Cohesion: 0.20
Nodes (21): amount(), canon(), cap(), counted(), find(), fresh(), have(), key() (+13 more)

### Community 10 - "getReact"
Cohesion: 0.25
Nodes (18): collectProps(), compileAttr(), cssToObj(), getReact(), hostPositionStyle(), isDeckMountTag(), kebabToCamel(), renderDeckKids() (+10 more)

### Community 11 - "createExternalModules"
Cohesion: 0.17
Nodes (14): bundledBlob(), createExternalModules(), ensureBabel(), load(), resolveGlobal(), waitForGlobal(), createHelmetManager(), applyCanvasBg() (+6 more)

### Community 12 - "createRuntime"
Cohesion: 0.24
Nodes (11): createComponentFactory(), getDC(), createRuntime(), adoptParsed(), dcUpdate(), ensureFetched(), setStreaming(), updateHtml() (+3 more)

### Community 13 - "package.json"
Cohesion: 0.18
Nodes (12): @anthropic-ai/sdk, wrangler, dependencies, @anthropic-ai/sdk@^1.0.0, devDependencies, wrangler@^4.0.0, name, private (+4 more)

### Community 14 - "Mat-appen (Matglede): varedatabase for oppskrifter og handleliste"
Cohesion: 0.18
Nodes (10): Appen (app/), Datamodell, Kom i gang, Mat-appen (Matglede): varedatabase for oppskrifter og handleliste, Neste steg, Populære oppskrifter fra Rema 1000, Aichas Mat og Marit Kolby, Sette opp innlogging (Firebase), Slik lages handlelisten (+2 more)

### Community 16 - "auth.js"
Cohesion: 0.39
Nodes (6): emit(), FV(), load(), setHousehold(), start(), toUser()

### Community 17 - "boot"
Cohesion: 0.29
Nodes (7): boot(), createStreamTracker(), getReactDOM(), init(), parseDataProps(), parseDcDocument(), parseDcText()

### Community 18 - "createRegistry"
Cohesion: 1.00
Nodes (3): createRegistry(), bump(), get()

## Knowledge Gaps
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `pick_product()` connect `test_core.py` to `score_product`, `Mat-appen (Matglede): varedatabase for oppskrifter og handleliste`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `createRuntime()` (e.g. with `adoptParsed()` and `dcUpdate()`) actually correct?**
  _`createRuntime()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09308510638297872 - nodes in this community are weakly interconnected._
- **Why does `Appen (app/)` connect `Mat-appen (Matglede): varedatabase for oppskrifter og handleliste` to `test_core.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `import_ingredient()` (e.g. with `KassalClient` and `.search_products()`) actually correct?**
  _`import_ingredient()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `__main__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10128205128205128 - nodes in this community are weakly interconnected._
- **Why does `IngredientRule` connect `score_product` to `test_core.py`, `__main__.py`, `offers.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._