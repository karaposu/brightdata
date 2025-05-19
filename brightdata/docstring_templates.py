# docstring_templates.py

"""
Docstring Templates
===================

Google-style docstring templates for scraper classes and methods.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Class docstring template
# ─────────────────────────────────────────────────────────────────────────────

CLASS_DOCSTRING = '''"""ClassName

Explanation:
    <Short description of what this scraper does.>

Example:
    >>> scraper = ClassName(bearer_token="…")
    >>> snap = scraper.collect_by_url(["https://example.com/product/123"])
"""'''
# Fill in:
#   • ClassName      → e.g. AmazonScraper
#   • Explanation    → what domains/endpoints it handles
#   • Example        → minimal instantiation + call


# ─────────────────────────────────────────────────────────────────────────────
# Method docstring template
# ─────────────────────────────────────────────────────────────────────────────

METHOD_DOCSTRING = '''def method_name(
    self,
    arg1: ArgType,
    arg2: ArgType = default,
) -> ReturnType:
    """
    Method summary.

    Explanation:
        <Detailed description of what this method does.>

    Args:
        arg1 (ArgType):
            Explanation of arg1.
            Sample: example_value

        arg2 (ArgType, optional):
            Explanation of arg2.
            Sample: example_value

    Returns:
        ReturnType:
            Explanation of the return value.

    Example:
        >>> result = scraper.method_name(
        ...     arg1=example_value,
        ...     arg2=example_value,
        ... )
    """
'''
# Fill in:
#   • method_name   → e.g. collect_by_url
#   • ArgType       → e.g. Sequence[str], Optional[int], etc.
#   • default       → default value if any
#   • ReturnType    → e.g. List[Dict[str, Any]], str, etc.
#   • Samples       → representative values

