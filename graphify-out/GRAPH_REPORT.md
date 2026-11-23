# Graph Report - matglede  (2026-11-23)

## Corpus Check
- 32 files · ~55,275 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 2, .example 1, .webmanifest 1)

## Summary
- 458 nodes · 905 edges · 25 communities (19 shown, 6 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e649d21b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- __main__.py
- offers.py
- index.js
- test_core.py
- db.py
- support.js
- steps
- score_product
- varer.yml
- importer.py
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
- Matglede – notater for Claude
- AI for «Min beholdning» og «Mine oppskrifter»

## God Nodes (most connected - your core abstractions)
1. `score_product()` - 21 edges
2. `createRuntime()` - 15 edges
3. `import_ingredient()` - 15 edges
4. `IngredientRule` - 14 edges
5. `candidates()` - 14 edges
6. `main()` - 13 edges
7. `KassalClient` - 12 edges
8. `parse_package()` - 12 edges
9. `shopping_list()` - 11 edges
10. `to_base()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Appen (app/)` --references--> `pick_product()`  [INFERRED]
  README.md → matglede/shopping.py
- `MatchingTest` --uses--> `IngredientRule`  [INFERRED]
  tests/test_core.py → matglede/matching.py
- `import_ingredient()` --uses--> `IngredientRule`  [INFERRED]
  matglede/importer.py → matglede/matching.py
- `build_offers()` --uses--> `KassalClient`  [INFERRED]
  matglede/offers.py → matglede/kassal.py
- `candidates()` --uses--> `IngredientRule`  [INFERRED]
  matglede/shopping.py → matglede/matching.py

## Import Cycles
- None detected.

## Communities (25 total, 6 thin omitted)

### Community 0 - "__main__.py"
Cohesion: 0.09
Nodes (28): base_amount(), build(), _candidates(), _ingredients_csv(), previous_products(), write(), load_dotenv(), cmd_compare() (+20 more)

### Community 1 - "offers.py"
Cohesion: 0.10
Nodes (13): coop(), coop_pages(), flyer_for(), _get(), norgesgruppen(), build_offers(), offer_from_product(), top_category() (+5 more)

### Community 2 - "index.js"
Cohesion: 0.07
Nodes (27): assert, fs, html, o, path, assert, KNOWN, lowRice (+19 more)

### Community 3 - "test_core.py"
Cohesion: 0.12
Nodes (14): build(), build_recipe(), coverage(), slugify(), _has(), is_heading(), match_ingredient(), normalise_for_ingredient() (+6 more)

### Community 4 - "db.py"
Cohesion: 0.11
Nodes (9): connect(), create_meal_plan(), init_db(), load_ingredients(), load_recipes(), load(), cmd_init(), AppExportTest (+1 more)

### Community 5 - "support.js"
Cohesion: 0.10
Nodes (18): cdnScriptFor(), compileTemplate(), contentKey(), createPseudoSheet(), dcNameFromPath(), encodeCamelAttrs(), encodeCase(), findTopLevelEquality() (+10 more)

### Community 6 - "steps"
Cohesion: 0.07
Nodes (27): concurrency, cancel-in-progress, group, env, APP_BRANCH, KASSAL_API_KEY, jobs, tilbud (+19 more)

### Community 7 - "score_product"
Cohesion: 0.14
Nodes (10): _contains_word(), _excluded(), excluded_name(), IngredientRule, normalize(), score_product(), split_terms(), tag_offers() (+2 more)

### Community 8 - "varer.yml"
Cohesion: 0.07
Nodes (26): concurrency, cancel-in-progress, group, env, APP_BRANCH, KASSAL_API_KEY, jobs, varer (+18 more)

### Community 9 - "importer.py"
Cohesion: 0.15
Nodes (12): _categories(), import_all(), import_ingredient(), link(), _now(), _price_date(), upsert_offer(), upsert_product() (+4 more)

### Community 10 - "pantry.js"
Cohesion: 0.18
Nodes (21): amount(), canon(), cap(), counted(), find(), fresh(), have(), key() (+13 more)

### Community 11 - "getReact"
Cohesion: 0.25
Nodes (18): collectProps(), compileAttr(), cssToObj(), getReact(), hostPositionStyle(), isDeckMountTag(), kebabToCamel(), renderDeckKids() (+10 more)

### Community 12 - "createExternalModules"
Cohesion: 0.17
Nodes (14): bundledBlob(), createExternalModules(), ensureBabel(), load(), resolveGlobal(), waitForGlobal(), createHelmetManager(), applyCanvasBg() (+6 more)

### Community 13 - "createRuntime"
Cohesion: 0.24
Nodes (11): createComponentFactory(), getDC(), createRuntime(), adoptParsed(), dcUpdate(), ensureFetched(), setStreaming(), updateHtml() (+3 more)

### Community 14 - "package.json"
Cohesion: 0.18
Nodes (12): @anthropic-ai/sdk, wrangler, dependencies, @anthropic-ai/sdk@^1.0.0, devDependencies, wrangler@^4.0.0, name, private (+4 more)

### Community 15 - "Mat-appen (Matglede): varedatabase for oppskrifter og handleliste"
Cohesion: 0.18
Nodes (10): Appen (app/), Datamodell, Kom i gang, Mat-appen (Matglede): varedatabase for oppskrifter og handleliste, Neste steg, Populære oppskrifter fra Rema 1000, Aichas Mat og Marit Kolby, Sette opp innlogging (Firebase), Slik lages handlelisten (+2 more)

### Community 17 - "auth.js"
Cohesion: 0.39
Nodes (6): emit(), FV(), load(), setHousehold(), start(), toUser()

### Community 18 - "boot"
Cohesion: 0.29
Nodes (7): boot(), createStreamTracker(), getReactDOM(), init(), parseDataProps(), parseDcDocument(), parseDcText()

### Community 19 - "createRegistry"
Cohesion: 1.00
Nodes (3): createRegistry(), bump(), get()

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `pick_product()` connect `__main__.py` to `Mat-appen (Matglede): varedatabase for oppskrifter og handleliste`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `createRuntime()` (e.g. with `adoptParsed()` and `dcUpdate()`) actually correct?**
  _`createRuntime()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `__main__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0889894419306184 - nodes in this community are weakly interconnected._
- **Why does `Appen (app/)` connect `Mat-appen (Matglede): varedatabase for oppskrifter og handleliste` to `__main__.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `import_ingredient()` (e.g. with `KassalClient` and `.search_products()`) actually correct?**
  _`import_ingredient()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `offers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0960960960960961 - nodes in this community are weakly interconnected._
- **Why does `score_product()` connect `score_product` to `importer.py`, `test_core.py`, `offers.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._