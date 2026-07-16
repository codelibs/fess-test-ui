import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Any

from playwright.sync_api import sync_playwright

from fess.test.ui import FessContext
from fess.test.result import ResultCollector, TestResult
from fess.test import i18n as i18n_mod
from fess.test.metrics import MetricsCollector
from fess.test.logging_config import setup_logging
from fess.test.ui.admin import (accesstoken,
                                badword,
                                boostdoc,
                                dataconfig,
                                duplicatehost,
                                elevateword,
                                fileauth,
                                general,
                                keymatch,
                                label,
                                pathmap,
                                relatedcontent,
                                relatedquery,
                                reqheader,
                                scheduler,
                                sysinfo,
                                user,
                                group,
                                role,
                                virtualhost,
                                webauth,
                                webconfig,
                                fileconfig)

from fess.test.ui.admin.dict import (kuromoji,
                                     protwords,
                                     mapping,
                                     stemmeroverride,
                                     stopwords,
                                     synonym)

from fess.test.ui.search import (
    advance as search_advance,
    error_pages as search_error_pages,
    facet as search_facet,
    form_submit as search_form_submit,
    help as search_help,
    login_form as search_login_form,
    logout as search_logout,
    no_results as search_no_results,
    osdd as search_osdd,
    query_errors as search_query_errors,
    pagination as search_pagination,
    profile_form as search_profile_form,
    query as search_query,
    related as search_related,
    root_top as search_root_top,
    seed as search_seed,
    sort as search_sort,
    suggest as search_suggest,
    thumbnail as search_thumbnail,
    top as search_top,
    i18n_smoke as search_i18n_smoke,
    multibyte_query as search_multibyte_query,
    layout_overflow as search_layout_overflow,
    console_errors as search_console_errors,
    multibyte_admin_input as search_multibyte_admin_input,
)

from fess.test.ui import integration

# Leaves of the general/ and sysinfo/ packages. The default run drives the two
# composers imported above; these aliases exist so TEST_MODULES can name a
# single leaf when debugging one settings page.
from fess.test.ui.admin.general import (
    jsonResponse as general_jsonResponse,
    logLevel as general_logLevel,
    loginLink as general_loginLink,
    loginRequired as general_loginRequired,
    notificationLogin as general_notificationLogin,
    notificationSearchTop as general_notificationSearchTop,
    pagedesign as general_pagedesign,
    plugin as general_plugin,
    popularWord as general_popularWord,
    storage as general_storage,
)
from fess.test.ui.admin.sysinfo import (
    backup as sysinfo_backup,
    configinfo as sysinfo_configinfo,
    crawlinfo as sysinfo_crawlinfo,
    failureurl as sysinfo_failureurl,
    joblog as sysinfo_joblog,
    logfile as sysinfo_logfile,
    maintenance as sysinfo_maintenance,
    searchlist as sysinfo_searchlist,
    searchlog as sysinfo_searchlog,
)

logger = logging.getLogger(__name__)


def _initialize_i18n() -> dict:
    """Resolve TEST_LANG, init the i18n singleton, return banner info dict."""
    raw_lang = os.environ.get("TEST_LANG", "").strip() or None
    raw_seed = os.environ.get("TEST_LANG_SEED", "").strip()
    seed = int(raw_seed) if raw_seed else None

    lang = i18n_mod.select_language(raw_lang, seed=seed)
    label_dir = os.environ.get("FESS_LABEL_DIR", "/labels")
    i18n_mod.init(lang, label_dir)
    sizes = i18n_mod.label_sizes()

    # Note: $GITHUB_ENV is written from the host in run_test.sh (the file path
    # is host-only and unreachable from inside the runner container).

    return {
        "lang": lang,
        "browser_locale": i18n_mod.selected_browser_locale(),
        "label_dir": label_dir,
        "sizes": sizes,
        "seed": seed,
    }


def get_modules_to_run() -> List[Any]:
    """
    Get list of test modules to run based on TEST_MODULES environment variable.

    Returns:
        List of module objects to execute
    """
    # All available modules
    all_modules = {
        'accesstoken': accesstoken,
        'badword': badword,
        'boostdoc': boostdoc,
        'duplicatehost': duplicatehost,
        'elevateword': elevateword,
        'keymatch': keymatch,
        'label': label,
        'dataconfig': dataconfig,
        'pathmap': pathmap,
        'relatedcontent': relatedcontent,
        'relatedquery': relatedquery,
        'user': user,
        'group': group,
        'role': role,
        'kuromoji': kuromoji,
        'protwords': protwords,
        'mapping': mapping,
        'stemmeroverride': stemmeroverride,
        'stopwords': stopwords,
        'synonym': synonym,
        'fileauth': fileauth,
        'reqheader': reqheader,
        'scheduler': scheduler,
        'virtualhost': virtualhost,
        'webauth': webauth,
        'webconfig': webconfig,
        'fileconfig': fileconfig,
        'search_seed': search_seed,
        'search_root_top': search_root_top,
        'search_top': search_top,
        'search_help': search_help,
        'search_login_form': search_login_form,
        'search_profile_form': search_profile_form,
        'search_form_submit': search_form_submit,
        'search_query': search_query,
        'search_advance': search_advance,
        'search_no_results': search_no_results,
        'search_query_errors': search_query_errors,
        'search_error_pages': search_error_pages,
        'search_osdd': search_osdd,
        'search_logout': search_logout,
        'search_pagination': search_pagination,
        'search_facet': search_facet,
        'search_sort': search_sort,
        'search_thumbnail': search_thumbnail,
        'search_suggest': search_suggest,
        'search_related': search_related,
        'search_i18n_smoke': search_i18n_smoke,
        'search_multibyte_query': search_multibyte_query,
        'search_layout_overflow': search_layout_overflow,
        'search_console_errors': search_console_errors,
        'search_multibyte_admin_input': search_multibyte_admin_input,
        # Package composers. The default run drives these, not their leaves:
        # a leaf added to the package then runs without anyone remembering to
        # touch this file, which is exactly how the six general modules stayed
        # unregistered and unrun.
        'general': general,
        'sysinfo': sysinfo,
        'integration': integration,
        # The same leaves, addressable individually so TEST_MODULES can still
        # name one while debugging (TEST_MODULES=storage). Filtering only --
        # they are absent from the default order above by design.
        'jsonResponse': general_jsonResponse,
        'logLevel': general_logLevel,
        'loginLink': general_loginLink,
        'loginRequired': general_loginRequired,
        'notificationLogin': general_notificationLogin,
        'notificationSearchTop': general_notificationSearchTop,
        'pagedesign': general_pagedesign,
        'plugin': general_plugin,
        'popularWord': general_popularWord,
        'storage': general_storage,
        'backup': sysinfo_backup,
        'configinfo': sysinfo_configinfo,
        'crawlinfo': sysinfo_crawlinfo,
        'failureurl': sysinfo_failureurl,
        'joblog': sysinfo_joblog,
        'logfile': sysinfo_logfile,
        'maintenance': sysinfo_maintenance,
        'searchlist': sysinfo_searchlist,
        'searchlog': sysinfo_searchlog,
    }

    # Check for TEST_MODULES environment variable
    test_modules_env = os.environ.get('TEST_MODULES', 'all').strip()

    if test_modules_env == 'all':
        # Run all modules in default order
        return [
            accesstoken, badword, boostdoc, duplicatehost, elevateword,
            keymatch, label, pathmap, relatedcontent, relatedquery, user, group,
            role, kuromoji, protwords, mapping, stemmeroverride, stopwords, synonym,
            webconfig, fileconfig,
            dataconfig, fileauth, reqheader, scheduler, webauth, virtualhost,
            search_seed,
            search_root_top, search_top, search_help, search_login_form,
            search_profile_form, search_form_submit,
            search_query, search_advance, search_no_results,
            search_query_errors,
            search_pagination, search_facet, search_sort,
            search_thumbnail, search_suggest, search_related,
            search_i18n_smoke, search_multibyte_query,
            search_layout_overflow, search_console_errors,
            search_multibyte_admin_input,
            # search_osdd must precede general: /osdd is behind the
            # loginRequired gate, which general's last module toggles.
            search_error_pages, search_osdd, search_logout,
            # Cross-resource workflows. After the search modules: dictionary_workflow
            # edits the morphological analyser's dictionaries, and changed tokenisation
            # would change what the search assertions above see.
            integration,
            sysinfo,
            # Last: general's final module (loginRequired) briefly closes the
            # public UI to anonymous visitors. It restores the setting itself,
            # but if that ever fails, nothing is left queued behind it.
            general,
        ]
    else:
        # Parse comma-separated list of module names
        module_names = [name.strip() for name in test_modules_env.split(',')]
        modules = []

        for name in module_names:
            if name in all_modules:
                modules.append(all_modules[name])
                logger.info(f"Including module: {name}")
            else:
                logger.warning(f"Unknown module: {name}, skipping")

        if not modules:
            logger.error("No valid modules specified in TEST_MODULES")
            logger.info(f"Available modules: {', '.join(sorted(all_modules.keys()))}")
            sys.exit(1)

        return modules


def save_failure_screenshot(context: FessContext, module_name: str) -> str:
    """
    Save screenshot of current page on test failure.

    Args:
        context: FessContext instance
        module_name: Name of the failed module

    Returns:
        Path to saved screenshot or None if failed
    """
    try:
        page = context.get_current_page()
        if page is None:
            logger.warning("No page available for screenshot")
            return None

        # Create screenshots directory if it doesn't exist
        os.makedirs('screenshots', exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f'screenshots/failure_{module_name}_{i18n_mod.selected_lang()}_{timestamp}.png'

        # Save screenshot
        page.screenshot(path=screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")

        return screenshot_path

    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return None


def run_module(context: FessContext, module: Any, collector: ResultCollector,
               metrics: MetricsCollector) -> bool:
    """
    Run a single test module and collect results.

    Args:
        context: FessContext instance
        module: Module object with run() function
        collector: ResultCollector instance

    Returns:
        True if module passed, False otherwise
    """
    module_name = module.__name__.split('.')[-1]
    logger.info(f"Starting module: {module_name}")

    # Start module trace
    context.start_module_trace(module_name)

    start_time = time.time()
    result = None

    try:
        # Run the module
        module.run(context)

        # Module passed
        duration = time.time() - start_time
        result = TestResult(
            module=module_name,
            status='passed',
            duration=duration
        )
        collector.add_result(result)
        metrics.add_metric(module_name, duration, 'passed')

        # Stop trace without saving for passed tests (unless TRACE_ALL)
        context.stop_module_trace(save=False, status='passed')
        return True

    except AssertionError as e:
        # Test assertion failed
        duration = time.time() - start_time
        error_msg = str(e)
        screenshot_path = save_failure_screenshot(context, module_name)

        # Stop and save trace for failed tests
        trace_path = context.stop_module_trace(save=True, status='failed')

        page = context.get_current_page()
        url = page.url if page else None

        if page:
            context.html_capture.capture_on_failure(page, error_msg)

        result = TestResult(
            module=module_name,
            status='failed',
            duration=duration,
            error_message=error_msg,
            error_type='AssertionError',
            screenshot_path=screenshot_path,
            url_at_failure=url
        )
        collector.add_result(result)
        metrics.add_metric(module_name, duration, 'failed')

        logger.error(f"Module {module_name} failed: {error_msg}")
        if url:
            logger.error(f"URL at failure: {url}")
        if trace_path:
            logger.info(f"Trace available: {trace_path}")

        return False

    except Exception as e:
        # Other error (e.g., timeout, element not found)
        duration = time.time() - start_time
        error_msg = str(e)
        error_type = type(e).__name__
        screenshot_path = save_failure_screenshot(context, module_name)

        # Stop and save trace for error tests
        trace_path = context.stop_module_trace(save=True, status='error')

        page = context.get_current_page()
        url = page.url if page else None

        if page:
            context.html_capture.capture_on_failure(page, error_msg)

        result = TestResult(
            module=module_name,
            status='error',
            duration=duration,
            error_message=error_msg,
            error_type=error_type,
            screenshot_path=screenshot_path,
            url_at_failure=url
        )
        collector.add_result(result)
        metrics.add_metric(module_name, duration, 'error')

        logger.error(f"Module {module_name} error ({error_type}): {error_msg}")
        if url:
            logger.error(f"URL at failure: {url}")
        if trace_path:
            logger.info(f"Trace available: {trace_path}")

        # Also log page content for debugging
        if page:
            logger.debug(f"Page content:\n{page.content()}")

        return False


def main():
    """Main test execution function"""
    i18n_info = _initialize_i18n()

    logger.info("="*70)
    logger.info("FESS UI TEST SUITE - Starting execution")
    logger.info("="*70)
    logger.info(f"Selected language : {i18n_info['lang']}")
    logger.info(f"Browser locale    : {i18n_info['browser_locale']}")
    logger.info(f"Label directory   : {i18n_info['label_dir']} "
                f"({i18n_info['sizes']['lang']} keys + "
                f"{i18n_info['sizes']['base']} fallback)")
    if i18n_info['seed'] is not None:
        logger.info(f"Lang seed         : {i18n_info['seed']} "
                    f"(export TEST_LANG_SEED={i18n_info['seed']} to reproduce)")
    logger.info(f"Fess URL          : {os.environ.get('FESS_URL', 'unknown')}")
    logger.info("="*70)

    # Initialize result collector and metrics collector
    collector = ResultCollector()
    collector.set_environment_extra({
        "selected_language": i18n_info["lang"],
        "browser_locale_resolved": i18n_info["browser_locale"],
        "lang_seed": i18n_info["seed"],
    })
    metrics = MetricsCollector()

    # Get modules to run
    modules_to_run = get_modules_to_run()
    logger.info(f"Running {len(modules_to_run)} test modules")

    with sync_playwright() as playwright:
        context: FessContext = FessContext(playwright)

        try:
            # Login once before all tests
            context.login()
            logger.info("Successfully logged in to Fess")

            # Run all selected modules
            all_passed = True
            for module in modules_to_run:
                passed = run_module(context, module, collector, metrics)
                if not passed:
                    all_passed = False

        except Exception as e:
            # Catch any unexpected errors during setup/teardown
            logger.error(f"Fatal error during test execution: {e}", exc_info=True)
            all_passed = False

        finally:
            # Always close the context
            try:
                context.close()
                logger.info("Browser context closed")
            except Exception as e:
                logger.error(f"Error closing context: {e}")

    # Save results to JSON
    try:
        collector.save_json('test_results.json')
    except Exception as e:
        logger.error(f"Failed to save test results: {e}")

    # Save and print metrics
    try:
        metrics.save_history()
        metrics.print_metrics_summary()
    except Exception as e:
        logger.error(f"Failed to save/print metrics: {e}")

    # Print summary to console
    collector.print_summary()

    # Return appropriate exit code
    summary = collector.get_summary()
    if summary.failed > 0 or summary.errors > 0:
        logger.error("TEST SUITE FAILED")
        return 1
    else:
        logger.info("TEST SUITE PASSED")
        return 0


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
