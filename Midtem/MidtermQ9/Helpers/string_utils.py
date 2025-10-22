def shout(s: str) -> str:
    """Return the input string in uppercase."""
    if not isinstance(s, str):
        raise TypeError("Input must be a string")
    return s.upper()
