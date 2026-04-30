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
from fess.test.coverage import (
    CoverageAnalyzer,
    InventoryManager,
    CoverageReporter,
    TestStubGenerator,
)
from fess.test.ui.admin import (accesstoken,
                                badword,
                                boostdoc,
                                dataconfig,
                                duplicatehost,
                                elevateword,
                                fileauth,
                                keymatch,
                                label,
                                pathmap,
                                relatedcontent,
                                relatedquery,
                                reqheader,
                                scheduler,
                                user,
                                group,
                                role,
                                virtualhost,
                                webauth,
                                webconfig,
                                fileconfig)

from fess.test.ui.admin.general import (popularWord,
                                        pagedesign,
                                        storage,
                                        plugin)

from fess.test.ui.admin.sysinfo import (backup,
                                        configinfo,
                                        crawlinfo,
                                        failureurl,
                                        joblog,
                                        logfile,
                                        maintenance,
                                        searchlist,
                                        searchlog)

from fess.test.ui.admin.dict import (kuromoji,
                                     protwords,
                                     mapping,
                                     stemmeroverride,
                                     stopwords,
                                     synonym)

from fess.test.ui.search import (
    facet as search_facet,
    no_results as search_no_results,
    pagination as search_pagination,
    query as search_query,
    related as search_related,
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

# Integration tests are available but not run by default
# Uncomment the following line to include integration tests in test runs
# from fess.test.ui import integration

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

    # Export resolved lang to $GITHUB_ENV for CI artifact naming
    gh_env = os.environ.get("GITHUB_ENV")
    if gh_env:
        try:
            with open(gh_env, "a", encoding="utf-8") as f:
                f.write(f"TEST_LANG_RESOLVED={lang}\n")
        except Exception as e:
            logger.warning(f"Failed to export TEST_LANG_RESOLVED to GITHUB_ENV: {e}")

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
        'search_top': search_top,
        'search_query': search_query,
        'search_no_results': search_no_results,
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
        'popularWord': popularWord,
        # Admin read-only: general sub-pages
        'pagedesign': pagedesign,
        'storage': storage,
        'plugin': plugin,
        # Admin read-only: system info
        'searchlog': searchlog,
        'joblog': joblog,
        'searchlist': searchlist,
        'crawlinfo': crawlinfo,
        'failureurl': failureurl,
        'logfile': logfile,
        'backup': backup,
        'maintenance': maintenance,
        'configinfo': configinfo,
        # 'integration': integration,  # Uncomment to enable
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
            search_top, search_query, search_no_results,
            search_pagination, search_facet, search_sort,
            search_thumbnail, search_suggest, search_related,
            search_i18n_smoke, search_multibyte_query,
            search_layout_overflow, search_console_errors,
            search_multibyte_admin_input,
            popularWord,
            # Admin read-only: general
            pagedesign, storage, plugin,
            # Admin read-only: system info (data-independent structural first)
            configinfo, logfile,
            crawlinfo, joblog, failureurl,
            searchlog, searchlist,
            backup, maintenance,
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

    # Run coverage analysis if HTML capture was enabled
    try:
        run_coverage_analysis()
    except Exception as e:
        logger.error(f"Failed to run coverage analysis: {e}")

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


def run_coverage_analysis() -> None:
    """
    Run coverage analysis on captured HTML files.

    This function analyzes HTML snapshots captured during test execution,
    calculates coverage metrics, and generates reports.
    """
    coverage_enabled = os.environ.get("COVERAGE_ANALYSIS", "false").lower() == "true"
    html_capture_dir = os.environ.get("HTML_CAPTURE_DIR", "html_snapshots")

    if not coverage_enabled:
        logger.debug("Coverage analysis is disabled (set COVERAGE_ANALYSIS=true to enable)")
        return

    if not os.path.exists(html_capture_dir):
        logger.info(f"No HTML snapshots found in {html_capture_dir}")
        return

    logger.info("=" * 60)
    logger.info("COVERAGE ANALYSIS - Starting")
    logger.info("=" * 60)

    # Initialize components
    analyzer = CoverageAnalyzer()
    inventory_manager = InventoryManager()
    report_format = os.environ.get("COVERAGE_REPORT_FORMAT", "json")
    report_dir = os.environ.get("COVERAGE_REPORT_DIR", "coverage_reports")
    reporter = CoverageReporter(output_dir=report_dir)

    # Analyze HTML files
    inventories = analyzer.analyze_directory(html_capture_dir)
    if not inventories:
        logger.warning("No HTML files found for analysis")
        return

    logger.info(f"Analyzed {len(inventories)} HTML snapshots")

    # Add inventories to manager
    for inv in inventories:
        inventory_manager.add_inventory(inv)

    # Import test logs to identify tested elements
    log_file = os.environ.get("LOG_FILE_PATH")
    if log_file and os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        inventory_manager.import_test_logs(log_content)

    # Calculate coverage for each page
    page_coverages = {}
    for url_path in inventory_manager._inventories.keys():
        coverage = inventory_manager.calculate_coverage(url_path)
        if coverage:
            page_coverages[url_path] = coverage

    # Identify coverage gaps
    gaps = inventory_manager.identify_gaps(min_priority=0.5)

    # Generate reports
    if report_format == "all":
        reporter.generate_report(page_coverages, gaps, "json")
        reporter.generate_report(page_coverages, gaps, "html")
        reporter.generate_report(page_coverages, gaps, "md")
    else:
        reporter.generate_report(page_coverages, gaps, report_format)

    # Print console summary
    reporter.print_console_summary(page_coverages, gaps)

    # Generate test stubs if gaps found
    generate_stubs = os.environ.get("COVERAGE_GENERATE_STUBS", "false").lower() == "true"
    if generate_stubs and gaps:
        stub_dir = os.environ.get("COVERAGE_STUB_DIR", "generated_tests")
        generator = TestStubGenerator(output_dir=stub_dir)
        generator.generate_from_gaps(gaps)
        logger.info(f"Generated test stubs in {stub_dir}")

    # Save inventory for future reference
    inventory_manager.save_inventory()

    logger.info("Coverage analysis completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    setup_logging()
    sys.exit(main())
