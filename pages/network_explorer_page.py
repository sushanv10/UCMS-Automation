from playwright.sync_api import Page, expect

from config.config import Config


class NetworkExplorerPage:
    def __init__(self, page: Page):
        self.page = page

        # --------------------------------------------------
        # Network Explorer
        # --------------------------------------------------
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

        # --------------------------------------------------
        # Coverage panel
        # --------------------------------------------------
        self.coverage_heading = page.get_by_role(
            "heading",
            name="Coverage",
            exact=True,
        )

        self.coverage_close_button = page.get_by_label(
            "Close",
            exact=True,
        )

    # ======================================================
    # Network Explorer
    # ======================================================

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

    # ======================================================
    # Coverage panel
    # ======================================================

    def open_coverage_panel(self):
        """Open the Coverage panel."""

        expect(self.coverage_button).to_be_visible(
            timeout=15000,
        )

        self.coverage_button.click()

    def verify_coverage_panel_open(self):
        """Verify that the Coverage panel is visible."""

        expect(self.coverage_heading).to_be_visible(
            timeout=15000,
        )

    def close_coverage_panel(self):
        """Close the Coverage panel using the close button."""

        expect(self.coverage_close_button).to_be_visible(
            timeout=15000,
        )

        self.coverage_close_button.click()

    def verify_coverage_panel_closed(self):
        """Verify that the Coverage panel is closed."""

        expect(self.coverage_heading).not_to_be_visible(
            timeout=5000,
        )

    # ======================================================
    # Session
    # ======================================================

    def clear_session_data(self):
        """Clear authentication cookies and browser storage."""

        # Clear authentication cookies
        self.page.context.clear_cookies()

        # Clear browser storage
        self.page.evaluate(
            """
            () => {
                localStorage.clear();
                sessionStorage.clear();
            }
            """
        )