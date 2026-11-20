import datetime as dt
import unittest

from matglede.offers import offer_from_product, week_info

NOW = dt.datetime(2026, 11, 20, 12, tzinfo=dt.timezone.utc)


def hist(*pairs):
    return [{"price": p, "date": (NOW - dt.timedelta(days=d)).isoformat().replace("+00:00", "Z")} for d, p in pairs]


class OffersTest(unittest.TestCase):
    def test_price_drop_is_offer(self):
        p = {"name": "Kyllingfilet 700g", "price_history": hist((1, 109), (10, 139), (20, 139), (30, 139))}
        o = offer_from_product(p, NOW)
        self.assertEqual((o["price"], o["before"], o["pct"]), (109, 139, 22))

    def test_small_or_old_drop_is_not_offer(self):
        small = {"name": "x", "price_history": hist((1, 19.9), (10, 20.9), (20, 20.9), (30, 20.9))}
        old = {"name": "y", "price_history": hist((20, 50), (30, 99), (40, 99), (50, 99))}
        self.assertIsNone(offer_from_product(small, NOW))
        self.assertIsNone(offer_from_product(old, NOW))

    def test_week(self):
        self.assertEqual(week_info(dt.date(2026, 11, 20)), {"week": 47, "from": "2026-11-16", "to": "2026-11-22"})


class CoopPagesTest(unittest.TestCase):
    def test_parses_spreads(self):
        from matglede.flyers import coop_pages
        html = """g_cfg.si_dir = '/aviser/extra/ost/760OPP/'; {"img":"ost-47_00-01.jpg?s=1","nr":"0"},{"img":"ost-47_02-03.jpg?s=1"}"""
        self.assertEqual(coop_pages(html, "https://kundeavis.coop.no/aviser/?id=1"), [
            "https://kundeavis.coop.no/aviser/extra/ost/760OPP/ost-47_00-01.jpg?s=1",
            "https://kundeavis.coop.no/aviser/extra/ost/760OPP/ost-47_02-03.jpg?s=1"])


if __name__ == "__main__":
    unittest.main()
