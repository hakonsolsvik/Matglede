import unittest

from matglede.aviser import build_store, pick, variants


class AviserTest(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(variants("Coca-Cola/Fanta/Sprite", "et utvalg, 0,33 l"), ["Coca-Cola", "Fanta", "Sprite"])
        self.assertEqual(variants("SYNNØVE GULOST", "Original/lettost. Pr kg"), ["Synnøve gulost original", "Synnøve gulost lettost"])
        self.assertEqual(variants("Melange", "500 g/500 ml. Pr pk"), [])
        self.assertEqual(variants("Røde/grønne druer", ""), ["Røde druer", "Grønne druer"])
        self.assertEqual(variants("Coca-cola original/ zero", ""), ["Coca-cola original", "Coca-cola zero"])
        self.assertEqual(variants("RED BULL/ RED BULL SUKKERFRI", ""), ["Red bull", "Red bull sukkerfri"])
        self.assertEqual(variants("Lutefisk", "m/skinn"), [])

    def test_pick_newest_main_flyer(self):
        cats = [{"id": "jul", "dealer_id": "80742m", "run_from": "2026-10-31", "page_count": 36},
                {"id": "uke", "dealer_id": "80742m", "run_from": "2026-11-22", "page_count": 31}]
        self.assertEqual(pick(cats)["EXTRA"]["id"], "uke")

    def test_hotspot_box_and_before(self):
        cat = {"id": "c", "dimensions": {"height": 1.5}}
        hs = [{"type": "offer", "id": "a", "locations": {"2": [[0.1, 0.3], [0.1, 0.6], [0.5, 0.6], [0.5, 0.3]]},
               "offer": {"heading": "KJØTTDEIG", "pricing": {"price": 49.9, "pre_price": None}}}]
        s = build_store(cat, [{"view": "p1"}, {"view": "p2"}], hs, [{"id": "a", "description": "400 g Førpris: 72,90"}])
        h = s["hot"][0]
        self.assertEqual((h["pg"], h["r"], h["n"], h["b"]), (1, [0.1, 0.2, 0.4, 0.2], "Kjøttdeig", 72.9))


if __name__ == "__main__":
    unittest.main()
