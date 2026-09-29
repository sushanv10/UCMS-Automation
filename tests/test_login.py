import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from pages.login_page import LoginPage
from test_data.login_test_data import (
    CASE_SENSITIVE_PASSWORD,
    INVALID_CREDENTIALS,
    INVALID_PASSWORD,
    INVALID_USERNAME,
    LOADING_BUTTON_TEXT,
    PASSWORD_REQUIRED,
    PASSWORD_TOO_SHORT,
    SHORT_PASSWORD,
    TOO_MANY_ATTEMPTS,
    USERNAME_REQUIRED,
)


# ============================================================
# TC_LOGIN_001
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_001_login_with_valid_credentials(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_001:
    Verify login with valid username and password.

    Expected:
        User is successfully authenticated and redirected
        to the Network Explorer page.
    """

    login_page = LoginPage(page)

    username, password = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Enter valid credentials
    login_page.enter_username(username)
    login_page.enter_password(password)

    # Sign in
    login_page.click_sign_in()

    # Verify successful login
    expect(page).to_have_url(
        Config.NETWORK_EXPLORER_URL,
        timeout=15000,
    )

    print(f"\nCurrent URL: {page.url}")
    print(f"Page title: {page.title()}")

    print(
        "\nTC_LOGIN_001 passed."
        "\nUser successfully logged in."
    )


# ============================================================
# TC_LOGIN_002
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_002_sign_in_button_loading_state(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_002:
    Verify that the Sign in button shows a loading state
    and becomes disabled while the login request is processing.

    Expected:
        The Sign in button becomes disabled and displays
        the loading text while authentication is processing.
    """

    login_page = LoginPage(page)

    username, password = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Enter valid credentials
    login_page.enter_username(username)
    login_page.enter_password(password)

    # Click Sign in
    login_page.click_sign_in()

    # Verify button is disabled
    expect(
        login_page.sign_in_button
    ).to_be_disabled(
        timeout=5000
    )

    # Verify loading text
    expect(
        login_page.sign_in_button
    ).to_contain_text(
        LOADING_BUTTON_TEXT,
        timeout=10000,
    )

    print(
        "\nTC_LOGIN_002 passed."
        "\nSign in button entered the expected loading state."
    )


# ============================================================
# TC_LOGIN_003
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_003_empty_username_and_password(
    page: Page,
):
    """
    TC_LOGIN_003:
    Validate empty username and password fields.

    Expected:
        Required-field validation messages are displayed
        for both username and password.
    """

    login_page = LoginPage(page)

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Leave both fields empty
    login_page.username_input.fill("")
    login_page.password_input.fill("")

    # Click Sign in
    login_page.click_sign_in()

    # Verify username validation
    expect(
        page.get_by_text(
            USERNAME_REQUIRED,
            exact=True,
        )
    ).to_be_visible(
        timeout=5000
    )

    # Verify password validation
    expect(
        page.get_by_text(
            PASSWORD_REQUIRED,
            exact=True,
        )
    ).to_be_visible(
        timeout=5000
    )

    # Verify user remains on Login
    expect(page).to_have_url(
        Config.LOGIN_URL,
        timeout=5000,
    )

    print(
        "\nTC_LOGIN_003 passed."
        "\nUsername and password required-field validation works."
    )


# ============================================================
# TC_LOGIN_004
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_004_empty_username(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_004:
    Validate empty username field.

    Expected:
        Username required validation message is displayed.
    """

    login_page = LoginPage(page)

    _, password = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Empty username + valid password
    login_page.username_input.fill("")
    login_page.password_input.fill(password)

    # Click Sign in
    login_page.click_sign_in()

    # Verify username validation
    expect(
        page.get_by_text(
            USERNAME_REQUIRED,
            exact=True,
        )
    ).to_be_visible(
        timeout=5000
    )

    print(
        "\nTC_LOGIN_004 passed."
        "\nUsername required validation works."
    )


# ============================================================
# TC_LOGIN_005
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_005_empty_password(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_005:
    Validate empty password field.

    Expected:
        Password required validation message is displayed.
    """

    login_page = LoginPage(page)

    username, _ = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Valid username + empty password
    login_page.username_input.fill(username)
    login_page.password_input.fill("")

    # Click Sign in
    login_page.click_sign_in()

    # Verify password validation
    expect(
        page.get_by_text(
            PASSWORD_REQUIRED,
            exact=True,
        )
    ).to_be_visible(
        timeout=5000
    )

    print(
        "\nTC_LOGIN_005 passed."
        "\nPassword required validation works."
    )


# ============================================================
# TC_LOGIN_006
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_006_login_with_invalid_credentials(
    page: Page,
):
    """
    TC_LOGIN_006:
    Validate login with invalid credentials.

    Expected:
        Invalid credentials message is displayed.
    """

    login_page = LoginPage(page)

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Enter invalid credentials
    login_page.enter_username(INVALID_USERNAME)
    login_page.enter_password(INVALID_PASSWORD)

    # Click Sign in
    login_page.click_sign_in()

    # Verify error message
    expect(
        page.get_by_text(
            INVALID_CREDENTIALS,
            exact=True,
        )
    ).to_be_visible(
        timeout=5000
    )

    print(
        "\nTC_LOGIN_006 passed."
        "\nInvalid credentials were rejected correctly."
    )


# ============================================================
# TC_LOGIN_007
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_007_verify_password_case_sensitivity(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_007:
    Verify password case sensitivity.

    Expected:
        A password with incorrect casing is rejected.
    """

    login_page = LoginPage(page)

    username, _ = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Enter username and intentionally incorrect
    # case-sensitive password
    login_page.enter_username(username)
    login_page.enter_password(CASE_SENSITIVE_PASSWORD)

    # Click Sign in
    login_page.click_sign_in()

    # Verify invalid credentials
    expect(
        page.get_by_text(
            INVALID_CREDENTIALS,
            exact=True,
        )
    ).to_be_visible()

    print(
        "\nTC_LOGIN_007 passed."
        "\nPassword case sensitivity is enforced."
    )


# ============================================================
# TC_LOGIN_008
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_008_verify_password_minimum_length(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_008:
    Verify that the system enforces minimum password length.

    Expected:
        Password-too-short validation message is displayed.
    """

    login_page = LoginPage(page)

    username, _ = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Valid username + short password
    login_page.enter_username(username)
    login_page.enter_password(SHORT_PASSWORD)

    # Click Sign in
    login_page.click_sign_in()

    # Verify validation message
    expect(
        page.get_by_text(
            PASSWORD_TOO_SHORT,
            exact=True,
        )
    ).to_be_visible()

    print(
        "\nTC_LOGIN_008 passed."
        "\nPassword minimum-length validation works."
    )


# ============================================================
# TC_LOGIN_009
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_009_verify_direct_URL_access_without_authentication(
    page: Page,
):
    """
    TC_LOGIN_009:
    Verify that accessing a protected URL directly without
    authentication redirects the user to Login.

    Expected:
        Unauthenticated access to the protected Network Explorer
        redirects the browser to the Login page.
    """

    protected_url = Config.PROTECTED_URL

    # Attempt direct access to protected route
    page.goto(
        protected_url,
        wait_until="domcontentloaded",
    )

    # Verify redirect to Login
    expect(page).to_have_url(
        Config.LOGIN_URL)

    print(
        "\nTC_LOGIN_009 passed."
        "\nUnauthenticated direct access was redirected to Login."
    )


# ============================================================
# TC_LOGIN_010
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_010_session_persistence_on_refresh(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_010:
    Verify that the authenticated session persists after
    a page refresh.

    Expected:
        After successful authentication and page refresh,
        the user remains authenticated and remains on
        the Network Explorer page.
    """

    login_page = LoginPage(page)

    username, password = credentials

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Login
    login_page.login(
        username,
        password,
    )

    # Verify successful authentication
    expect(page).to_have_url(
        Config.NETWORK_EXPLORER_URL
    )

    authenticated_url = page.url

    print(
        f"\nAuthenticated URL: {authenticated_url}"
    )

    # Refresh page
    login_page.refresh_page()

    # Verify user remains on same page
    expect(page).to_have_url(
        authenticated_url,
    )

    # Verify user was not redirected to Login
    assert Config.LOGIN_URL not in page.url, (
        "User was redirected to the Login page after refresh."
    )

    print(
        "\nTC_LOGIN_010 passed."
        "\nSession persisted successfully after refresh."
        f"\nUser remained on: {page.url}"
    )


# ============================================================
# TC_LOGIN_011
# ============================================================

@pytest.mark.login
def test_TC_LOGIN_011_repeated_failed_login_attempts(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_011:
    Verify system behavior after multiple consecutive
    failed login attempts.

    Test data:
        Username: Valid username from .env
        Password: INVALID_PASSWORD
        Attempts: 6

    Expected:
        "Too Many Attempts" message is displayed after
        repeated failed login attempts.
    """

    login_page = LoginPage(page)

    username = Config.LOCKED_USERNAME

    # Navigate to Login
    login_page.navigate()

    # Verify Login page
    login_page.verify_login_page_visible()

    # Perform six failed attempts
    for attempt in range(1, 7):

        print(
            f"\nLogin attempt {attempt}/6"
        )

        # Enter valid username
        login_page.enter_username(username)

        # Enter intentionally incorrect password
        login_page.enter_password(INVALID_PASSWORD)

        # Click Sign in
        login_page.click_sign_in()

        # Attempts 1-5
        if attempt < 6:

            # Wait until request processing finishes
            # and button becomes available again.
            login_page.verify_sign_in_button_enabled()

            print(
                f"Attempt {attempt} completed with "
                "invalid credentials."
            )

        # Attempt 6
        else:
            # Verify throttling/rate-limit message
            expect(
                page.get_by_text(
                    TOO_MANY_ATTEMPTS,
                    exact=False,
                )
            ).to_be_visible()

            print(
                "\nToo Many Attempts message displayed."
            )

    print(
        "\nTC_LOGIN_011 passed."
        "\nRepeated failed login attempts were handled correctly."
    )