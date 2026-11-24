# Login Page 

from playwright.sync_api import Page, expect
from config.config import Config
from test_data.login_test_data import LOADING_BUTTON_TEXT


class LoginPage:

    def __init__(self, page: Page):
        self.page = page

        # Locators
        self.username_input = page.locator("#username")
        self.password_input = page.locator("#password")
        self.sign_in_button = page.locator('button[type="submit"]')
    
        

    def navigate(self):
        """Navigate to the UCMS login page."""
        self.page.goto(
            Config.LOGIN_URL, 
            wait_until="domcontentloaded"
        )
    

    def enter_username(self, username: str):
        """Enter username."""
        expect(self.username_input).to_be_visible()
        expect(self.username_input).to_be_editable()
        self.username_input.fill(username)

    def enter_password(self, password: str):
        """Enter password."""
        expect(self.password_input).to_be_visible()
        expect(self.password_input).to_be_editable()
        self.password_input.fill(password)

    def click_sign_in(self):
        """Click the Sign in button."""
        expect(self.sign_in_button).to_be_visible()
        expect(self.sign_in_button).to_be_enabled()
        self.sign_in_button.click()

    def verify_sign_in_button_loading(self):
        """
        Verify that the Sign in button displays a loading state
        and is disabled while the request is processing.
        """

        # Verify that the button is disabled.
        expect(self.sign_in_button).to_be_disabled(
            timeout=5000
        )

        # Verify the loading text.
        expect(self.sign_in_button).to_contain_text(
            LOADING_BUTTON_TEXT,
            timeout=5000,
        )

    def verify_sign_in_button_enabled(self):
        """Verify that the Sign in button is enabled."""
        expect(self.sign_in_button).to_be_enabled(
            timeout=15000
        )

    def login(self, username: str, password: str):
        """Perform login using the provided credentials."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_sign_in()

    def verify_login_successful(self):
        expect(self.page).to_have_url(
            Config.NETWORK_EXPLORER_URL,
            timeout=15000,
        )

    def refresh_page(self):
        """Refresh the current page."""
        self.page.reload(wait_until="domcontentloaded")
    
    def verify_login_page_visible(self):
        """Verify that the login form is visible."""
        expect(self.username_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.sign_in_button).to_be_visible()