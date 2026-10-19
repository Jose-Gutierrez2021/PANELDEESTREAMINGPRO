import re
import unicodedata
from urllib.parse import quote


_BRANDS = {
    "netflix": ("Netflix", "netflix.com", "E50914", "N"),
    "disney": ("Disney+", "disneyplus.com", "113CCF", "D+"),
    "disneyplus": ("Disney+", "disneyplus.com", "113CCF", "D+"),
    "max": ("Max", "max.com", "002BE7", "M"),
    "hbomax": ("HBO Max", "max.com", "002BE7", "HBO"),
    "primevideo": ("Prime Video", "primevideo.com", "00A8E1", "P"),
    "paramount": ("Paramount+", "paramountplus.com", "0064FF", "P+"),
    "paramountplus": ("Paramount+", "paramountplus.com", "0064FF", "P+"),
    "crunchyroll": ("Crunchyroll", "crunchyroll.com", "F47521", "C"),
    "appletv": ("Apple TV+", "tv.apple.com", "FFFFFF", "TV"),
    "vix": ("ViX", "vix.com", "F15A24", "ViX"),
    "star": ("Star+", "starplus.com", "00A8E0", "S+"),
    "starplus": ("Star+", "starplus.com", "00A8E0", "S+"),
    "hulu": ("Hulu", "hulu.com", "1CE783", "H"),
    "spotify": ("Spotify", "spotify.com", "1ED760", "S"),
    "applemusic": ("Apple Music", "music.apple.com", "FA243C", "A"),
    "youtubemusic": ("YouTube Music", "music.youtube.com", "FF0000", "YT"),
    "deezer": ("Deezer", "deezer.com", "FEAA2D", "D"),
    "tidal": ("Tidal", "tidal.com", "FFFFFF", "T"),
    "amazonmusic": ("Amazon Music", "music.amazon.com", "25D1DA", "AM"),
}

_SIMPLE_ICON_SLUGS = {
    "Apple Music": "applemusic",
    "Apple TV+": "appletv",
    "Tidal": "tidal",
    "Crunchyroll": "crunchyroll",
    "Paramount+": "paramountplus",
    "Max": "max",
}

_BRAND_LOGO_URLS = {
    "HBO Max": "https://cdn.simpleicons.org/hbo/FFFFFF",
    "Disney+": (
        "https://cdn.jsdelivr.net/gh/homarr-labs/"
        "dashboard-icons@main/svg/disney-plus.svg"
    ),
    "Star+": (
        "https://cdn.jsdelivr.net/gh/hmarcelodn/caece-a2a-cinema@main/"
        "apps/lumus-ui/public/platforms/star-plus.svg"
    ),
}


def _normalize(value):
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_value = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]", "", ascii_value)


def get_product_brand(product_name):
    brand = _BRANDS.get(_normalize(product_name))
    if brand is None:
        return None

    name, domain, color, initials = brand
    icon_slug = _SIMPLE_ICON_SLUGS.get(name)
    icon_url = (
        _BRAND_LOGO_URLS.get(name)
        or (
            f"https://cdn.simpleicons.org/{icon_slug}/{color}"
            if icon_slug
            else (
                "https://www.google.com/s2/favicons?domain="
                f"{quote(domain, safe='')}&sz=128"
            )
        )
    )
    return {
        "name": name,
        "domain": domain,
        "color": color,
        "initials": initials,
        "icon_url": icon_url,
        "is_wordmark": name == "Star+",
    }
