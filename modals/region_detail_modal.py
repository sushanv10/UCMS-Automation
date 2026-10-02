import re

from playwright.sync_api import Page, Locator, expect
from test_data import region_detail_test_data as td

class RegionDetailsModal:
    def __init__(self, page: Page):
        self.page = page
        self._page = page

        # -----------------------------------------------------------
        # Modal chrome - CONFIRMED
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_icon = page.get_by_title("Close")
        self.close_button = page.get_by_text("Close", exact=True)

        # -----------------------------------------------------------
        # Field labels - CONFIRMED
        # -----------------------------------------------------------
        self.id_label = page.get_by_text("ID", exact=True)
        self.label_label = page.get_by_text("Label", exact=True)

        # Modal container locator (for visibility checks)
        self.modal_container = self._page.locator(
            '[role="dialog"]'
        )

        # -----------------------------------------------------------
        # Edit hand-off 
        # -----------------------------------------------------------
        self.edit_button = page.get_by_role("button", name=re.compile(r"Edit", re.IGNORECASE))
        self.edit_modal_heading = page.get_by_role("heading", name=td.EDIT_MODAL_TITLE)
        # The Edit Region form reuses the same Region Name field as Add
        # Region (same placeholder).
        self.edit_region_name_input = page.locator("#edit-region-label")

        self.expand_arrow = page.get_by_role("button", name="Collapse")
        

    # =================================================================
    # Locators needing a known region ID + name
    # =================================================================
    def region_tree_row(self, region_id: str, region_name: str) -> Locator:
        """
        The region's row/button in the Coverage hierarchy tree.
        CONFIRMED format: "Region: {ID} - {Name}".
        """
        name = f"Region: {region_id} - {region_name}"
        return self._page.get_by_role("button", name=name, exact=True)

    def path_text(self, region_id: str, region_name: str) -> Locator:
        """CONFIRMED format: "Path: {ID} - {Name}"."""
        return self._page.get_by_text(f"Path: {region_id} - {region_name}", exact=True)

    def id_value(self, region_id: str) -> Locator:
        return self._page.get_by_text(region_id, exact=True)

    def label_value(self, region_name: str) -> Locator:
        return self._page.get_by_text(region_name, exact=True)


    # =================================================================
    # Locators for when the ID is NOT known ahead of time
    # =================================================================
    def region_tree_row_by_name(self, region_name: str) -> Locator:
        """Matches the tree row button for any auto-generated ID."""
        pattern = re.compile(rf"^Region:\s+\S+\s+-\s+{re.escape(region_name)}$")
        return self._page.get_by_role("button", name=pattern)

    def path_text_by_name(self, region_name: str) -> Locator:
        """Matches the 'Path: {ID} - {Name}' text for any ID."""
        pattern = re.compile(rf"^Path:\s+\S+\s+-\s+{re.escape(region_name)}$")
        return self._page.get_by_text(pattern, exact=True)

    def get_id_from_path(self, region_name: str) -> str:
        """
        Read back whatever ID the server actually assigned, by parsing the
        'Path: {ID} - {Name}' text. Use this for regions created during the
        test itself, where the ID can't be hardcoded in advance.
        """
        text = self.path_text_by_name(region_name).text_content() or ""
        match = re.match(r"^Path:\s+(\S+)\s+-\s+", text)
        return match.group(1) if match else ""
    

    # =================================================================
    # Actions
    # =================================================================
    def open_for_region(
        self,
        region_id: str,
        region_name: str,
    ):
        """Open Region Details for an exact region using ID + name."""
        row = self.region_tree_row(
            region_id,
            region_name,
        )

        expect(row).to_be_visible(timeout=15000)
        row.click()

        expect(
            self.modal_heading
        ).to_be_visible(timeout=15000)

        
    def open_for_region_name(self, region_name: str):
        """Open Region Details without needing to know the ID in advance."""

        row = self._page.locator("button").filter(
            has_text=re.compile(
                rf"^Region:\s+\S+\s+-\s+{re.escape(region_name)}$"
            )
        )

        expect(row).to_be_visible(timeout=15000)
        row.click()

        expect(self.modal_heading).to_be_visible(timeout=15000)

    def close_via_x(self):
        expect(self.close_icon).to_be_visible()
        self.close_icon.click()

    def close_via_button(self):
        expect(self.close_button).to_be_visible()
        self.close_button.click()

    def click_edit(self):
        expect(self.edit_button).to_be_visible()
        self.edit_button.click()

    # =================================================================
    # Assertions
    # =================================================================
    def verify_modal_open(self):
        expect(self.modal_heading).to_be_visible()

    def verify_modal_closed(self):
        expect(self.modal_heading).to_be_hidden()

    def verify_region_details(self, region_id: str, region_name: str):
        expect(self.path_text(region_id, region_name)).to_be_visible()
        expect(self.id_label).to_be_visible()
        expect(self.id_value(region_id)).to_be_visible()
        expect(self.label_label).to_be_visible()
        expect(self.label_value(region_name)).to_be_visible()

    def verify_edit_modal_open(self):
        expect(self.edit_modal_heading).to_be_visible()

    def script_element_for_payload(self, region_name: str) -> Locator:
        """
        Find a script element whose text contains the JavaScript payload
        from the supplied region name.
        """

        match = re.search(
            r"<script>(.*?)</script>",
            region_name,
            re.DOTALL,
        )

        if not match:
            raise ValueError(
                f"Region name does not contain a script payload: {region_name!r}"
            )

        script_content = match.group(1)

        return self._page.locator(
            "script",
            has_text=script_content,
        )