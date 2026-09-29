from playwright.sync_api import Page, expect

from config.config import Config


class NetworkExplorerPage:
    def __init__(self, page: Page):
        self.page = page

        self.coverage_button = page.get_by_role(
            "button",
            name="Coverage",
        )

        self.zoom_in_button = page.get_by_role(
            "button",
            name="Zoom in",
        )

        self.zoom_out_button = page.get_by_role(
            "button",
            name="Zoom out",
        )

        self.select_row_message = page.get_by_text(
            "Select a row in Coverage to",
        )

    def verify_page_loaded(self):
        """Verify that the Network Explorer page is loaded."""

        expect(self.page).to_have_url(
            Config.NETWORK_EXPLORER_URL,
            timeout=15000,
        )

        expect(self.coverage_button).to_be_visible(
            timeout=15000,
        )

        expect(self.zoom_in_button).to_be_visible(
            timeout=15000,
        )

        expect(self.zoom_out_button).to_be_visible(
            timeout=15000,
        )

    def verify_map_empty_state(self):
        """Verify the initial Network Explorer map state."""

        expect(self.select_row_message).to_be_visible(
            timeout=15000,
        )

    def clear_session_data(self):
        """Clear browser cookies, local storage, and session storage."""

        # Clear browser cookies
        self.page.context.clear_cookies()

        # Clear localStorage and sessionStorage
        self.page.evaluate(
            """
            () => {
                localStorage.clear();
                sessionStorage.clear();
            }
            """
        )