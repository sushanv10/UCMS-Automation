
import pytest
from playwright.sync_api import Page, expect
from config.config import Config
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage


@pytest.mark.network_explorer
def test_TC_NETWORK_EXPLORER_001_page_load(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_NETWORK_EXPLORER_001:
    Verify that the Network Explorer page
    loads with all required data after login.

    After successful login, the user is redirected
    to the Network Explorer page.
    """

    login_page = LoginPage(page)
    network_explorer_page = NetworkExplorerPage(page)

    # --------------------------------------------------
    # Step 1: Navigate to login page
    # --------------------------------------------------
    login_page.navigate()

    # Verify login page is displayed
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 2: Get valid credentials from fixture
    # --------------------------------------------------
    username, password = credentials

    # --------------------------------------------------
    # Step 3: Sign in successfully
    # --------------------------------------------------
    login_page.login(username, password)

    # --------------------------------------------------
    # Step 4: Verify navigation to Network Explorer
    # --------------------------------------------------
    network_explorer_page.verify_page_loaded()

    print(
        f"\nUser successfully redirected to: {page.url}"
    )

    # --------------------------------------------------
    # Step 5: Verify required page data/elements
    # --------------------------------------------------
    network_explorer_page.verify_map_empty_state()

    print(
        "\nNetwork Explorer page loaded successfully."
    )
    print(
        "Required page elements are displayed."
    )

@pytest.mark.network_explorer
def test_TC_NETWORK_EXPLORER_002_redirects_to_login_after_session_clear(page: Page, credentials: tuple[str, str]):
    """
    TC_NETWORK_EXPLORER_002:
    Verify that the Network Explorer redirects to the login page
    after clearing cookies and session data.

    Steps:
    1. Log in to the application.
    2. Navigate to the Network Explorer.
    3. Clear browser cookies, local storage, and session storage.
    4. Reload the Network Explorer page.
    5. Verify that the user is redirected to the Login page.

    Expected:
        The system should detect that the session is no longer valid
        and redirect the user to the Login page.
    """

    login_page = LoginPage(page)
    network_explorer_page = NetworkExplorerPage(page)

    # --------------------------------------------------
    # Step 1: Navigate to login page
    # --------------------------------------------------
    login_page.navigate()

    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 2: Get valid credentials
    # --------------------------------------------------
    username, password = credentials

    # --------------------------------------------------
    # Step 3: Log in successfully
    # --------------------------------------------------
    login_page.login(username, password)

    # --------------------------------------------------
    # Step 4: Verify Network Explorer is loaded
    # --------------------------------------------------
    network_explorer_page.verify_page_loaded()

    print(
        f"\nUser successfully logged in."
        f"\nCurrent URL: {page.url}"
    )

    # --------------------------------------------------
    # Step 5: Clear cookies and browser session data
    # --------------------------------------------------
    network_explorer_page.clear_session_data()

    print(
        "\nCookies, localStorage, and sessionStorage cleared."
    )

    # --------------------------------------------------
    # Step 6: Reload Network Explorer
    # --------------------------------------------------
    page.reload()

    print(
        f"\nURL after session data was cleared: {page.url}"
    )

    # --------------------------------------------------
    # Step 7: Verify redirect to Login page
    # --------------------------------------------------
    expect(page).to_have_url(
        Config.LOGIN_URL,
        timeout=15000,
    )

    # --------------------------------------------------
    # Step 8: Verify Login page is displayed
    # --------------------------------------------------
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 9: Verify protected Network Explorer content
    #         is no longer accessible
    # --------------------------------------------------
    expect(
        network_explorer_page.select_row_message
    ).not_to_be_visible(timeout=3000)

    print(
        "\nTC_DASHBOARD_002 passed."
        "\nSession was invalidated and the user was "
        "redirected to the Login page."
    )