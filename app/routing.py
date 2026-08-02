from dataclasses import dataclass


ACCOUNT_REGION_BY_PLATFORM = {
    "BR1": "americas",
    "LA1": "americas",
    "LA2": "americas",
    "NA1": "americas",
    "EUN1": "europe",
    "EUW1": "europe",
    "TR1": "europe",
    "RU": "europe",
    "JP1": "asia",
    "KR": "asia",
    "OC1": "asia",
    "PH2": "asia",
    "SG2": "asia",
    "TH2": "asia",
    "TW2": "asia",
    "VN2": "asia",
}


@dataclass(frozen=True)
class Platform:
    code: str
    name: str


PLATFORMS = tuple(
    Platform(code, name)
    for code, name in (
        ("BR1", "Brasil"),
        ("EUN1", "Europa Nórdica y del Este"),
        ("EUW1", "Europa Oeste"),
        ("JP1", "Japón"),
        ("KR", "Corea"),
        ("LA1", "Latinoamérica Norte"),
        ("LA2", "Latinoamérica Sur"),
        ("NA1", "Norteamérica"),
        ("OC1", "Oceanía"),
        ("PH2", "Filipinas"),
        ("RU", "Rusia"),
        ("SG2", "Singapur"),
        ("TH2", "Tailandia"),
        ("TR1", "Turquía"),
        ("TW2", "Taiwán"),
        ("VN2", "Vietnam"),
    )
)

TIER_ORDER = {
    "NONE": 0,
    "IRON": 1,
    "BRONZE": 2,
    "SILVER": 3,
    "GOLD": 4,
    "PLATINUM": 5,
    "EMERALD": 6,
    "DIAMOND": 7,
    "MASTER": 8,
    "GRANDMASTER": 9,
    "CHALLENGER": 10,
}


def get_platform(code: str) -> Platform:
    normalized = code.upper()
    for platform in PLATFORMS:
        if platform.code == normalized:
            return platform
    raise ValueError(f"Plataforma no soportada: {code}")


def account_region_for_platform(platform: str) -> str:
    normalized = platform.upper()
    if normalized not in ACCOUNT_REGION_BY_PLATFORM:
        raise ValueError(f"Plataforma no soportada: {platform}")
    return ACCOUNT_REGION_BY_PLATFORM[normalized]
