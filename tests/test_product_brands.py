import unittest

from services.product_brands import get_product_brand


class ProductBrandTests(unittest.TestCase):
    def test_brand_lookup_maps_streaming_and_music_products(self):
        expected = {
            "Apple Music": "https://cdn.simpleicons.org/applemusic/",
            "Apple TV+": "https://cdn.simpleicons.org/appletv/",
            "Tidal": "https://cdn.simpleicons.org/tidal/",
            "Star+": (
                "https://cdn.jsdelivr.net/gh/hmarcelodn/"
                "caece-a2a-cinema@main/"
            ),
            "Star Plus": (
                "https://cdn.jsdelivr.net/gh/hmarcelodn/"
                "caece-a2a-cinema@main/"
            ),
            "Crunchyroll": "https://cdn.simpleicons.org/crunchyroll/",
            "Disney": (
                "https://cdn.jsdelivr.net/gh/homarr-labs/"
                "dashboard-icons@main/"
            ),
            "Disney+": (
                "https://cdn.jsdelivr.net/gh/homarr-labs/"
                "dashboard-icons@main/"
            ),
            "HBO Max": "https://cdn.simpleicons.org/hbo/FFFFFF",
            "Max": "https://cdn.simpleicons.org/max/",
            "Paramount": "https://cdn.simpleicons.org/paramountplus/",
            "Paramount+": "https://cdn.simpleicons.org/paramountplus/",
            "Paramount Plus": "https://cdn.simpleicons.org/paramountplus/",
        }

        for product_name, expected_source in expected.items():
            with self.subTest(product=product_name):
                brand = get_product_brand(product_name)
                self.assertIsNotNone(brand)
                self.assertTrue(brand["icon_url"].startswith(expected_source))
                self.assertEqual(
                    brand["is_wordmark"],
                    product_name in {"Star+", "Star Plus"},
                )

    def test_brand_lookup_ignores_spaces_and_punctuation(self):
        self.assertEqual(
            get_product_brand(" Disney + ")["name"],
            "Disney+",
        )

    def test_unknown_product_has_no_guessed_brand(self):
        self.assertIsNone(get_product_brand("Unknown service"))


if __name__ == "__main__":
    unittest.main()
