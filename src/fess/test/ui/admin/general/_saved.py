"""Shared check for "did the /admin/general/ save actually get accepted?".

Every settings module on this page needs it, and the obvious answer is wrong.
The form posts to the page's own URL:

    admin_general.jsp:29   <la:form action="/admin/general/">

and LastaFlute picks the action from the submit button's request parameter
(name="update"), not from a URL segment. AdminGeneralAction.update() then ends
in redirect(getClass()) on success, but a validation or token failure returns
asHtml(path_AdminGeneral_AdminGeneralJsp), which re-renders in place. Success
redirects to /admin/general/; failure stays on /admin/general/. The URL is
byte-identical either way, so asserting on it proves nothing -- there is no
input that makes such an assertion red.

The page does render a discriminator (admin_general.jsp:35-38):

    <la:info id="msg" message="true">
        <div class="alert alert-success">${msg}</div>
    </la:info>
    <la:errors property="_global"/>

update() calls saveInfo() before redirecting and the message survives the
redirect in the session, so the success alert is present exactly when the save
was accepted, and absent when it was rejected.
"""
import logging

from fess.test import assert_true

logger = logging.getLogger(__name__)

SUCCESS_ALERT = "div.alert-success"
ERROR_LIST = "ul.has-error"


def assert_saved(page) -> None:
    """Assert the save just submitted was accepted.

    Red when the save is rejected: no success alert is rendered. Reports any
    validation text the page came back with, since that names the cause.
    """
    if page.locator(SUCCESS_ALERT).count() > 0:
        return

    errors = ""
    if page.locator(ERROR_LIST).count() > 0:
        errors = page.locator(ERROR_LIST).first.inner_text()
    assert_true(False,
                f"the /admin/general/ save was rejected: no {SUCCESS_ALERT} was "
                f"rendered. Validation output: {errors or '(none)'}. Note the URL "
                f"is {page.url} either way -- success and failure both land on "
                f"/admin/general/, so only this alert distinguishes them.")
