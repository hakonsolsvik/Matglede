import unittest

from matglede.forpriser import merge, to_offer


def raw(dealer, heading, desc, price, pre, week):
    return {"dealer_id": dealer, "heading": heading, "description": desc, "run_from": week + "T00:00:00+0000",
            "pricing": {"price": price, "pre_price": pre}}


class ForpriserTest(unittest.TestCase):
    def test_name_and_before_from_text(self):
        o = to_offer(raw("faa0Ym", "MEIERISMØR", "Tine, 500 g, 89,80 pr. kg\nFørpris 61,40", 44.9, None, "2026-11-22"))
        self.assertEqual((o["code"], o["name"], o["before"]), ("REMA", "MEIERISMØR Tine, 500 g", 61.4))

    def test_without_before_is_skipped(self):
        self.assertIsNone(to_offer(raw("faa0Ym", "Melk", "1 l", 20, None, "2026-11-22")))
        self.assertIsNone(to_offer(raw("ukjent", "Melk", "1 l", 20, 25, "2026-11-22")))

    def test_newest_week_wins(self):
        a, _ = merge({"stores": []}, [raw("257bxm", "GULROT", "750 g", 19.9, 34.9, "2026-11-22")])
        b, new = merge(a, [raw("257bxm", "GULROT", "750 g", 19.9, 29.9, "2026-03-01"),
                           raw("257bxm", "Gulrot", "750 g", 15, 36.9, "2026-11-29")])
        self.assertEqual([o["before"] for o in b["stores"][0]["offers"]], [36.9])
        self.assertEqual([(n["before"], n["old"]) for n in new], [(36.9, 34.9)])


if __name__ == "__main__":
    unittest.main()
