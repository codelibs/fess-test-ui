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

    # ---- Document lookup (GoAction / CacheAction) ---------------------
    # Saved when a docId resolves to no document. Takes the offending docId
    # as {0}. GoAction (:106-107) redirects to /error/, whose error.jsp
    # renders it through <la:errors>; CacheAction (:79-80) redirects to
    # /error/notfound/?message_key=errors.docid_not_found instead, and
    # error/notFound.jsp renders neither <la:errors> nor the message_key
    # parameter -- so this text is assertable on the Go path only.
    ERRORS_DOCID_NOT_FOUND = "errors.docid_not_found"

    # ---- Admin wizard (AdminWizardAction) -----------------------------
    # saveInfo()'d by BOTH crawlingConfig() and crawlingConfigNext() with
    # the created config's name as {0}, and it survives the redirect in the
    # session. It is the only discriminator between a wizard save that was
    # accepted and one rejected by validation or the double-submit token:
    # both render admin_wizard_config.jsp at the same URL. Carrying {0}
    # makes it stronger than a bare success check -- it names which config
    # the wizard claims to have created.
    SUCCESS_CREATE_CRAWLING_CONFIG_AT_WIZARD = (
        "success.create_crawling_config_at_wizard")

    # ---- Confirm-modal delete-all (sysinfo list pages) ----------------
    # saveInfo()'d by the deleteall() of each action, then read off the
    # redirected list page. Distinct keys per page, so asserting the right
    # one proves the modal's submit button dispatched to that page's own
    # action rather than merely reloading the list.
    SUCCESS_JOB_LOG_DELETE_ALL = "success.job_log_delete_all"
    SUCCESS_CRAWLING_INFO_DELETE_ALL = "success.crawling_info_delete_all"
