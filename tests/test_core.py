import json
import unittest
from datetime import datetime, timezone

from matglede import db, external
from matglede.recipe_parse import match_ingredient, normalise_for_ingredient, parse_line
from matglede.matching import IngredientRule, score_product
from matglede.shopping import compare_chains, shopping_list
from matglede.units import parse_package, to_base

NOW = datetime(2026, 11, 19, tzinfo=timezone.utc)
FRESH = "2026-11-18T08:00:00Z"
OLD = "2024-05-05T08:00:00Z"


class UnitsTest(unittest.TestCase):
    def test_parse_from_weight_field(self):
        self.assertEqual(parse_package("Hva som helst", 0.4, "kg"), (400.0, "g"))
        self.assertEqual(parse_package("Egg", 12, "piece"), (12.0, "stk"))

    def test_parse_from_name(self):
        self.assertEqual(parse_package("Kjøttdeig 14% Fett 400g First Price"), (400.0, "g"))
        self.assertEqual(parse_package("Lettmelk 1,75 l"), (1750.0, "ml"))
        self.assertEqual(parse_package("Mutti polpa 12x400g"), (4800.0, "g"))
        self.assertEqual(parse_package("Egg Frittgående M/L 12stk"), (12.0, "stk"))
        self.assertEqual(parse_package("Løk"), (None, None))

    def test_zero_weight_falls_back_to_name(self):
        self.assertEqual(parse_package("Hakkede tomater 390 g", 0, "kg"), (390.0, "g"))

    def test_to_base(self):
        self.assertEqual(to_base(6, "dl", "ml"), 600)
        self.assertEqual(to_base(2, "ss", "ml"), 30)
        self.assertEqual(to_base(1, "stk", "g", 120), 120)
        self.assertIsNone(to_base(1, "stk", "g", None))
        self.assertIsNone(to_base(1, "never", "g"))


class MatchingTest(unittest.TestCase):
    rule = IngredientRule(
        search_terms=["hvitløk"], must_include=[],
        exclude_terms=["pulver", "saus", "is"], category_hints=["løk"],
    )

    def test_plain_product_scores(self):
        s = score_product(self.rule, "Hvitløk 100g", ["Frukt & grønt", "Grønnsaker", "Løk"], FRESH, True, NOW)
        self.assertGreater(s, 5)

    def test_long_exclusion_matches_inside_word(self):
        self.assertIsNone(score_product(self.rule, "Hvitløkspulver 56g", [], FRESH, True, NOW))

    def test_short_exclusion_needs_word_start(self):
        self.assertIsNotNone(score_product(self.rule, "Hvitløk pris 100g", [], FRESH, True, NOW))

    def test_flavour_ranks_below_main_ingredient(self):
        main = score_product(self.rule, "Hvitløk 100g", [], FRESH, True, NOW)
        flav = score_product(self.rule, "Poteter med hvitløk 700 g", [], FRESH, True, NOW)
        self.assertTrue(flav is None or flav < main - 3)

    def test_stale_price_penalised(self):
        fresh = score_product(self.rule, "Hvitløk 100g", [], FRESH, True, NOW)
        old = score_product(self.rule, "Hvitløk 100g", [], OLD, True, NOW)
        self.assertGreater(fresh, old)

    def test_whole_word_with_endings(self):
        egg = IngredientRule(["egg"], [], [], [])
        self.assertIsNotNone(score_product(egg, "Økologiske egg 12 stk", [], FRESH, True, NOW))
        self.assertIsNone(score_product(egg, "Eggdeler 11 cm", [], FRESH, True, NOW))
        tomat = IngredientRule(["tomat"], [], [], [])
        self.assertIsNotNone(score_product(tomat, "Tomater klase 500 g", [], FRESH, True, NOW))

    def test_no_term_no_match(self):
        self.assertIsNone(score_product(self.rule, "Rødløk 500g", [], FRESH, True, NOW))


class ShoppingListTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        c = self.conn
        c.execute("""INSERT INTO ingredient(id, slug, name, base_unit, grams_per_piece, search_terms)
                     VALUES (1,'kjottdeig','Kjøttdeig','g',NULL,'kjøttdeig'),
                            (2,'lok','Løk','g',120,'løk'),
                            (3,'melk','Lettmelk','ml',NULL,'lettmelk')""")
        c.execute("INSERT INTO recipe(id, slug, name, servings) VALUES (1,'a','A',4),(2,'b','B',2)")
        c.execute("""INSERT INTO recipe_ingredient(recipe_id, ingredient_id, amount, unit) VALUES
                     (1,1,400,'g'),(1,2,1,'stk'),(2,1,300,'g'),(2,3,3,'dl')""")
        products = [
            (1, "ean:1", "Kjøttdeig 400g", 400, "g"),
            (2, "ean:2", "Kjøttdeig 1 kg", 1000, "g"),
            (3, "ean:3", "Løk 1 kg", 1000, "g"),
            (4, "ean:4", "Lettmelk 1 l", 1000, "ml"),
        ]
        for pid, key, name, amt, unit in products:
            c.execute("""INSERT INTO product(id, source_key, name, package_amount, package_unit, updated_at)
                         VALUES (?,?,?,?,?,'x')""", (pid, key, name, amt, unit))
        offers = [
            (1, "KIWI", 60.0, FRESH), (2, "KIWI", 179.0, FRESH), (3, "KIWI", 25.0, FRESH),
            (4, "KIWI", 22.0, FRESH),
            (1, "REMA", 55.0, OLD), (3, "REMA", 20.0, OLD),
        ]
        for pid, chain, price, d in offers:
            c.execute("""INSERT INTO offer(product_id, chain_code, store_name, price, price_date, fetched_at)
                         VALUES (?,?,?,?,?,'x')""", (pid, chain, f"p{pid}", price, d))
        for iid, pid, score in [(1, 1, 5), (1, 2, 4.5), (2, 3, 5), (3, 4, 5)]:
            c.execute("INSERT INTO ingredient_product(ingredient_id, product_id, score) VALUES (?,?,?)",
                      (iid, pid, score))
        # A x4 porsjoner, B x4 porsjoner (dobbel oppskrift)
        self.plan = db.create_meal_plan(c, "uke", "2026-11-16", [("2026-11-16", "a", 4), ("2026-11-17", "b", 4)])

    def lines(self, chain):
        return {l.ingredient: l for l in shopping_list(self.conn, self.plan, chain, NOW)}

    def test_amounts_are_scaled_and_summed(self):
        lines = self.lines("KIWI")
        self.assertEqual(lines["Kjøttdeig"].need, "1000 g")      # 400 + 300*2
        self.assertEqual(lines["Lettmelk"].need, "600 ml")       # 3 dl * 2
        self.assertEqual(lines["Løk"].need, "120 g")             # 1 stk * 120 g

    def test_picks_cheapest_total_within_score_band(self):
        l = self.lines("KIWI")["Kjøttdeig"]
        # 3 x 400 g = 180 kr, 1 x 1 kg = 179 kr
        self.assertEqual((l.product, l.packages, l.total), ("p2", 1, 179.0))

    def test_verified_link_wins(self):
        self.conn.execute("UPDATE ingredient_product SET status='verified' WHERE product_id=1")
        l = self.lines("KIWI")["Kjøttdeig"]
        self.assertEqual((l.product, l.packages), ("p1", 3))

    def test_rejected_link_is_skipped(self):
        self.conn.execute("UPDATE ingredient_product SET status='rejected' WHERE product_id=2")
        self.assertEqual(self.lines("KIWI")["Kjøttdeig"].product, "p1")

    def test_missing_and_stale_in_other_chain(self):
        lines = self.lines("REMA")
        self.assertIsNone(lines["Lettmelk"].product)
        self.assertTrue(lines["Kjøttdeig"].stale)

    def test_package_in_grams_for_piece_ingredient(self):
        c = self.conn
        c.execute("INSERT INTO ingredient(id, slug, name, base_unit, grams_per_piece, search_terms) "
                  "VALUES (4,'egg','Egg','stk',60,'egg')")
        c.execute("INSERT INTO recipe_ingredient(recipe_id, ingredient_id, amount, unit) VALUES (1,4,8,'stk')")
        c.execute("INSERT INTO product(id, source_key, name, package_amount, package_unit, updated_at) "
                  "VALUES (5,'ean:5','Egg 6 stk',360,'g','x')")
        c.execute("INSERT INTO offer(product_id, chain_code, store_name, price, price_date, fetched_at) "
                  "VALUES (5,'KIWI','egg6',30,?, 'x')", (FRESH,))
        c.execute("INSERT INTO ingredient_product(ingredient_id, product_id, score) VALUES (4,5,5)")
        self.assertEqual(self.lines("KIWI")["Egg"].packages, 2)  # 8 egg, 6 per pakke

    def test_compare(self):
        rows = {r["code"]: r for r in compare_chains(self.conn, self.plan, NOW)}
        self.assertEqual(rows["KIWI"]["found"], 3)
        self.assertEqual(rows["KIWI"]["total"], 179.0 + 25.0 + 22.0)
        self.assertEqual(rows["REMA"]["missing"], ["Lettmelk"])
        self.assertEqual(rows["REMA"]["stale_prices"], 2)


class SeedTest(unittest.TestCase):
    def test_seed_loads(self):
        conn = db.connect(":memory:")
        db.init_db(conn)
        self.assertGreater(db.load_ingredients(conn), 30)
        self.assertGreater(db.load_recipes(conn), 4)

    def test_external_recipes_load(self):
        conn = db.connect(":memory:")
        db.init_db(conn)
        db.load_ingredients(conn)
        n, _ = external.load(conn)
        self.assertGreater(n, 40)
        row = conn.execute("SELECT source_url FROM recipe WHERE slug='rema-kremet-pasta'").fetchone()
        self.assertTrue(row["source_url"].startswith("https://www.rema.no/"))

    def test_external_file_has_no_instructions(self):
        data = json.loads(external.OUT.read_text(encoding="utf-8"))
        for r in data["recipes"]:
            self.assertFalse({"instructions", "recipeInstructions", "image"} & set(r))


class RecipeParseTest(unittest.TestCase):
    def p(self, raw):
        x = parse_line(raw)
        return x.amount, x.unit, x.name

    def test_schema_org_words(self):
        self.assertEqual(self.p("2 spiseskje Salt"), (2, "ss", "Salt"))
        self.assertEqual(self.p("0,5 desiliter Rømme"), (0.5, "dl", "Rømme"))
        self.assertEqual(self.p("3 kilogram Ribbe"), (3, "kg", "Ribbe"))

    def test_blog_fractions_and_ranges(self):
        self.assertEqual(self.p("1 1/2 ts havsalt"), (1.5, "ts", "havsalt"))
        self.assertEqual(self.p("½ ts chiliflak"), (0.5, "ts", "chiliflak"))
        self.assertEqual(self.p("400 - 500 g poteter"), (450, "g", "poteter"))
        self.assertEqual(self.p("1 boks (300g) med kokte kikerter")[:2], (300, "g"))
        self.assertEqual(self.p("500 poteter , gjerne nypoteter")[:2], (500, "g"))

    def test_package_weight_in_name(self):
        self.assertEqual(self.p("1 pakke Kjøttdeig 600 g Nordfjord")[:2], (600, "g"))
        self.assertEqual(self.p("1 stykk Kvernet deig av storfe 14%, , 400 g Nordfjord")[:2], (400, "g"))
        self.assertEqual(match_ingredient("Karbonadedeig"), "kjottdeig")
        self.assertIsNone(match_ingredient("Kjøttkaker med grønnsaker"))

    def test_uncountable(self):
        self.assertEqual(self.p("1 klype Salt og pepper"), (None, "klype", "Salt og pepper"))
        self.assertEqual(self.p("Pepper"), (None, None, "Pepper"))

    def test_matching(self):
        self.assertEqual(match_ingredient("Hvitløk, finhakket"), "hvitlok")
        self.assertEqual(match_ingredient("hvitløksfedd"), "hvitlok")
        self.assertIsNone(match_ingredient("Hvitløkspulver"))
        self.assertEqual(match_ingredient("Rød paprika"), "paprika")
        self.assertIsNone(match_ingredient("paprika", "ts"))
        self.assertIsNone(match_ingredient("Paprikapulver"))
        self.assertEqual(match_ingredient("Rødløk"), "rodlok")
        self.assertEqual(match_ingredient("løk, finhakket"), "lok")
        self.assertIsNone(match_ingredient("Vårløk"))
        self.assertIsNone(match_ingredient("eggnudler"))
        self.assertIsNone(match_ingredient("risnudler"))
        self.assertIsNone(match_ingredient("peanøttsmør"))
        self.assertEqual(match_ingredient("Meierismør"), "smor")
        self.assertIsNone(match_ingredient("Cherrytomater"))

    def test_normalise(self):
        self.assertEqual(normalise_for_ingredient("hvitlok", 3, "stk", "hvitløksfedd"), (15, "g"))
        self.assertEqual(normalise_for_ingredient("hakkede_tomater", 1, "pk"), (400, "g"))
        self.assertEqual(normalise_for_ingredient("kyllingfilet", 2, "stk"), (300, "g"))


if __name__ == "__main__":
    unittest.main()


class AppExportTest(unittest.TestCase):
    def setUp(self):
        from matglede import app_export
        self.app_export = app_export
        self.conn = db.connect(":memory:")
        db.init_db(self.conn)
        db.load_ingredients(self.conn)
        c = self.conn
        kd = c.execute("SELECT id FROM ingredient WHERE slug='kjottdeig'").fetchone()["id"]
        for pid, name, amt in [(1, "Kjøttdeig 400g", 400), (2, "Kjøttdeig 1 kg", 1000), (3, "Kjøttdeig feil", 400)]:
            c.execute("""INSERT INTO product(id, source_key, name, package_amount, package_unit, updated_at)
                         VALUES (?,?,?,?, 'g','x')""", (pid, f"ean:{pid}", name, amt))
        for pid, chain, price, d in [(1, "KIWI", 60.0, FRESH), (2, "KIWI", 129.0, FRESH),
                                     (3, "KIWI", 10.0, FRESH), (1, "REMA", 55.0, OLD)]:
            c.execute("""INSERT INTO offer(product_id, chain_code, store_name, price, price_date, fetched_at)
                         VALUES (?,?,?,?,?,'x')""", (pid, chain, f"p{pid}", price, d))
        for pid, score, status in [(1, 5, "auto"), (2, 4.6, "auto"), (3, 5, "rejected")]:
            c.execute("INSERT INTO ingredient_product VALUES (?,?,?,?)", (kd, pid, score, status))

    def test_own_recipes_only(self):
        data = self.app_export.build(None, NOW)
        ids = {r["id"] for r in data["recipes"]}
        self.assertGreaterEqual(len(ids), 12)
        self.assertFalse(any(i.split("-")[0] in {"rema", "aicha", "kolby"} for i in ids))
        for r in data["recipes"]:
            self.assertIn(r["diff"], range(1, 6), r["id"])
            self.assertGreater(r["time"], 0, r["id"])
            self.assertTrue(r["steps"], r["id"])
            self.assertNotIn("url", r)
        self.assertFalse(data["hasPrices"])
        self.assertEqual(data["stats"]["lines"], sum(len(r["ing"]) for r in data["recipes"]))
        self.assertTrue({"hverdag", "sondag"} <= {c for r in data["recipes"] for c in r["cats"]})

    def test_base_amounts(self):
        data = self.app_export.build(None, NOW)
        rec = {r["id"]: {i["n"]: i["base"] for i in r["ing"]} for r in data["recipes"]}
        self.assertEqual(rec["tacofredag"]["Kjøttdeig"], 400)
        self.assertEqual(rec["tacofredag"]["Mais"], 340)  # 1 boks
        self.assertEqual(rec["spaghetti-bolognese"]["Hakkede tomater"], 800)  # 2 bokser
        self.assertEqual(rec["spaghetti-bolognese"]["Hvitløk"], 10)  # 2 fedd
        self.assertEqual(rec["kjottkaker-brun-saus"]["Lettmelk"], 100)  # 1 dl
        self.assertIsNone(rec["kjottkaker-brun-saus"]["Kjøttbuljong"])

    def test_previous_prices_reused(self):
        data = self.app_export.build(None, NOW, previous={"kjottdeig": {"KIWI": [{"name": "x", "price": 1}]}})
        self.assertTrue(data["hasPrices"])
        self.assertEqual(data["ingredients"]["kjottdeig"]["products"]["KIWI"][0]["name"], "x")

    def test_candidates_per_chain(self):
        data = self.app_export.build(self.conn, NOW)
        self.assertTrue(data["hasPrices"])
        prods = data["ingredients"]["kjottdeig"]["products"]
        self.assertEqual([p["name"] for p in prods["KIWI"]], ["p2", "p1"])  # avvist kobling er ute, billigst per gram først
        self.assertEqual(prods["KIWI"][1]["size"], 400)
        self.assertTrue(prods["REMA"][0]["stale"])
        self.assertNotIn("ODA", prods)

    def test_write_js(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            out = self.app_export.write({"a": "æ"}, Path(d) / "data.js")
            self.assertIn('window.MATGLEDE_DATA = {"a":"æ"};', out.read_text(encoding="utf-8"))
