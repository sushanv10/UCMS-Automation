import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from pages.login_page import LoginPage
from test_data.login_test_data import CASE_SENSITIVE_PASSWORD, INVALID_CREDENTIALS, INVALID_PASSWORD, INVALID_USERNAME, LOADING_BUTTON_TEXT, PASSWORD_REQUIRED, PASSWORD_TOO_SHORT, SHORT_PASSWORD, TOO_MANY_ATTEMPTS, USERNAME_REQUIRED



@pytest.mark.login
def test_TC_LOGIN_001_login_with_valid_credentials(page: Page, credentials: tuple[str, str]):
    """
    TC_LOGIN_001:
    Verify login with valid username and password.
    """

    username, password = credentials

    login_page = LoginPage(page)

    # 1. Navigate to login page
    login_page.navigate()

    # 2. Verify login form
    login_page.verify_login_page_visible()

    # 3. Fill credentials from .env
    login_page.enter_username(username)
    login_page.enter_password(password)

    # 4. Click Sign in
    login_page.click_sign_in()

    # 5. Wait for login processing
    page.wait_for_timeout(3000)

    print(f"\nCurrent URL: {page.url}")
    print(f"Page title: {page.title()}")


    # 6. Verify successful login
    expect(page).to_have_url(
        Config.NETWORK_EXPLORER_URL,
        timeout=15000,
    )

@pytest.mark.login
def test_TC_LOGIN_002_sign_in_button_loading_state(page: Page, credentials: tuple[str, str]):
    """
    TC_LOGIN_002:
    Verify that the Sign in button shows a loading state
    and becomes disabled while the login request is processing.

    Steps:
    1. Navigate to the login page.
    2. Enter a valid username.
    3. Enter a valid password.
    4. Click the Sign in button.
    5. Verify that the button shows a loading state.
    6. Verify that the button is disabled during processing.
    """

    login_page = LoginPage(page)

    # 1. Navigate to the login page
    login_page.navigate()

    # 2. Verify the login form
    login_page.verify_login_page_visible()

    # 3. Load valid credentials from .env
    username, password = credentials

    # 4. Enter valid username and password
    login_page.enter_username(username)
    login_page.enter_password(password)

    # 5. Click Sign in
    login_page.click_sign_in()

    # 6. Verify loading text and disabled state
    expect(login_page.sign_in_button).to_be_disabled(
        timeout=5000
    )

    expect(login_page.sign_in_button).to_contain_text(
        LOADING_BUTTON_TEXT,
        timeout=5000,
    )


@pytest.mark.login
def test_TC_LOGIN_003_empty_username_and_password(page: Page):
    """
    TC_LOGIN_003:
    Validate empty username and password fields.

    Steps:
    1. Navigate to the login page.
    2. Leave the username field empty.
    3. Leave the password field empty.
    4. Click the Sign in button.
    5. Verify both required-field validation messages.
    """

    login_page = LoginPage(page)

    # 1. Navigate to the login page
    login_page.navigate()

    # 2. Verify that the login form is visible
    login_page.verify_login_page_visible()

    # 3. Make sure both fields are empty
    login_page.username_input.fill("")
    login_page.password_input.fill("")

    # 4. Click Sign in
    login_page.click_sign_in()

    # 5. Verify username validation message
    expect(page.get_by_text(USERNAME_REQUIRED, exact=True)).to_be_visible(
        timeout=5000
    )

    # 6. Verify password validation message
    expect(page.get_by_text(PASSWORD_REQUIRED, exact=True)).to_be_visible(
        timeout=5000
    )

    # 7. Verify that the user remains on the login page
    expect(page).to_have_url(
        Config.LOGIN_URL,
        timeout=5000,
    )

@pytest.mark.login
def test_TC_LOGIN_004_empty_username(page: Page):
    """
    TC_LOGIN_004:
    Validate empty username field.

    Steps:
    1. Navigate to the login page.
    2. Leave the username field empty.
    3. Enter a valid password.
    4. Click the Sign in button.
    5. Verify the required-field validation message for the username.
    """

    login_page = LoginPage(page)

    # 1. Navigate to the login page
    login_page.navigate()

    # 2. Verify that the login form is visible
    login_page.verify_login_page_visible()

    # 3. Make sure username field is empty and enter a valid password
    login_page.username_input.fill("")
    login_page.password_input.fill(Config.VALID_PASSWORD)

    # 4. Click Sign in
    login_page.click_sign_in()

    # 5. Verify username validation message
    expect(page.get_by_text(USERNAME_REQUIRED, exact=True)).to_be_visible(
        timeout=5000
    )

@pytest.mark.login
def test_TC_LOGIN_005_empty_password(page: Page):
    login_page = LoginPage(page)

    login_page.navigate()

    login_page.verify_login_page_visible()

    # 3. Make sure password field is empty and enter a valid username
    login_page.username_input.fill(Config.VALID_USERNAME)
    login_page.password_input.fill("")

    # Click Sign in
    login_page.click_sign_in()

    # Verify password validation message
    expect(page.get_by_text(PASSWORD_REQUIRED, exact=True)).to_be_visible(
        timeout=5000
    )

@pytest.mark.login
def test_TC_LOGIN_006_login_with_invalid_credentials(page: Page):
    """
    TC_LOGIN_006:
    Validate login with invalid credentials.

    Steps:
    1. Navigate to the login page.
    2. Enter invalid username.
    3. Enter invalid password.
    4. Click the Sign in button.
    """
    login_page = LoginPage(page)

    # Navigate to login page 
    login_page.navigate()

    # Verify login form is visible
    login_page.verify_login_page_visible()

    # Enter invalid credentials
    login_page.enter_username(INVALID_USERNAME)
    login_page.enter_password(INVALID_PASSWORD)

    # Click Sign in
    login_page.click_sign_in()

    # Verify invalid credentials message
    expect(page.get_by_text(INVALID_CREDENTIALS, exact=True)).to_be_visible(
        timeout=5000
    )

@pytest.mark.login
def test_TC_LOGIN_007_verify_password_case_sensitivity(page: Page):
    login_page = LoginPage(page)

    login_page.navigate()

    login_page.verify_login_page_visible()

    # Enter valid username and case-sensitive password
    login_page.enter_username(Config.VALID_USERNAME)
    login_page.enter_password(CASE_SENSITIVE_PASSWORD)

    # Click Sign in
    login_page.click_sign_in()

    # Verify invalid credentials message
    expect(page.get_by_text(INVALID_CREDENTIALS, exact=True)).to_be_visible(
        timeout=5000
    )

    
@pytest.mark.login 
def test_TC_LOGIN_008_verify_password_minimum_length(page: Page):
    """
    TC_LOGIN_008:
    Verify that the system enforces a minimum password length.

    Steps:
    1. Navigate to the login page.
    2. Enter a valid username.
    3. Enter a password shorter than the minimum required length (e.g., 8 characters).
    4. Click the Sign in button.
    5. Verify that the appropriate validation message is displayed.
    """

    login_page = LoginPage(page)

    # 1. Navigate to the login page
    login_page.navigate()

    # 2. Verify that the login form is visible
    login_page.verify_login_page_visible()

    # 3. Enter a valid username and a short password
    login_page.enter_username(Config.VALID_USERNAME)
    login_page.enter_password(SHORT_PASSWORD)

    # 4. Click the Sign in button
    login_page.click_sign_in()

    # 5. Verify that the appropriate validation message is displayed
    expect(page.get_by_text(
        PASSWORD_TOO_SHORT, exact=True,)).to_be_visible(
        timeout=5000
    )

@pytest.mark.login 
def test_TC_LOGIN_009_verify_direct_URL_access_without_authentication(page: Page):
    """
    TC_LOGIN_009:
    Verify that accessing a protected URL directly without authentication
    redirects the user to the login page.

    Steps:
    1. Attempt to access a protected URL (/map) directly.
    2. Verify that the user is redirected to the login page.
    """

    # 1. Attempt to access a protected URL directly
    protected_url = Config.PROTECTED_URL
    page.goto(protected_url)

    # 2. Verify that the user is redirected to the login page
    expect(page).to_have_url(
        Config.LOGIN_URL,
        timeout=5000,
    )
    

@pytest.mark.login
def test_tc_login_010_session_persistence_on_refresh(page: Page):
    """
    TC_LOGIN_010:
    Verify that the authenticated session persists after a page refresh.

    Steps:
    1. Navigate to the login page.
    2. Sign in successfully using valid credentials.
    3. Verify successful login.
    4. Store the authenticated page URL.
    5. Refresh the browser page.
    6. Verify the user remains logged in.
    7. Verify the user remains on the same page and is not
       redirected to the login page.
    """

    login_page = LoginPage(page)

    # ---------------------------------------------------------
    # 1. Navigate to login page
    # ---------------------------------------------------------
    login_page.navigate()

    # Verify login form
    login_page.verify_login_page_visible()

    # ---------------------------------------------------------
    # 2. Load valid credentials from .env
    # ---------------------------------------------------------
    username = Config.VALID_USERNAME
    password = Config.VALID_PASSWORD

    if not username or not password:
        pytest.fail(
            "VALID_USERNAME and VALID_PASSWORD "
            "must be configured in the .env file."
        )

    # ---------------------------------------------------------
    # 3. Login successfully
    # ---------------------------------------------------------
    login_page.login(username, password)

    # ---------------------------------------------------------
    # 4. Verify successful login
    # ---------------------------------------------------------
    expect(page).to_have_url(
        Config.NETWORK_EXPLORER_URL,
        timeout=15000,
    )

    # Save the URL after successful authentication
    authenticated_url = page.url

    print(f"\nAuthenticated URL: {authenticated_url}")

    # ---------------------------------------------------------
    # 5. Refresh the browser page
    # ---------------------------------------------------------
    login_page.refresh_page()

    # ---------------------------------------------------------
    # 6. Verify user remains on the same page
    # ---------------------------------------------------------
    expect(page).to_have_url(
        authenticated_url,
        timeout=15000,
    )

    # ---------------------------------------------------------
    # 7. Verify user was NOT redirected to login
    # ---------------------------------------------------------
    assert Config.LOGIN_URL not in page.url, (
        "User was redirected to the login page after refresh."
    )

    print(
        "\nSession persistence verified successfully."
    )
    print(
        f"User remained on: {page.url}"
    )

@pytest.mark.login
def test_tc_login_011_repeated_failed_login_attempts(
    page: Page,
    credentials: tuple[str, str],
):
    """
    TC_LOGIN_011:
    Verify system behavior after multiple consecutive failed login attempts.

    Test data:
        Username: Valid username from .env
        Password: test_password
        Attempts: 6

    Expected:
        "Too Many Attempts" message should be displayed
        after repeated failed login attempts.
    """

    login_page = LoginPage(page)

    # --------------------------------------------------
    # Step 1: Navigate to login page
    # --------------------------------------------------
    login_page.navigate()

    # Verify login form is visible
    login_page.verify_login_page_visible()

    # --------------------------------------------------
    # Step 2: Get valid username from credentials fixture
    # --------------------------------------------------
    username, _ = credentials

    # --------------------------------------------------
    # Step 3: Perform 6 consecutive failed login attempts
    # --------------------------------------------------
    for attempt in range(1, 7):

        print(f"\nLogin attempt {attempt}/6")

        # Enter valid username
        login_page.enter_username(username)

        # Enter intentionally incorrect password
        login_page.enter_password(INVALID_PASSWORD)

        # Click Sign in
        login_page.click_sign_in()

        # --------------------------------------------------
        # Attempts 1-5
        # --------------------------------------------------
        if attempt < 6:

            # Wait for the login request to complete.
            # This also confirms the button is no longer
            # in the loading/disabled state.
            login_page.verify_sign_in_button_enabled()

            print(
                f"Attempt {attempt} completed with invalid credentials."
            )

        # --------------------------------------------------
        # Attempt 6
        # --------------------------------------------------
        else:

            # Verify account/request throttling message
            expect(
                page.get_by_text(
                    TOO_MANY_ATTEMPTS,
                    exact=False,
                )
            ).to_be_visible(
                timeout=5000
            )

            print(
                "\nToo Many Attempts message displayed."
            )

    print(
        "\nTC_LOGIN_011 passed."
        "\nRepeated failed login attempts were handled correctly."
    )