"""Shared pytest fixtures and hooks.

pytest-playwright already provides the `page`, `context` and `browser` fixtures
(and their setup/teardown). Here we customise them and add our own fixtures.
"""
import base64

import pytest
from playwright.sync_api import expect
from config.config import Config
from pages.login_page import LoginPage
from utils.helpers import safe_filename, timestamp


# ------------------------------------------------------------------ setup
@pytest.fixture(scope="session", autouse=True)
def _prepare_environment():
    Config.REPORTS_DIR.mkdir(exist_ok=True)
    Config.SCREENSHOTS_DIR.mkdir(exist_ok=True)
    expect.set_options(timeout=Config.DEFAULT_TIMEOUT)  # default timeout for all expect() calls


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Options used for every new browser context (one fresh context per test)."""
    return {
        **browser_context_args,
        "viewport": Config.VIEWPORT,
        # "ignore_https_errors": Config.IGNORE_HTTPS_ERRORS,
    }


# @pytest.fixture(autouse=True)
# def _default_timeouts(page):
#     page.set_default_timeout(settings.TIMEOUT_MS)
#     page.set_default_navigation_timeout(settings.TIMEOUT_MS)


# ------------------------------------------------------------------ page objects
# @pytest.fixture
# def login_page(page) -> LoginPage:
#     return LoginPage(page)


# @pytest.fixture
# def dashboard_page(page) -> DashboardPage:
#     return DashboardPage(page)


@pytest.fixture
def credentials():
    """(username, password) of the valid account, read from .env."""
    if not Config.has_valid_credentials():
        pytest.fail(
            "Valid credentials are missing. Copy .env.example to .env and set "
            "UCMS_USERNAME and UCMS_PASSWORD (or export them as environment variables)."
        )
    return Config.VALID_USERNAME, Config.VALID_PASSWORD


# @pytest.fixture
# def logged_in(login_page, dashboard_page, credentials) -> DashboardPage:
#     """Open the login page, sign in with valid credentials and return the DashboardPage."""
#     login_page.open()
#     login_page.login_and_wait(*credentials)
#     return dashboard_page


# ------------------------------------------------------------------ reporting
def pytest_html_report_title(report):
    report.title = "UCMS - Automation Report"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On failure: save a full-page screenshot and embed it in the HTML report."""
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return

    try:
        file_path = Config.SCREENSHOTS_DIR / f"{safe_filename(item.name)}_{timestamp()}.png"
        png_bytes = page.screenshot(path=str(file_path), full_page=True)

        pytest_html = item.config.pluginmanager.getplugin("html")
        if pytest_html:
            extras = getattr(report, "extras", [])
            extras.append(pytest_html.extras.png(base64.b64encode(png_bytes).decode("utf-8")))
            report.extras = extras
    except Exception as error:  # never let a screenshot problem hide the real failure
        print(f"Could not capture screenshot: {error}")

