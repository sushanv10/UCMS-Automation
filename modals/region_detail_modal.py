import re

from playwright.sync_api import Page, Locator, expect
from test_data import region_detail_test_data as td

# Matches the Coverage tree row text "Region: {ID} - {Name}" and captures {ID}.
_TREE_ROW_ID_PATTERN = re.compile(r"Region:\s*(\S+)\s+-\s+")


class RegionDetailsModal:
    def __init__(self, page: Page):
        self.page = page
        self._page = page

        # ID of the region whose details modal was most recently opened via
        # open_for_region_name() / open_for_row(). Read from the Coverage
        # tree at runtime - never hardcoded.
        self.opened_region_id: str | None = None

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_icon = page.get_by_title("Close")
        self.close_button = page.get_by_text("Close", exact=True)
        self.modal_container = self._page.locator('[role="dialog"]')

        # -----------------------------------------------------------
        # Field labels
        # -----------------------------------------------------------
        self.id_label = page.get_by_text("ID", exact=True)
        self.label_label = page.get_by_text("Label", exact=True)

        # -----------------------------------------------------------
        # Coverage area section (Leaflet map)
        # -----------------------------------------------------------
        self.coverage_area_heading = page.get_by_text("Coverage area", exact=True)
        self.map_container = page.locator(".leaflet-container")
        self.map_zoom_in = page.get_by_title("Zoom in")
        self.map_zoom_out = page.get_by_title("Zoom out")
        self.map_attribution = page.locator(".leaflet-control-attribution")
        self.no_polygon_text = page.get_by_text(td.NO_POLYGON_TEXT, exact=True)

        # -----------------------------------------------------------
        # Edit hand-off
        # -----------------------------------------------------------
        self.edit_button = page.get_by_role("button", name="Edit", exact=True)
        self.edit_modal_heading = page.get_by_role("heading", name=td.EDIT_MODAL_TITLE)
        self.edit_region_name_input = page.locator("#edit-region-label")

    # =================================================================
    # Locators that take a runtime-provided ID + name
    # =================================================================
    def path_text(self, region_id: str, region_name: str) -> Locator:
        """Format: "Path: {ID} - {Name}"."""
        return self._page.get_by_text(f"Path: {region_id} - {region_name}", exact=True)

    def id_value(self, region_id: str) -> Locator:
        return self._page.get_by_text(region_id, exact=True)

    def label_value(self, region_name: str) -> Locator:
        return self._page.get_by_text(region_name, exact=True)

    # =================================================================
    # Locators by NAME only (no ID needed)
    # =================================================================
    def region_tree_rows(self, region_name: str) -> Locator:
        """
        ALL tree rows whose name matches, for any auto-generated ID.
        Row format: "Region: {ID} - {Name}". More than one row is returned
        when regions share the same name.
        """
        pattern = re.compile(rf"^Region:\s+\S+\s+-\s+{re.escape(region_name)}$")
        return self._page.locator("button").filter(has_text=pattern)

    def region_tree_rows_by_prefix(self, name_prefix: str) -> Locator:
        """
        Tree rows whose name STARTS with the prefix. Used for very long
        names, which the tree shows truncated with "...".
        """
        pattern = re.compile(rf"^Region:\s+\S+\s+-\s+{re.escape(name_prefix)}")
        return self._page.locator("button").filter(has_text=pattern)

    def any_region_row(self) -> Locator:
        return self._page.locator("button").filter(has_text=re.compile(r"^Region:\s"))

    def path_text_by_name(self, region_name: str) -> Locator:
        """Matches the 'Path: {ID} - {Name}' text for any ID."""
        pattern = re.compile(rf"^Path:\s+\S+\s+-\s+{re.escape(region_name)}$")
        return self._page.get_by_text(pattern, exact=True)

    def expand_arrow_for(self, region_name: str, index: int = 0) -> Locator:
        """
        The expand/collapse arrow belonging to a region row.

        The arrow is its own button (accessible name "Collapse"/"Expand"),
        not a child of the row label. Find the closest container that holds
        both this row and an arrow button, then take its first arrow, which
        is the region's own arrow rather than one from its child networks.
        """
        row = self.region_tree_rows(region_name).nth(index)
        arrow_pattern = re.compile(r"^(collapse|expand)$", re.I)

        container = (
            self._page.locator("li, div, section")
            .filter(has=row)
            .filter(has=self._page.get_by_role("button", name=arrow_pattern))
            .last  # document order: the last match is the innermost container
        )
        return container.get_by_role("button", name=arrow_pattern).first

    # =================================================================
    # Reading IDs at runtime
    # =================================================================
    def _read_id_from_row(self, row: Locator, description: str) -> str:
        try:
            expect(row).to_be_visible(timeout=15000)
        except AssertionError:
            found = self.any_region_row().all_inner_texts()
            raise AssertionError(
                f"No tree row for {description}. "
                f"{len(found)} region rows are in the DOM, e.g.: {found[:15]}"
            )
        text = row.text_content() or ""
        match = _TREE_ROW_ID_PATTERN.search(text)
        assert match, f"Could not read a region ID from tree row text: {text!r}"
        return match.group(1)

    def get_region_id_from_tree(self, region_name: str, index: int = 0) -> str:
        row = self.region_tree_rows(region_name).nth(index)
        return self._read_id_from_row(row, f"region {region_name!r} (#{index})")

    # =================================================================
    # Actions
    # =================================================================
    def open_for_row(self, row: Locator) -> str:
        """Click a tree row's label, wait for the modal, remember the ID."""
        region_id = self._read_id_from_row(row, "the requested row")
        row.click()
        expect(self.modal_heading).to_be_visible(timeout=15000)
        self.opened_region_id = region_id
        return region_id

    def open_for_region_name(self, region_name: str, index: int = 0) -> str:
        """
        Open Region Details for a region identified by NAME only.
        `index` picks among regions that share the same name (0 = first).
        """
        return self.open_for_row(self.region_tree_rows(region_name).nth(index))

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

    def verify_opened_region_details(self, region_name: str):
        """Verify the modal for the region last opened."""
        assert self.opened_region_id, "No region has been opened yet"
        self.verify_region_details(self.opened_region_id, region_name)

    def verify_tree_row_unchanged(
        self, region_name: str, region_id: str, index: int = 0
    ):
        """After closing the modal the row must still show the same ID + name."""
        rows = self.region_tree_rows(region_name).filter(
            has_text=re.compile(rf"^Region:\s+{re.escape(region_id)}\s+-\s+")
        )
        expect(rows.first).to_be_visible()

    def verify_edit_modal_open(self):
        expect(self.edit_modal_heading).to_be_visible()

    def verify_within_viewport(self, *locators: Locator):
        """Every locator's box must lie fully inside the browser viewport."""
        size = self._page.viewport_size
        for loc in locators:
            box = loc.bounding_box()
            assert box, f"Element {loc} has no bounding box (not rendered)"
            assert box["x"] >= -1 and box["y"] >= -1, f"{loc} starts off-screen: {box}"
            assert box["x"] + box["width"] <= size["width"] + 1, (
                f"{loc} extends past the right edge: {box}"
            )
            assert box["y"] + box["height"] <= size["height"] + 1, (
                f"{loc} extends past the bottom edge: {box}"
            )

    def verify_content_within_modal(self, *locators: Locator):
        """Text elements must stay inside the modal box (long-name overflow)."""
        modal_box = self.modal_container.bounding_box()
        assert modal_box, "Modal container has no bounding box"
        for loc in locators:
            box = loc.bounding_box()
            assert box, f"Element {loc} has no bounding box"
            assert box["x"] >= modal_box["x"] - 1, f"{loc} overflows modal (left)"
            assert box["x"] + box["width"] <= modal_box["x"] + modal_box["width"] + 1, (
                f"{loc} overflows the modal on the right: element={box}, modal={modal_box}"
            )

    def verify_no_horizontal_scroll(self):
        overflow = self._page.evaluate(
            "() => document.documentElement.scrollWidth "
            "- document.documentElement.clientWidth"
        )
        assert overflow <= 0, f"Page has horizontal scroll ({overflow}px overflow)"

    def verify_modal_centred(self, tolerance_ratio: float = 0.15):
        box = self.modal_container.bounding_box()
        size = self._page.viewport_size
        assert box, "Modal container has no bounding box"
        centre_x = box["x"] + box["width"] / 2
        assert abs(centre_x - size["width"] / 2) <= size["width"] * tolerance_ratio, (
            f"Modal is not horizontally centred: centre_x={centre_x}, viewport={size}"
        )

    def script_element_for_payload(self, region_name: str) -> Locator:
        """Find a script element whose text contains the payload's JavaScript."""
        match = re.search(r"<script>(.*?)</script>", region_name, re.DOTALL)
        if not match:
            raise ValueError(
                f"Region name does not contain a script payload: {region_name!r}"
            )
        return self._page.locator("script", has_text=match.group(1))