"""Build CourtListener search query strings."""


def build_search_query(user_input: str, mode: str, court_id: str | None = None) -> str:
    """
    Build the q= parameter for CourtListener search API.
    Use type=r for federal dockets.
    """
    normalized = " ".join(user_input.strip().split())
    if not normalized:
        return ""

    if mode == "docket":
        # Escape quotes in user input for docketNumber field
        escaped = normalized.replace('"', '\\"')
        q = f'docketNumber:"{escaped}"'
    else:
        # mode == "name" -> party search
        escaped = normalized.replace('"', '\\"')
        q = f'party:"{escaped}"'

    if court_id and court_id.strip():
        q = f"({q}) AND court_id:{court_id.strip()}"

    return q
