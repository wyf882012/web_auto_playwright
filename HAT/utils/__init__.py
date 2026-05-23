def _safe_filename(name: str, max_len: int = 50) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(name))[:max_len]
