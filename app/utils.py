import unicodedata
from urllib.parse import quote


def parse_riot_id(value: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise ValueError("El Riot ID debe tener el formato Nombre#TAG.")
    pieces = value.strip().split("#")
    if len(pieces) != 2:
        raise ValueError("El Riot ID debe contener exactamente un signo #.")
    game_name, tag_line = pieces[0].strip(), pieces[1].strip()
    if not game_name or not tag_line:
        raise ValueError("El nombre y el tag del Riot ID no pueden estar vacíos.")
    return game_name, tag_line


def riot_id_path(game_name: str, tag_line: str) -> str:
    return f"{quote(game_name, safe='')}/{quote(tag_line, safe='')}"


def normalize_search(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def format_number(value: float | int | None) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)
