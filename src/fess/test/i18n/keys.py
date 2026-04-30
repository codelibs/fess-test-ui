"""Catalog of fess_label.properties keys used by tests.

Every test that references a localized string MUST go through these
constants — never use raw key strings inline. This file is the single
source of truth for "which Fess label keys does the test suite depend
on?", which makes it possible to detect breakage when Fess renames or
removes a key.

Keys marked `# TBV` are placeholders that must be confirmed against
fess_label.properties during implementation of the consuming test.
"""


class Labels:
    # ---- Login --------------------------------------------------------
    LOGIN = "labels.login"
    LOGIN_PLACEHOLDER_USERNAME = "labels.login.placeholder_username"
    LOGIN_PLACEHOLDER_PASSWORD = "labels.login.placeholder_password"

    # ---- Sidebar / menu ----------------------------------------------
    MENU_DASHBOARD_CONFIG = "labels.menu_dashboard_config"
    MENU_SYSTEM = "labels.menu_system"
    MENU_WIZARD = "labels.menu_wizard"
    MENU_CRAWL_CONFIG = "labels.menu_crawl_config"
    MENU_SCHEDULER_CONFIG = "labels.menu_scheduler_config"
    MENU_DESIGN = "labels.menu_design"
    MENU_DICT = "labels.menu_dict"
    MENU_ACCESS_TOKEN = "labels.menu_access_token"
    MENU_PLUGIN = "labels.menu_plugin"
    MENU_STORAGE = "labels.menu_storage"
    MENU_CRAWL = "labels.menu_crawl"
    MENU_WEB = "labels.menu_web"
    MENU_FILE_SYSTEM = "labels.menu_file_system"
    MENU_DATA_STORE = "labels.menu_data_store"
    MENU_LABEL_TYPE = "labels.menu_label_type"
    MENU_KEY_MATCH = "labels.menu_key_match"
    MENU_BOOST_DOCUMENT_RULE = "labels.menu_boost_document_rule"
    MENU_RELATED_CONTENT = "labels.menu_related_content"
    MENU_RELATED_QUERY = "labels.menu_related_query"
    MENU_PATH_MAPPING = "labels.menu_path_mapping"
    MENU_WEB_AUTHENTICATION = "labels.menu_web_authentication"
    MENU_FILE_AUTHENTICATION = "labels.menu_file_authentication"
    MENU_REQUEST_HEADER = "labels.menu_request_header"
    MENU_DUPLICATE_HOST = "labels.menu_duplicate_host"
    MENU_USER = "labels.menu_user"
    MENU_ROLE = "labels.menu_role"
    MENU_GROUP = "labels.menu_group"
    MENU_SUGGEST = "labels.menu_suggest"
    MENU_SUGGEST_WORD = "labels.menu_suggest_word"
    MENU_ELEVATE_WORD = "labels.menu_elevate_word"
    MENU_BAD_WORD = "labels.menu_bad_word"
    MENU_SYSTEM_LOG = "labels.menu_system_log"
    MENU_SYSTEM_INFO = "labels.menu_system_info"
    MENU_SEARCH_LOG = "labels.menu_searchLog"
    MENU_JOB_LOG = "labels.menu_jobLog"
    MENU_CRAWLING_INFO = "labels.menu_crawling_info"
    MENU_LOG = "labels.menu_log"
    MENU_FAILURE_URL = "labels.menu_failure_url"
    MENU_SEARCH_LIST = "labels.menu_search_list"
    MENU_BACKUP = "labels.menu_backup"
    MENU_MAINTENANCE = "labels.menu_maintenance"

    # ---- CRUD link (top of list page) --------------------------------
    CRUD_LINK_CREATE = "labels.crud_link_create"
    CRUD_LINK_DELETE = "labels.crud_link_delete"

    # ---- CRUD button (form submit) -----------------------------------
    CRUD_BUTTON_CREATE = "labels.crud_button_create"
    CRUD_BUTTON_UPDATE = "labels.crud_button_update"
    CRUD_BUTTON_DELETE = "labels.crud_button_delete"
    CRUD_BUTTON_CANCEL = "labels.crud_button_cancel"
    CRUD_BUTTON_BACK = "labels.crud_button_back"
    CRUD_BUTTON_EDIT = "labels.crud_button_edit"

    # ---- Scheduler ---------------------------------------------------
    SCHEDULER_BUTTON_START = "labels.scheduledjob_button_start"

    # ---- Search results ----------------------------------------------
    # Renders as a message containing "{0}" placeholder for the query, e.g.
    # JP: "<b>{0}</b> に一致する情報は見つかりませんでした。"
    # EN: "Your search - <b>{0}</b> - did not match any documents."
    SEARCH_DID_NOT_MATCH = "labels.did_not_match"
