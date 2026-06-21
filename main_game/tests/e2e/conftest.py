import pytest

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - playwright is an installed dependency
    sync_playwright = None


@pytest.fixture
def browser_available():
    """Skip e2e tests when a Chromium browser cannot actually launch.

    The Playwright Python package may be installed while the browser binary or
    its system libraries are missing (e.g. a fresh checkout without
    ``playwright install --with-deps``). In that case we skip rather than hard
    fail, so the default suite stays green; CI installs the browser and runs it.
    """
    if sync_playwright is None:
        pytest.skip("Playwright is not installed.")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            browser.close()
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Chromium is unavailable for Playwright e2e tests: {exc}")
