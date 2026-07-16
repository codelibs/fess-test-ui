
import logging

from fess.test import assert_equal, assert_not_equal, assert_startswith
from fess.test.i18n import t
from fess.test.i18n.keys import Labels
from fess.test.ui import FessContext
from playwright.sync_api import Playwright, sync_playwright

logger = logging.getLogger(__name__)


def setup(playwright: Playwright) -> FessContext:
    context: FessContext = FessContext(playwright)
    context.login()
    return context


def destroy(context: FessContext) -> None:
    context.close()


def run(context: FessContext) -> None:
    """
    Integration test for user permission workflow:
    1. Create a new role
    2. Create a new group
    3. Create a new user and assign to group
    4. Verify user exists with group assignment
    5. Delete user, group, and role (cleanup)
    """
    logger.info("start user permission workflow integration test")

    page: "Page" = context.get_admin_page()
    label_base: str = context.create_label_name()
    role_name: str = f"Role_{label_base}"
    group_name: str = f"Group_{label_base}"
    user_name: str = f"User_{label_base}"

    created: list = []
    try:
        # Step 1: Create a new role
        logger.info("Step 1: Creating role")
        page.click(f"text={t(Labels.MENU_USER)}")
        page.click(f"text={t(Labels.MENU_ROLE)}")
        assert_equal(page.url, context.url("/admin/role/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/role/createnew/"))

        page.fill("input[name=\"name\"]", role_name)
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/role/"))

        page.wait_for_load_state("domcontentloaded")
        table_content: str = page.inner_text("table")
        assert_not_equal(table_content.find(role_name), -1,
                         f"{role_name} not created")
        created.append("role")
        logger.info(f"✓ Role '{role_name}' created successfully")

        # Step 2: Create a new group
        logger.info("Step 2: Creating group")
        page.goto(context.url("/admin/group/"))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.url, context.url("/admin/group/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/group/createnew/"))

        page.fill("input[name=\"name\"]", group_name)
        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/group/"))

        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(group_name), -1,
                         f"{group_name} not created")
        created.append("group")
        logger.info(f"✓ Group '{group_name}' created successfully")

        # Step 3: Create a new user and assign to group
        logger.info("Step 3: Creating user with group assignment")
        page.goto(context.url("/admin/user/"))
        page.wait_for_load_state("domcontentloaded")
        assert_equal(page.url, context.url("/admin/user/"))

        page.click(f"text={t(Labels.CRUD_LINK_CREATE)}")
        assert_equal(page.url, context.url("/admin/user/createnew/"))

        page.fill("input[name=\"name\"]", user_name)
        page.fill("input[name=\"password\"]", "testpassword123")
        page.fill("input[name=\"confirmPassword\"]", "testpassword123")

        # Select the group
        page.select_option("select[name=\"groups\"]", label=group_name)

        page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_CREATE)}")')
        assert_equal(page.url, context.url("/admin/user/"))

        page.wait_for_load_state("domcontentloaded")
        table_content = page.inner_text("table")
        assert_not_equal(table_content.find(user_name), -1,
                         f"{user_name} not created")
        created.append("user")
        logger.info(f"✓ User '{user_name}' created and assigned to group")

        # Step 4: Verify user details with group assignment
        logger.info("Step 4: Verifying user with group assignment")
        page.click(f"text={user_name}")
        assert_startswith(page.url, context.url("/admin/user/details/4/"))

        page_content = page.inner_text("body")
        assert_not_equal(page_content.find(group_name), -1,
                         f"User not associated with group {group_name}")
        logger.info(f"✓ User-Group association verified")
    finally:
        # Step 5: Cleanup - Delete user, group, and role
        logger.info("Step 5: Cleanup - deleting user, group, and role")

        # Delete user (known password: testpassword123 — must not leak)
        if "user" in created:
            try:
                page.goto(context.url("/admin/user/"))
                page.wait_for_load_state("domcontentloaded")
                page.click(f"text={user_name}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f"text={t(Labels.CRUD_LINK_DELETE)}")
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/user/"))
                logger.info(f"✓ User '{user_name}' deleted")
            except Exception as e:
                logger.error(f"LEAKED user '{user_name}' with known password 'testpassword123' — will pollute later modules: {e}")

        # Delete group
        if "group" in created:
            try:
                page.goto(context.url("/admin/group/"))
                page.wait_for_load_state("domcontentloaded")
                assert_equal(page.url, context.url("/admin/group/"))
                page.click(f"text={group_name}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f"text={t(Labels.CRUD_LINK_DELETE)}")
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/group/"))
                logger.info(f"✓ Group '{group_name}' deleted")
            except Exception as e:
                logger.error(f"LEAKED group '{group_name}' — will pollute later modules: {e}")

        # Delete role
        if "role" in created:
            try:
                page.goto(context.url("/admin/role/"))
                page.wait_for_load_state("domcontentloaded")
                assert_equal(page.url, context.url("/admin/role/"))
                page.click(f"text={role_name}")
                page.wait_for_load_state("domcontentloaded")
                page.click(f'button:has-text("{t(Labels.CRUD_BUTTON_DELETE)}")')
                page.click('div.modal-footer button[name="delete"]')
                assert_equal(page.url, context.url("/admin/role/"))
                logger.info(f"✓ Role '{role_name}' deleted")
            except Exception as e:
                logger.error(f"LEAKED role '{role_name}' — will pollute later modules: {e}")

    logger.info("✓ User permission workflow integration test completed successfully")


if __name__ == "__main__":
    with sync_playwright() as playwright:
        context: FessContext = setup(playwright)
        run(context)
        destroy(context)
