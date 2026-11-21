import json
import unittest
from types import SimpleNamespace as NS

from matglede.flyer_ai import clean, flyer_content, read_flyers


class FakeStream:
    def __init__(self, msg): self.msg = msg
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def get_final_message(self): return self.msg


class FakeClient:
    def __init__(self, items):
        msg = NS(stop_reason="end_turn", content=[NS(type="text", text=json.dumps({"items": items}))])
        self.calls = []
        self.beta = NS(messages=NS(stream=lambda **kw: (self.calls.append(kw), FakeStream(msg))[1]))


def item(name, price, before=0, **kw):
    return {"name": name, "brand": "", "price": price, "before": before, "unit": "", "deal": "", "cat": "Fisk", **kw}


class FlyerAiTest(unittest.TestCase):
    def test_clean(self):
        out = clean([item("Laks 400 g", 69.9, 99.9), item("Laks 400 g", 69.9), item("Torsk", 0), item("Reker", 89, 50, cat="?")])
        self.assertEqual([(o["name"], o["price"], o["pct"]) for o in out], [("Laks 400 g", 69.9, 30), ("Reker", 89.0, 0)])
        self.assertEqual((out[1]["before"], out[1]["cat"], out[0]["src"]), (0, "Middag og tørrvarer", "avis"))

    def test_content(self):
        get = lambda url: b"%PDF-1.7" if url.endswith("pdf") else b"jpg"
        self.assertEqual(flyer_content({"type": "pdf", "url": "x.pdf"}, get)[0]["source"]["media_type"], "application/pdf")
        self.assertEqual(len(flyer_content({"type": "images", "pages": ["a", "b"]}, get)), 2)
        self.assertIsNone(flyer_content({"type": "link", "url": "x"}, get))
        self.assertIsNone(flyer_content({"type": "pdf", "url": "x.html"}, lambda u: b"<html>"))

    def test_read_flyers_replaces_only_readable(self):
        import matglede.flyer_ai as fa
        orig, fa._download = fa._download, lambda url: b"%PDF-1.7"
        try:
            data = {"stores": [{"name": "Kiwi", "view": {"type": "pdf", "url": "k.pdf"}, "offers": [], "hasData": True},
                               {"name": "Rema", "view": {"type": "link", "url": "r"}, "offers": [{"name": "x"}], "hasData": False}]}
            client = FakeClient([item("Laks", 70), item("Torsk", 60), item("Egg 12 stk", 30)])
            read_flyers(data, client, log=lambda *a: None)
        finally:
            fa._download = orig
        self.assertEqual(len(data["stores"][0]["offers"]), 3)
        self.assertTrue(data["stores"][0]["fromFlyer"])
        self.assertEqual(data["stores"][1]["offers"], [{"name": "x"}])
        self.assertEqual(len(client.calls), 1)


if __name__ == "__main__":
    unittest.main()
