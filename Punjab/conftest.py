import os

import pytest

from run import log_step, save_error_artifact


# @pytest.fixture(autouse=True)
# def _capture_page_for_artifacts(request, page):
#     """Expose the Playwright page to pytest hooks for failure artifacts."""
#     request.node._playwright_page = page

#     yield  # ── test runs here ──

#     # ── teardown: runs whether the test passed, failed, or errored ────────────
#     keep_open = os.getenv("KEEP_BROWSER_OPEN", "").lower() in {"1", "true", "yes"}
#     if keep_open and not page.is_closed():
#         log_step("Browser staying open. Press ENTER in this terminal to close it.")
#         try:
#             input("\n[KEEP_BROWSER_OPEN] Press ENTER to close the browser and exit...\n")
#         except (EOFError, KeyboardInterrupt):
#             pass  # Ctrl+C or non-interactive shell → just continue teardown

@pytest.fixture(autouse=True)
def _capture_page_for_artifacts(request, page):
    """Expose the Playwright page to pytest hooks for failure artifacts."""
    request.node._playwright_page = page
    yield

    keep_open = os.getenv("KEEP_BROWSER_OPEN", "").lower() in {"1", "true", "yes"}
    rep_call = getattr(request.node, "rep_call", None)

    # 🔥 NEW: keep browser open even on failure
    if keep_open and rep_call and rep_call.failed:
        log_step("Test failed — browser kept open for debugging.")
        input("Press ENTER to close browser...")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot when a pytest test fails during execution."""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when != "call" or report.passed:
        return

    page = getattr(item, "_playwright_page", None)
    if page is None or page.is_closed():
        return

    save_error_artifact(page, item.name)

    summary = ""
    if call.excinfo is not None:
        summary = str(call.excinfo.value).strip()
    elif hasattr(report, "longreprtext"):
        summary = report.longreprtext.strip().splitlines()[-1]

    if summary:
        log_step(f"Failure reason: {summary[:220]}")
