# Graph Report - Matglede  (2026-11-23)

## Corpus Check
- 55 files · ~70,190 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .example 1, .webmanifest 1)

## Summary
- 506 nodes · 989 edges · 25 communities (20 shown, 5 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 82 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- App-logikk og handleliste
- Eksport av appdata
- Tilbudsaviser og Kassalapp
- Eksterne oppskrifter
- Database og startdata
- Claude Design-runtime
- Ukentlig tilbud-workflow
- Ingrediensmatching
- Produktimport
- Spiskammer-tester
- Skjermbilder og innstillinger
- Login, AI og navigasjon
- Spiskammer-logikk
- Runtime-rendering
- Runtime-moduler
- Runtime-komponenter
- AI-worker oppsett
- Handleliste-tester
- Runtime-oppstart
- Firebase-login
- Teller-register
- Glemt passord

## God Nodes (most connected - your core abstractions)
1. `score_product()` - 21 edges
2. `createRuntime()` - 15 edges
3. `import_ingredient()` - 15 edges
4. `IngredientRule` - 15 edges
5. `main()` - 13 edges
6. `KassalClient` - 13 edges
7. `pick_product()` - 13 edges
8. `parse_package()` - 12 edges
9. `shopping_list()` - 11 edges
10. `ShoppingListTest` - 11 edges

## Surprising Connections (you probably didn't know these)
- `pickPack cheapest whole packs` --semantically_similar_to--> `shopping.pick_product`  [INFERRED] [semantically similar]
  app/index.html → README.md
- `renderVals` --references--> `Grocery chains (Oda, Kiwi, Meny, Rema 1000, Coop, Spar, Joker)`  [INFERRED]
  app/index.html → README.md
- `MatchingTest` --uses--> `IngredientRule`  [INFERRED]
  tests/test_core.py → matglede/matching.py
- `buildShop shopping list builder` --implements--> `Shopping list generation`  [INFERRED]
  app/index.html → README.md
- `STORES flyer store list` --implements--> `Tilbud page (weekly offers)`  [INFERRED]
  app/index.html → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Claude worker flow for pantry and recipe photos** — app_index_askai, app_index_scanphoto, app_index_scanrecipe, app_index_jpeg, worker_readme_ai_worker [INFERRED 0.85]
- **Shopping list pricing pipeline** — app_index_buildshop, app_index_pickpack, app_index_prods, app_index_homerun, readme_shopping_list_algorithm [INFERRED 0.85]
- **Ingredient/product/offer data model** — readme_ingredient, readme_product, readme_offer, readme_ingredient_product [EXTRACTED 1.00]
- **Store selection drives shopping-list pricing and color** — docs_skjermbilder_innstillinger_24t_price_store_selector, docs_skjermbilder_handleliste_butikkfarger_store_price_chips, docs_skjermbilder_handleliste_butikkfarger_basket_summary_card, docs_skjermbilder_handleliste_butikkfarger_store_brand_theming [INFERRED 0.85]
- **Ways items enter the shopping list** — docs_skjermbilder_mork_modus_shopping_list, docs_skjermbilder_populaere_varer_quick_add_items, docs_skjermbilder_mork_modus_cheaper_version [INFERRED 0.75]

## Communities (25 total, 5 thin omitted)

### Community 0 - "App-logikk og handleliste"
Cohesion: 0.05
Nodes (51): addToPlan, applyMine [merge own recipes into D.R), buildShop shopping list builder, cheapIng savings swaps [sparegris), Component [DCLogic app logic), costText [ca./minst X kr), D data bootstrap [MATGLEDE_DATA, offers, topics, articles), fmt amount formatter (+43 more)

### Community 1 - "Eksport av appdata"
Cohesion: 0.09
Nodes (29): base_amount(), build(), _candidates(), _ingredients_csv(), previous_products(), write(), load_dotenv(), cmd_compare() (+21 more)

### Community 2 - "Tilbudsaviser og Kassalapp"
Cohesion: 0.10
Nodes (13): coop(), coop_pages(), flyer_for(), _get(), norgesgruppen(), build_offers(), offer_from_product(), top_category() (+5 more)

### Community 3 - "Eksterne oppskrifter"
Cohesion: 0.11
Nodes (16): build(), build_recipe(), coverage(), slugify(), _has(), is_heading(), match_ingredient(), normalise_for_ingredient() (+8 more)

### Community 4 - "Database og startdata"
Cohesion: 0.11
Nodes (10): connect(), create_meal_plan(), init_db(), load_ingredients(), load_recipes(), _base_units(), load(), cmd_init() (+2 more)

### Community 5 - "Claude Design-runtime"
Cohesion: 0.10
Nodes (18): cdnScriptFor(), compileTemplate(), contentKey(), createPseudoSheet(), dcNameFromPath(), encodeCamelAttrs(), encodeCase(), findTopLevelEquality() (+10 more)

### Community 6 - "Ukentlig tilbud-workflow"
Cohesion: 0.07
Nodes (27): concurrency, cancel-in-progress, group, env, APP_BRANCH, KASSAL_API_KEY, jobs, tilbud (+19 more)

### Community 7 - "Ingrediensmatching"
Cohesion: 0.13
Nodes (11): _contains_anywhere(), _contains_word(), _excluded(), excluded_name(), IngredientRule, normalize(), score_product(), split_terms() (+3 more)

### Community 8 - "Produktimport"
Cohesion: 0.15
Nodes (12): _categories(), import_all(), import_ingredient(), link(), _now(), _price_date(), upsert_offer(), upsert_product() (+4 more)

### Community 9 - "Spiskammer-tester"
Cohesion: 0.10
Nodes (22): assert, KNOWN, lowRice, milk, pantry, R, R2, ranked (+14 more)

### Community 10 - "Skjermbilder og innstillinger"
Cohesion: 0.10
Nodes (25): Basket summary card ('2 av 25 i kurven'), Rema 1000 total ca. 107 kr (outlier), Shopping list store colors screenshot, Store brand color theming, Store price chips (Oda/Kiwi/Meny ...), Appearance setting (Automatisk/Lys/Mork), Default number of persons (2/4/6), Image credits (Wikimedia Commons) (+17 more)

### Community 11 - "Login, AI og navigasjon"
Cohesion: 0.11
Nodes (23): addPantry, askAI worker call, authRun / submitLogin / googleLogin, componentDidMount, componentDidUpdate [localStorage + history), fromHash / hashOf URL routing, jpeg image downscaler, listen [Web Speech API voice input) (+15 more)

### Community 12 - "Spiskammer-logikk"
Cohesion: 0.20
Nodes (21): amount(), canon(), cap(), counted(), find(), fresh(), have(), key() (+13 more)

### Community 13 - "Runtime-rendering"
Cohesion: 0.25
Nodes (18): collectProps(), compileAttr(), cssToObj(), getReact(), hostPositionStyle(), isDeckMountTag(), kebabToCamel(), renderDeckKids() (+10 more)

### Community 14 - "Runtime-moduler"
Cohesion: 0.17
Nodes (14): bundledBlob(), createExternalModules(), ensureBabel(), load(), resolveGlobal(), waitForGlobal(), createHelmetManager(), applyCanvasBg() (+6 more)

### Community 15 - "Runtime-komponenter"
Cohesion: 0.24
Nodes (11): createComponentFactory(), getDC(), createRuntime(), adoptParsed(), dcUpdate(), ensureFetched(), setStreaming(), updateHtml() (+3 more)

### Community 16 - "AI-worker oppsett"
Cohesion: 0.18
Nodes (12): @anthropic-ai/sdk, wrangler, dependencies, @anthropic-ai/sdk@^1.0.0, devDependencies, wrangler@^4.0.0, name, private (+4 more)

### Community 18 - "Runtime-oppstart"
Cohesion: 0.29
Nodes (7): boot(), createStreamTracker(), getReactDOM(), init(), parseDataProps(), parseDcDocument(), parseDcText()

### Community 19 - "Firebase-login"
Cohesion: 0.53
Nodes (4): emit(), load(), start(), toUser()

### Community 20 - "Teller-register"
Cohesion: 1.00
Nodes (3): createRegistry(), bump(), get()

## Ambiguous Edges - Review These
- `Rema 1000 total ca. 107 kr (outlier)` → `Store for prices selector`  [AMBIGUOUS]
  docs/skjermbilder/handleliste-butikkfarger.png · relation: conceptually_related_to

## Knowledge Gaps
- **22 isolated node(s):** `recipe / recipe_ingredient tables`, `python -m matglede CLI`, `Link review (review/verify/reject)`, `matglede/flyers.py flyer embedding`, `.github/workflows/tilbud.yml` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 124 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `App (app/) from Claude Design` connect `App-logikk og handleliste` to `Login, AI og navigasjon`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `createRuntime()` (e.g. with `adoptParsed()` and `dcUpdate()`) actually correct?**
  _`createRuntime()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `recipe / recipe_ingredient tables`, `python -m matglede CLI`, `Link review (review/verify/reject)` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `App-logikk og handleliste` be split into smaller, more focused modules?**
  _Cohesion score 0.05254901960784314 - nodes in this community are weakly interconnected._
- **Why does `recipe_parse.PACK_SIZES` connect `App-logikk og handleliste` to `Eksterne oppskrifter`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `import_ingredient()` (e.g. with `KassalClient` and `.search_products()`) actually correct?**
  _`import_ingredient()` has 3 INFERRED edges - model-reasoned connections that need verification._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Rema 1000 total ca. 107 kr (outlier)` and `Store for prices selector`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._