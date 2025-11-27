from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class ProductFamily:
    slug: str                 # "ps5", "xbox-series-x", "iphone-13"
    display_name: str         # "PlayStation 5", "Xbox Series X", "iPhone 13"
    keywords: List[str]       # palavras que, se aparecerem, sugerem essa família
    category: str             # "console", "phone"
    brand: str                # "playstation", "xbox", "apple", "samsung"

# Data class to hold the result of query classification
@dataclass
class QueryProfile:
    category: Optional[str]
    brand: Optional[str]
    family_slug: Optional[str]
    raw_query: str
    tokens: List[str]


FAMILIES: List[ProductFamily] = [
    # CONSOLES
    ProductFamily(
        slug="ps5",
        display_name="PlayStation 5",
        category="console",
        brand="playstation",
        keywords=[
            "ps5", "playstation 5", "playstation®5", "ps 5",
        ],
    ),
    ProductFamily(
        slug="ps4",
        display_name="PlayStation 4",
        category="console",
        brand="playstation",
        keywords=[
            "ps4", "playstation 4", "ps 4",
        ],
    ),
    ProductFamily(
        slug="xbox-series-x",
        display_name="Xbox Series X",
        category="console",
        brand="xbox",
        keywords=[
            "xbox series x", "series x", "xsx",
        ],
    ),
    ProductFamily(
        slug="xbox-series-s",
        display_name="Xbox Series S",
        category="console",
        brand="xbox",
        keywords=[
            "xbox series s", "series s", "xss",
        ],
    ),

    # CELULARES
    ProductFamily(
        slug="iphone-13",
        display_name="iPhone 13",
        category="phone",
        brand="apple",
        keywords=[
            "iphone 13", "iphone13", "iphone 13 128gb", "iphone 13 256gb",
        ],
    ),
    ProductFamily(
        slug="iphone-14",
        display_name="iPhone 14",
        category="phone",
        brand="apple",
        keywords=[
            "iphone 14", "iphone14",
        ],
    ),
    # add more families here...
]


def classify_query(query: str) -> QueryProfile:
    q_lower = query.lower()
    tokens = q_lower.split()

    best_match: Optional[ProductFamily] = None
    best_score = 0

    for fam in FAMILIES:
        score = 0
        for kw in fam.keywords:
            if kw in q_lower:
                score += 1
        if score > best_score:
            best_score = score
            best_match = fam

    if best_match is None:
        return QueryProfile(
            category=None,
            brand=None,
            family_slug=None,
            raw_query=query,
            tokens=tokens,
        )

    return QueryProfile(
        category=best_match.category,
        brand=best_match.brand,
        family_slug=best_match.slug,
        raw_query=query,
        tokens=tokens,
    )
