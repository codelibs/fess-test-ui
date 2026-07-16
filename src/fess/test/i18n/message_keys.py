"""Catalog of fess_message.properties keys used by tests.

The message counterpart of keys.py: same rule, every test that asserts on a
Fess-rendered user message MUST go through these constants rather than an
inline key string, so that a Fess rename or removal surfaces as a KeyError
naming the key instead of a silent mismatch.

Messages reach the search UI through <la:errors> in index.jsp, which wraps
each one in errors.front_prefix = '<div class="alert alert-warning">'.
"""


class Messages:
    # ---- Search query errors (SearchAction.search catch blocks) --------
    # Raised when the requested offset exceeds
    # query.max.search.result.offset (default 100000). The check is
    # strictly greater-than, so start=100000 does NOT raise it.
    ERRORS_RESULT_SIZE_EXCEEDED = "errors.result_size_exceeded"

    # InvalidQueryException carries its own message code; the sort variant
    # takes the offending sort field as {0}.
    ERRORS_INVALID_QUERY_UNSUPPORTED_SORT_FIELD = (
        "errors.invalid_query_unsupported_sort_field")
