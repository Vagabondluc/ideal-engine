"""Error formatting helpers extracted from world_builder.py."""


def html_escape(s: str) -> str:
    if s is None:
        return ''
    return (str(s)
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))


def format_exception_enhanced(exc: Exception, show_trace: bool = False) -> str:
    """Return an HTML-friendly exception message and optional traceback.

    This is a small helper for formatting exception objects; it deliberately
    does not conflict with the in-repo `format_error_enhanced` HTML builder.
    """
    msg = f"<b>{type(exc).__name__}:</b> {html_escape(str(exc))}"
    if show_trace:
        import traceback

        trace = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        msg += f"<pre>{html_escape(trace)}</pre>"
    return msg


def format_simple_error(msg: str) -> str:
    return f"<div class=\"wb-error\">{html_escape(msg)}</div>"
