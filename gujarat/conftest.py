import os

import pytest

from run import log_step, save_error_artifact


@pytest.fixture(autouse=True)
def _capture_page_for_artifacts(request, page):
    """Expose the Playwright page to pytest hooks for failure artifacts."""
    request.node._playwright_page = page
    yield

    keep_open = os.getenv("KEEP_BROWSER_OPEN", "").lower() in {"1", "true", "yes"}
    if keep_open and not page.is_closed():
        log_step("Keeping browser open after test completion. Press Ctrl+C when done.")
        page.wait_for_timeout(36000000)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot when a pytest test fails during execution."""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    page = getattr(item, "_playwright_page", None)
    if page is None or page.is_closed():
        return

    save_error_artifact(page, item.name)
