"""
Shared pytest fixtures and hooks for the UCMS automation framework.

pytest-playwright provides the standard `page`, `context`, and `browser`
fixtures. This file only customizes browser settings, credentials,
diagnostics, and failure reporting.
"""

import base64

import pytest
from playwright.sync_api import expect

from config.config import Config
from utils.helpers import safe_filename, timestamp


# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def _prepare_environment():
    """
    Prepare framework directories and configure the default Playwright
    expect() timeout for the entire test session.
    """
    Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    expect.set_options(timeout=Config.DEFAULT_TIMEOUT)


# ============================================================================
# PLAYWRIGHT BROWSER CONTEXT
# ============================================================================

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Configure every Playwright browser context.

    pytest-playwright still creates a fresh browser context for each test.
    This fixture only adds the project's viewport configuration.
    """
    return {
        **browser_context_args,
        "viewport": Config.VIEWPORT,
    }


# ============================================================================
# CREDENTIALS
# ============================================================================

@pytest.fixture
def credentials():
    """
    Return the valid UCMS username and password from .env.
    """
    if not Config.has_valid_credentials():
        pytest.fail(
            "Valid credentials are missing. "
            "Copy .env.example to .env and configure "
            "VALID_USERNAME and VALID_PASSWORD."
        )

    return Config.VALID_USERNAME, Config.VALID_PASSWORD

@pytest.fixture
def restricted_credentials():
    """
    Return the restricted-role UCMS username and password from .env.
    Used for nav bar role-based visibility tests (TC_NAVBAR_017, 018, 043, 059)
    where this account must lack access to at least one module (e.g. Outages
    or Port Allocations - confirm which with whoever seeded the test account).
    """
    if not Config.has_restricted_credentials():
        pytest.fail(
            "Restricted-role credentials are missing. "
            "Set RESTRICTED_USERNAME and RESTRICTED_PASSWORD in .env."
        )

    return Config.RESTRICTED_USERNAME, Config.RESTRICTED_PASSWORD


# ============================================================================
# AUTHENTICATION / SESSION DIAGNOSTICS
# ============================================================================

@pytest.fixture
def auth_debug(page):
    """
    Diagnostic helper for authentication/session-related tests.

    Usage:

        auth_debug("After login")
        auth_debug("After clearing session")
        auth_debug("After reload")

    This fixture does not modify browser state.
    """

    def log_state(label: str):
        print("\n" + "=" * 70)
        print(f"AUTH DEBUG: {label}")
        print("=" * 70)

        # ------------------------------------------------------------------
        # URL
        # ------------------------------------------------------------------
        print(f"URL: {page.url}")

        # ------------------------------------------------------------------
        # Browser context
        # ------------------------------------------------------------------
        print(f"Page ID: {id(page)}")
        print(f"Context ID: {id(page.context)}")

        # ------------------------------------------------------------------
        # Cookies
        # ------------------------------------------------------------------
        try:
            cookies = page.context.cookies()

            print("\nCookies:")

            if not cookies:
                print("  []")

            for cookie in cookies:
                value = cookie.get("value", "")

                # Don't print the complete authentication cookie value.
                masked_value = (
                    f"{value[:20]}..."
                    if len(value) > 20
                    else value
                )

                print(
                    f"  {cookie.get('name')}={masked_value} "
                    f"(httpOnly={cookie.get('httpOnly')}, "
                    f"secure={cookie.get('secure')}, "
                    f"sameSite={cookie.get('sameSite')})"
                )

        except Exception as error:
            print(f"Could not read cookies: {error}")

        # ------------------------------------------------------------------
        # Local storage
        # ------------------------------------------------------------------
        try:
            local_storage = page.evaluate(
                "() => Object.fromEntries(Object.entries(localStorage))"
            )

            print("\nLocal Storage:")
            print(local_storage)

        except Exception as error:
            print(f"Could not read localStorage: {error}")

        # ------------------------------------------------------------------
        # Session storage
        # ------------------------------------------------------------------
        try:
            session_storage = page.evaluate(
                "() => Object.fromEntries(Object.entries(sessionStorage))"
            )

            print("\nSession Storage:")
            print(session_storage)

        except Exception as error:
            print(f"Could not read sessionStorage: {error}")

        # ------------------------------------------------------------------
        # IndexedDB
        # ------------------------------------------------------------------
        try:
            indexed_db = page.evaluate(
                """
                async () => {
                    if (!window.indexedDB) {
                        return [];
                    }

                    const databases = await indexedDB.databases();

                    return databases.map(db => ({
                        name: db.name,
                        version: db.version
                    }));
                }
                """
            )

            print("\nIndexedDB:")
            print(indexed_db)

        except Exception as error:
            print(f"Could not read IndexedDB: {error}")

        print("=" * 70 + "\n")

    return log_state


@pytest.fixture
def auth_network_debug(page):
    """
    Capture authentication-related network responses.

    This is intended mainly for debugging session/login issues.

    It does not modify requests or responses.
    """

    def log_response(response):
        url = response.url.lower()

        relevant_keywords = (
            "login",
            "logout",
            "session",
            "auth",
            "token",
            "user",
        )

        if not any(keyword in url for keyword in relevant_keywords):
            return

        print("\n" + "-" * 70)
        print("AUTH NETWORK RESPONSE")
        print("-" * 70)

        print(f"Status : {response.status}")
        print(f"Method : {response.request.method}")
        print(f"Type   : {response.request.resource_type}")
        print(f"URL    : {response.url}")

        try:
            set_cookie = response.headers.get("set-cookie")

            if set_cookie:
                print(f"Set-Cookie: {set_cookie}")

        except Exception as error:
            print(f"Could not read response headers: {error}")

        print("-" * 70)

    page.on("response", log_response)

    return log_response


# ============================================================================
# FAILURE SCREENSHOT / HTML REPORT
# ============================================================================

def pytest_html_report_title(report):
    """
    Set the title of the pytest HTML report.
    """
    report.title = "UCMS-Automation Report"


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # Only capture screenshots for failures during the actual test call.
    if report.when != "call" or not report.failed:
        return

    page = item.funcargs.get("page")

    if page is None:
        return

    try:
        filename = (
            f"{safe_filename(item.name)}_"
            f"{timestamp()}.png"
        )

        file_path = Config.SCREENSHOTS_DIR / filename

        png_bytes = page.screenshot(
            path=str(file_path),
            full_page=True,
        )

        pytest_html = item.config.pluginmanager.getplugin("html")

        if pytest_html:
            extras = getattr(report, "extras", [])

            extras.append(
                pytest_html.extras.png(
                    base64.b64encode(png_bytes).decode("utf-8")
                )
            )

            report.extras = extras

        print(
            f"\nFailure screenshot saved: {file_path}"
        )

    except Exception as error:
        # Never allow screenshot/reporting errors to hide the actual
        # test failure.
        print(
            f"\nCould not capture failure screenshot: {error}"
        )

@pytest.fixture
def auth_network_debug(page):
    def log_response(response):
        url = response.url.lower()

        if not any(
            keyword in url
            for keyword in ("login", "auth", "session", "token")
        ):
            return

        print("\n" + "=" * 70)
        print("AUTH RESPONSE")
        print("=" * 70)

        print(f"Status : {response.status}")
        print(f"Method : {response.request.method}")
        print(f"Type   : {response.request.resource_type}")
        print(f"URL    : {response.url}")

        try:
            headers = response.headers

            for header in (
                "retry-after",
                "x-ratelimit-limit",
                "x-ratelimit-remaining",
                "x-ratelimit-reset",
            ):
                value = headers.get(header)

                if value is not None:
                    print(f"{header}: {value}")

        except Exception as error:
            print(f"Could not read response headers: {error}")

        # Only inspect the actual login POST response.
        if (
            response.request.method.upper() == "POST"
            and "/api/auth/login" in response.url
        ):
            try:
                print("\nLOGIN RESPONSE BODY:")
                print(response.text())
            except Exception as error:
                print(f"Could not read response body: {error}")

        print("=" * 70)

    page.on("response", log_response)

    return log_response