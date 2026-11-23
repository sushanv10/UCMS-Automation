import re

from playwright.sync_api import Page, Locator, expect

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

    # ======================================================
    # Coverage hierarchy tree
    # ======================================================

    def region_row(self, region_display: str) -> Locator:
        """
        Locate a region row in the Coverage tree by its display text
        (e.g. 'G36 - Test Region' or just the region name portion).
        """
        pattern = re.compile(re.escape(region_display), re.IGNORECASE)
        by_row = self.page.locator(".map-panel-tree-row").filter(has_text=pattern)
        by_text = self.page.get_by_text(pattern)
        return by_row.or_(by_text).first

    def network_row(self, network_name: str) -> Locator:
        """
        Locate a network node in the Coverage tree by its name.

        Tree labels often look like 'G36-D07 - Active Network', so we
        match any row that contains the network name as a substring.
        Falls back to a broader text search if the tree-row class is missing.
        """
        pattern = re.compile(re.escape(network_name), re.IGNORECASE)
        by_row = self.page.locator(".map-panel-tree-row").filter(has_text=pattern)
        by_text = self.page.get_by_text(pattern)
        return by_row.or_(by_text).first

    def click_add_network_on_region(self, region_display: str):
        """
        Click the '+' button on the given region row to open the
        Catalog - Add Network modal.
        """
        row = self.region_row(region_display)
        expect(row).to_be_visible(timeout=15000)
        # The '+' that opens Add Network is typically the last button
        # on the region row (or the one with title/aria related to add).
        add_btn = row.get_by_role("button").last
        expect(add_btn).to_be_visible()
        add_btn.click()

    def expand_region(self, region_display: str):
        """Expand a region node in the Coverage tree if it is collapsed."""
        pattern = re.compile(re.escape(region_display), re.IGNORECASE)
        # Prefer the tree-row container so we can click its expand chevron
        row = self.page.locator(".map-panel-tree-row").filter(has_text=pattern).first
        expect(row).to_be_visible(timeout=15000)
        # Expand chevron is usually the first control on the row
        expand = row.locator("button").first
        expand.click()
        self.page.wait_for_timeout(300)

    def verify_network_under_region(
        self, region_display: str, network_name: str
    ):
        """Assert that a network node is visible under the given region."""
        self.expand_region(region_display)
        expect(self.network_row(network_name)).to_be_visible(timeout=15000)

    def open_network_details(self, region_display: str, network_label: str):
        """
        Expand the region and open Network Details for the network identified
        by its unique label (never by a hard-coded ID).
        """
        self.expand_region(region_display)
        row = self.network_row(network_label)
        expect(row).to_be_visible(timeout=15000)
        # Prefer the name/button control inside the row; fall back to the row
        name_btn = row.get_by_role("button").filter(
            has_text=re.compile(re.escape(network_label), re.IGNORECASE)
        )
        if name_btn.count() > 0:
            name_btn.first.click()
        else:
            row.click()
        self.page.wait_for_timeout(400)