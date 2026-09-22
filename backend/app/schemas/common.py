def clean_str_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values:
        item = " ".join(value.strip().lower().split())
        if not item or item in seen:
            continue
        seen.add(item)
        cleaned.append(item)
    return cleaned
