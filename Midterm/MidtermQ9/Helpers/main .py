import helpers.string_utils as su
from helpers.math_utils import area

def main() -> None:
    """Demonstrate module importing and alias usage."""
    print(su.shout("module demo"))
    print(f"Area: {area(5, 10)}")

if __name__ == "__main__":
    main()
