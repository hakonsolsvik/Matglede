# Graph Report - matglede  (2026-11-24)

## Corpus Check
- 40 files · ~64,521 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 2, .example 1, .webmanifest 1)

## Summary
- 554 nodes · 1079 edges · 28 communities (21 shown, 7 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 62 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1987ebd0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- test_core.py
- re
- __main__.py
- pantry_test.js
- offers.py
- db.py
- support.js
- json
- steps
- varer.yml
- pantry.js
- forpriser.py
- getReact
- steps
- createExternalModules
- createRuntime
- package.json
- Mat-appen (Matglede): varedatabase for oppskrifter og handleliste
- ShoppingListTest
- auth.js
- boot
- createRegistry
- Matglede – notater for Claude
- AI for «Min beholdning», «Mine oppskrifter» og tilbudsavisene

## God Nodes (most connected - your core abstractions)
1. `score_product()` - 21 edges
2. `createRuntime()` - 15 edges
3. `main()` - 15 edges
4. `import_ingredient()` - 15 edges
5. `tag_offers()` - 15 edges
6. `IngredientRule` - 14 edges
7. `candidates()` - 14 edges
8. `KassalClient` - 12 edges
9. `parse_package()` - 12 edges
10. `shopping_list()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Appen (app/)` --references--> `pick_product()`  [INFERRED]
  README.md → matglede/shopping.py
- `MatchingTest` --uses--> `IngredientRule`  [INFERRED]
  tests/test_core.py → matglede/matching.py
- `import_ingredient()` --uses--> `IngredientRule`  [INFERRED]
  matglede/importer.py → matglede/matching.py
- `build_offers()` --uses--> `KassalClient`  [INFERRED]
  matglede/offers.py → matglede/kassal.py
- `tag_offers()` --uses--> `IngredientRule`  [INFERRED]
  matglede/offers.py → matglede/matching.py

## Import Cycles
- None detected.

## Communities (28 total, 7 thin omitted)

### Community 0 - "test_core.py"
Cohesion: 0.07
Nodes (26): base_amount(), build(), _candidates(), previous_products(), write(), _contains_word(), _excluded(), excluded_name() (+18 more)

### Community 1 - "re"
Cohesion: 0.07
Nodes (23): box(), build_store(), fetch(), nice(), pick(), see_products(), variants(), write() (+15 more)

### Community 2 - "__main__.py"
Cohesion: 0.10
Nodes (22): _categories(), import_all(), import_ingredient(), link(), _now(), _price_date(), upsert_offer(), upsert_product() (+14 more)

### Community 3 - "pantry_test.js"
Cohesion: 0.06
Nodes (31): assert, fs, html, o, path, assert, ings, KNOWN (+23 more)

### Community 4 - "offers.py"
Cohesion: 0.11
Nodes (16): _ingredients_csv(), coop(), coop_pages(), flyer_for(), _get(), norgesgruppen(), build_offers(), offer_from_product() (+8 more)

### Community 5 - "db.py"
Cohesion: 0.11
Nodes (9): connect(), create_meal_plan(), init_db(), load_ingredients(), load_recipes(), load(), cmd_init(), AppExportTest (+1 more)

### Community 6 - "support.js"
Cohesion: 0.10
Nodes (18): cdnScriptFor(), compileTemplate(), contentKey(), createPseudoSheet(), dcNameFromPath(), encodeCamelAttrs(), encodeCase(), findTopLevelEquality() (+10 more)

### Community 7 - "json"
Cohesion: 0.11
Nodes (9): clean(), flyer_content(), read_flyer(), read_flyers(), write_offers_js(), FakeClient, FakeStream, FlyerAiTest (+1 more)

### Community 8 - "steps"
Cohesion: 0.07
Nodes (28): concurrency, cancel-in-progress, group, env, ANTHROPIC_API_KEY, APP_BRANCH, KASSAL_API_KEY, jobs (+20 more)

### Community 9 - "varer.yml"
Cohesion: 0.07
Nodes (26): concurrency, cancel-in-progress, group, env, APP_BRANCH, KASSAL_API_KEY, jobs, varer (+18 more)

### Community 10 - "pantry.js"
Cohesion: 0.17
Nodes (22): amount(), canon(), cap(), counted(), find(), fresh(), have(), key() (+14 more)

### Community 11 - "forpriser.py"
Cohesion: 0.15
Nodes (9): fetch(), _get(), keep_tagged(), load(), merge(), to_offer(), write(), ForpriserTest (+1 more)

### Community 12 - "getReact"
Cohesion: 0.25
Nodes (18): collectProps(), compileAttr(), cssToObj(), getReact(), hostPositionStyle(), isDeckMountTag(), kebabToCamel(), renderDeckKids() (+10 more)

### Community 13 - "steps"
Cohesion: 0.11
Nodes (17): runs-on, steps, ANTHROPIC_API_KEY, jobs, aviser, name, on, push (+9 more)

### Community 14 - "createExternalModules"
Cohesion: 0.17
Nodes (14): bundledBlob(), createExternalModules(), ensureBabel(), load(), resolveGlobal(), waitForGlobal(), createHelmetManager(), applyCanvasBg() (+6 more)

### Community 15 - "createRuntime"
Cohesion: 0.24
Nodes (11): createComponentFactory(), getDC(), createRuntime(), adoptParsed(), dcUpdate(), ensureFetched(), setStreaming(), updateHtml() (+3 more)

### Community 16 - "package.json"
Cohesion: 0.18
Nodes (12): @anthropic-ai/sdk, wrangler, dependencies, @anthropic-ai/sdk@^1.0.0, devDependencies, wrangler@^4.0.0, name, private (+4 more)

### Community 17 - "Mat-appen (Matglede): varedatabase for oppskrifter og handleliste"
Cohesion: 0.18
Nodes (10): Appen (app/), Datamodell, Kom i gang, Mat-appen (Matglede): varedatabase for oppskrifter og handleliste, Neste steg, Populære oppskrifter fra Rema 1000, Aichas Mat og Marit Kolby, Sette opp innlogging (Firebase), Slik lages handlelisten (+2 more)

### Community 19 - "auth.js"
Cohesion: 0.39
Nodes (6): emit(), FV(), load(), setHousehold(), start(), toUser()

### Community 20 - "boot"
Cohesion: 0.29
Nodes (7): boot(), createStreamTracker(), getReactDOM(), init(), parseDataProps(), parseDcDocument(), parseDcText()

### Community 21 - "createRegistry"
Cohesion: 1.00
Nodes (3): createRegistry(), bump(), get()

## Knowledge Gaps
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `pick_product()` connect `test_core.py` to `Mat-appen (Matglede): varedatabase for oppskrifter og handleliste`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `createRuntime()` (e.g. with `adoptParsed()` and `dcUpdate()`) actually correct?**
  _`createRuntime()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_core.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0675990675990676 - nodes in this community are weakly interconnected._
- **Why does `Appen (app/)` connect `Mat-appen (Matglede): varedatabase for oppskrifter og handleliste` to `test_core.py`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `main()` (e.g. with `cmd_compare()` and `cmd_demo_plan()`) actually correct?**
  _`main()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `re` be split into smaller, more focused modules?**
  _Cohesion score 0.07184325108853411 - nodes in this community are weakly interconnected._
- **Why does `score_product()` connect `test_core.py` to `re`, `__main__.py`, `offers.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._