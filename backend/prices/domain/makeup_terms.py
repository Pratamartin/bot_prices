MAKEUP_KEYWORDS = [
    "gloss", "batom", "lip", "liphoney", "lipstick",
    "base", "corretivo", "pó", "primer",
    "rímel", "mascara", "sombra", "paleta", "delineador",
    "blush", "iluminador",
    "fran", "franciny", "ruby rose", "bruna tavares", "bt",
    "vult", "nina secrets", "mac", "nars", "dior", "maybelline",
]

def is_makeup_query(query: str) -> bool:
    q = query.lower()
    return any(word in q for word in MAKEUP_KEYWORDS)
