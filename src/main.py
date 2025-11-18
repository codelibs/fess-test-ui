import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Any

from playwright.sync_api import sync_playwright

from fess.test.ui import FessContext
from fess.test.result import ResultCollector, TestResult
from fess.test.metrics import MetricsCollector
from fess.test.ui.admin import (accesstoken,
                                badword,
                                boostdoc,
                                crawlinginfo,
                                dataconfig,
                                duplicatehost,
                                elevateword,
                                failureurl,
                                fileauth,
                                fileconfig,
                                group,
                                keymatch,
                                label,
                                pathmap,
                                relatedcontent,
                                relatedquery,
                                reqheader,
                                role,
                                scheduler,
                                user,
                                webauth,
                                webconfig)

from fess.test.ui.admin.dict import (kuromoji,
                                     protwords,
                                     mapping,
                                     stemmeroverride)

# Integration tests are available but not run by default
# Uncomment the following line to include integration tests in test runs
# from fess.test.ui import integration

logger = logging.getLogger(__name__)


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
        'crawlinginfo': crawlinginfo,
        'dataconfig': dataconfig,
        'duplicatehost': duplicatehost,
        'elevateword': elevateword,
        'failureurl': failureurl,
        'fileauth': fileauth,
        'fileconfig': fileconfig,
        'group': group,
        'keymatch': keymatch,
        'kuromoji': kuromoji,
        'label': label,
        'mapping': mapping,
        'pathmap': pathmap,
        'protwords': protwords,
        'relatedcontent': relatedcontent,
        'relatedquery': relatedquery,
        'reqheader': reqheader,
        'role': role,
        'scheduler': scheduler,
        'stemmeroverride': stemmeroverride,
        'user': user,
        'webauth': webauth,
        'webconfig': webconfig,
        # 'integration': integration,  # Uncomment to enable
    }

    # Check for TEST_MODULES environment variable
    test_modules_env = os.environ.get('TEST_MODULES', 'all').strip()

    if test_modules_env == 'all':
        # Run all modules in default order
        return [
            accesstoken, badword, boostdoc, crawlinginfo, dataconfig,
            duplicatehost, elevateword, failureurl, fileauth, fileconfig,
            group, keymatch, kuromoji, label, mapping, pathmap,
            protwords, relatedcontent, relatedquery, reqheader, role,
            scheduler, stemmeroverride, user, webauth, webconfig
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
        screenshot_path = f'screenshots/failure_{module_name}_{timestamp}.png'

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
        return True

    except AssertionError as e:
        # Test assertion failed
        duration = time.time() - start_time
        error_msg = str(e)
        screenshot_path = save_failure_screenshot(context, module_name)

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

        return False

    except Exception as e:
        # Other error (e.g., timeout, element not found)
        duration = time.time() - start_time
        error_msg = str(e)
        error_type = type(e).__name__
        screenshot_path = save_failure_screenshot(context, module_name)

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

        # Also log page content for debugging
        if page:
            logger.debug(f"Page content:\n{page.content()}")

        return False


def main():
    """Main test execution function"""
    logger.info("="*70)
    logger.info("FESS UI TEST SUITE - Starting execution")
    logger.info("="*70)

    # Initialize result collector and metrics collector
    collector = ResultCollector()
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
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
