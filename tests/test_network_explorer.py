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
def test_TC_NETWORK_EXPLORER_002_redirects_to_login_after_session_clear(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_NETWORK_EXPLORER_002:

    Verify that the Network Explorer redirects to the Login page
    after the authenticated browser session is cleared.

    Steps:
        1. Navigate to Login.
        2. Log in using valid credentials.
        3. Verify Network Explorer is loaded.
        4. Clear cookies, localStorage, and sessionStorage.
        5. Reload Network Explorer.
        6. Verify redirection to Login.
        7. Verify Login page is displayed.

    Expected:
        After the authenticated session is removed, accessing the
        protected Network Explorer should redirect the user to Login.
    """

    login_page = LoginPage(page)
    network_explorer_page = NetworkExplorerPage(page)

    # --------------------------------------------------
    # Step 1: Navigate to Login
    # --------------------------------------------------
    login_page.navigate()
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 2: Get valid credentials
    # --------------------------------------------------
    username, password = credentials

    # --------------------------------------------------
    # Step 3: Login
    # --------------------------------------------------
    login_page.login(username, password)

    # --------------------------------------------------
    # Step 4: Verify Network Explorer
    # --------------------------------------------------
    network_explorer_page.verify_page_loaded()


    # --------------------------------------------------
    # Step 5: Clear authenticated session
    # --------------------------------------------------
    network_explorer_page.clear_session_data()


    # --------------------------------------------------
    # Step 6: Reload protected page
    # --------------------------------------------------
    page.reload(
        wait_until="domcontentloaded"
    )

    # --------------------------------------------------
    # Step 7: Verify redirect to Login
    # --------------------------------------------------
    expect(page).to_have_url(
        Config.LOGIN_URL
    )

    # --------------------------------------------------
    # Step 8: Verify Login page
    # --------------------------------------------------
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 9: Verify Network Explorer is no longer visible
    # --------------------------------------------------
    expect(
        network_explorer_page.coverage_button
    ).not_to_be_visible(timeout=5000)

@pytest.mark.network_explorer
def test_TC_NETWORK_EXPLORER_003_coverage_panel_opens(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_NETWORK_EXPLORER_003:

    Verify that the Coverage panel opens correctly
    after clicking the Coverage button.
    """

    login_page = LoginPage(page)
    network_explorer_page = NetworkExplorerPage(page)

    # --------------------------------------------------
    # Step 1: Navigate to Login
    # --------------------------------------------------
    login_page.navigate()
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 2: Get valid credentials
    # --------------------------------------------------
    username, password = credentials

    # --------------------------------------------------
    # Step 3: Login
    # --------------------------------------------------
    login_page.login(username, password)

    # --------------------------------------------------
    # Step 4: Verify Network Explorer
    # --------------------------------------------------
    network_explorer_page.verify_page_loaded()

    # --------------------------------------------------
    # Step 5: Open Coverage panel
    # --------------------------------------------------
    network_explorer_page.open_coverage_panel()

    # --------------------------------------------------
    # Step 6: Verify Coverage panel
    # --------------------------------------------------
    network_explorer_page.verify_coverage_panel_open()

@pytest.mark.network_explorer
def test_TC_NETWORK_EXPLORER_004_coverage_panel_closes(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_NETWORK_EXPLORER_004:

    Verify that the Coverage panel closes after clicking
    the Close button.
    """

    login_page = LoginPage(page)
    network_explorer_page = NetworkExplorerPage(page)

    # --------------------------------------------------
    # Step 1: Navigate to Login
    # --------------------------------------------------
    login_page.navigate()
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 2: Get valid credentials
    # --------------------------------------------------
    username, password = credentials

    # --------------------------------------------------
    # Step 3: Login
    # --------------------------------------------------
    login_page.login(username, password)

    # --------------------------------------------------
    # Step 4: Verify Network Explorer
    # --------------------------------------------------
    network_explorer_page.verify_page_loaded()

    # --------------------------------------------------
    # Step 5: Open Coverage panel
    # --------------------------------------------------
    network_explorer_page.open_coverage_panel()
    network_explorer_page.verify_coverage_panel_open()

    # --------------------------------------------------
    # Step 6: Close Coverage panel
    # --------------------------------------------------
    network_explorer_page.close_coverage_panel()

    # --------------------------------------------------
    # Step 7: Verify Coverage panel is closed
    # --------------------------------------------------
    network_explorer_page.verify_coverage_panel_closed()