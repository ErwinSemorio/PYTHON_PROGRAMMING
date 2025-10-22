def area(length: float, width: float) -> float:
    """Return the area of a rectangle given length and width."""
    if not (isinstance(length, (int, float)) and isinstance(width, (int, float))):
        raise TypeError("Length and width must be numeric")
    return length * width
