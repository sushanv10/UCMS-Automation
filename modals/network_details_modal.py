
import re

from playwright.sync_api import Page, Locator, expect
from test_data import network_details_test_data as td


# Reads the loaded tile zoom levels from the modal's Leaflet map.
_ZOOM_REACHED_JS = r"""
(target) => {
    const zooms = [...document.querySelectorAll(
        '.leaflet-container img.leaflet-tile-loaded'
    )]
        .map(img => (img.src.match(/\/(\d+)\/\d+\/\d+/) || [])[1])
        .filter(Boolean)
        .map(Number);

    return zooms.length > 0 && Math.max(...zooms) === target;
}
"""

_CURRENT_ZOOM_JS = r"""
() => {
    const zooms = [...document.querySelectorAll(
        '.leaflet-container img.leaflet-tile-loaded'
    )]
        .map(img => (img.src.match(/\/(\d+)\/\d+\/\d+/) || [])[1])
        .filter(Boolean)
        .map(Number);

    return zooms.length > 0 ? Math.max(...zooms) : null;
}
"""


class NetworkDetailsModal:
    """
    Page object for the Network Details modal and for opening it from the
    Coverage tree.

    Regions and networks are located by NAME. Their auto-generated IDs
    are read from the tree at runtime and stored in:

        opened_region_id
        opened_network_id
    """

    def __init__(self, page: Page):
        self.page = page
        self._page = page

        self.opened_region_id: str | None = None
        self.opened_network_id: str | None = None

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role(
            "heading",
            name=td.MODAL_TITLE
        )

        self.close_icon = page.get_by_title("Close")
        self.close_button = page.get_by_text("Close", exact=True)

        self.edit_button = page.get_by_role(
            "button",
            name="Edit",
            exact=True
        )

        # -----------------------------------------------------------
        # Field labels
        # -----------------------------------------------------------
        self.id_label = page.get_by_text("ID", exact=True)
        self.label_label = page.get_by_text("Label", exact=True)
        self.region_label = page.get_by_text("Region", exact=True)
        self.status_label = page.get_by_text("Status", exact=True)

        # -----------------------------------------------------------
        # Coverage area (Leaflet map inside the modal)
        # -----------------------------------------------------------
        self.map = page.locator(".leaflet-container")

        self.zoom_in_button = self.map.locator(
            ".leaflet-control-zoom-in"
        )

        self.zoom_out_button = self.map.locator(
            ".leaflet-control-zoom-out"
        )

        self.polygon_shapes = self.map.locator(
            "path.leaflet-interactive"
        )

        self.polygon_info = page.get_by_text(
            re.compile(td.POLYGON_INFO_PATTERN)
        )

        self.no_polygon_message = page.get_by_text(
            td.NO_POLYGON_MESSAGE,
            exact=True
        )

        # -----------------------------------------------------------
        # Edit hand-off
        # -----------------------------------------------------------
        self.edit_modal_heading = page.get_by_role(
            "heading",
            name=re.compile(re.escape(td.EDIT_MODAL_TITLE))
        )

        self.edit_network_name_input = page.locator(
            "#edit-network-label"
        )

    # =================================================================
    # Field value locators
    # =================================================================

    def path_text(
        self,
        region_id: str,
        region_name: str,
        network_id: str,
        network_name: str,
    ) -> Locator:
        """
        Format:
        Path: {RegionID} - {Region} / {NetworkID} - {Network}
        """
        return self._page.get_by_text(
            f"Path: {region_id} - {region_name} / "
            f"{network_id} - {network_name}",
            exact=True
        )

    def id_value(self, network_id: str) -> Locator:
        return self._page.get_by_text(
            network_id,
            exact=True
        )

    def label_value(self, network_name: str) -> Locator:
        return self._page.get_by_text(
            network_name,
            exact=True
        )

    def region_value(self, region_id: str) -> Locator:
        return self._page.get_by_text(
            region_id,
            exact=True
        )

    def status_badge(self, status: str) -> Locator:
        return self._page.get_by_text(
            status,
            exact=True
        )

    # =================================================================
    # Coverage tree locators
    # =================================================================

    def region_rows(self, region_name: str) -> Locator:
        """
        Locate the actual region BUTTON.

        Supports:
            G188 - Region Name
            Region: G188 - Region Name

        IMPORTANT:
        This returns a button, NOT the parent tree-row container.
        """

        pattern = re.compile(
            rf"^(?:Region:\s*)?\S+\s+-\s+{re.escape(region_name)}$"
        )

        return self._page.locator("button").filter(
            has_text=pattern
        )

    def network_rows(
        self,
        region_id: str,
        network_name: str
    ) -> Locator:
        """
        Locate a network button using its region ID and network name.

        Example:
            G188-D47 - Temporary Name
            Network: G188-D47 - Temporary Name
        """

        pattern = re.compile(
            rf"^(?:Network:\s*)?{re.escape(region_id)}-\S+\s+-\s+"
            rf"{re.escape(network_name)}$"
        )

        return self._page.locator("button").filter(
            has_text=pattern
        )

    def _region_container(self, region_name: str) -> Locator:
        """
        Locate the parent tree-row container of a region button.

        region_rows() returns the button. This method finds its
        containing .map-panel-tree-row.
        """

        region_button = self.region_rows(region_name).first

        return self._page.locator(
            ".map-panel-tree-row"
        ).filter(
            has=region_button
        ).first

    # =================================================================
    # Reading IDs at runtime
    # =================================================================

    def get_region_id(self, region_name: str) -> str:
        row = self.region_rows(region_name).first

        expect(row).to_be_visible(timeout=15000)

        text = row.inner_text().strip()

        match = re.search(
            r"(?:Region:\s*)?(\S+)\s+-\s+",
            text
        )

        assert match, (
            f"Could not read a region ID from tree row. "
            f"Region: {region_name!r}, "
            f"Actual text: {text!r}"
        )

        return match.group(1)

    def get_network_id(
        self,
        region_id: str,
        network_name: str
    ) -> str:
        row = self.network_rows(
            region_id,
            network_name
        ).first

        expect(row).to_be_visible(timeout=15000)

        text = row.inner_text().strip()

        match = re.search(
            rf"({re.escape(region_id)}-\S+)\s+-\s+",
            text
        )

        assert match, (
            f"Could not read a network ID from tree row. "
            f"Network: {network_name!r}, "
            f"Actual text: {text!r}"
        )

        return match.group(1)

    # =================================================================
    # Region tree actions
    # =================================================================

    def expand_region(self, region_name: str):
        """
        Expand a region only when it is currently collapsed.
        Verify the expanded state before returning.
        """

        row = self._region_container(region_name)
        expect(row).to_be_visible(timeout=15000)

        expand_button = row.get_by_role(
            "button", name=re.compile(r"expand", re.I)
        ).first

        collapse_button = row.get_by_role(
            "button", name=re.compile(r"collapse", re.I)
        ).first

        # Already expanded
        if collapse_button.is_visible():
            return

        # Expand the region
        if expand_button.is_visible():
            expand_button.click()
            expect(collapse_button).to_be_visible(timeout=10000)
            return

        raise AssertionError(
            f"Unable to expand region '{region_name}'. "
            "Neither an expand nor a collapse button is visible."
        )

    # =================================================================
    # Add Network
    # =================================================================

    def add_network_button(self, region_name: str) -> Locator:
        """
        Locate the '+' button on the region's tree-row container.
        """

        row = self._region_container(region_name)

        named = row.get_by_role(
            "button",
            name=re.compile(r"add network", re.I)
        )

        if named.count() > 0:
            return named.first

        # Fallback: the '+' is the right-most button in the row.
        return row.locator("button").last

    def open_add_network(self, region_name: str):
        """
        Click the region's '+' control to open Add Network.
        """

        button = self.add_network_button(region_name)

        expect(button).to_be_visible(timeout=15000)
        expect(button).to_be_enabled()

        button.click()

    # =================================================================
    # Add Row (network-level '+')
    # =================================================================

    def _network_container(self, region_id: str, network_name: str) -> Locator:
        """Parent .map-panel-tree-row for a network button."""
        network_button = self.network_rows(region_id, network_name).first
        return self._page.locator(".map-panel-tree-row").filter(
            has=network_button
        ).first

    def row_rows(self, network_id: str, row_name: str) -> Locator:
        """
        Locate a row button under a network.

        Example:
            G277-D01-R01 - Banner Check Row
            Row: G277-D01-R01 - Banner Check Row
        """
        pattern = re.compile(
            rf"^(?:Row:\s*)?{re.escape(network_id)}-\S+\s+-\s+"
            rf"{re.escape(row_name)}$"
        )
        return self._page.locator("button").filter(has_text=pattern)

    def expand_network(self, region_id: str, network_name: str):
        """
        Expand a network only when it is currently collapsed.
        Verify the expanded state before returning.
        """

        row = self._network_container(region_id, network_name)
        expect(row).to_be_visible(timeout=15000)

        expand_button = row.get_by_role(
            "button", name=re.compile(r"expand", re.I)
        ).first

        collapse_button = row.get_by_role(
            "button", name=re.compile(r"collapse", re.I)
        ).first

        # Already expanded
        if collapse_button.is_visible():
            return

        # Expand the network
        if expand_button.is_visible():
            expand_button.click()
            expect(collapse_button).to_be_visible(timeout=10000)
            return

        raise AssertionError(
            f"Unable to expand network '{network_name}' "
            f"under region ID '{region_id}'. "
            "Neither an expand nor a collapse button is visible."
        )

    def add_row_button(self, region_id: str, network_name: str) -> Locator:
        """Locate the '+' (Add row) button on the network tree-row."""
        row = self._network_container(region_id, network_name)
        named = row.get_by_role(
            "button", name=re.compile(r"add row", re.I)
        )
        if named.count() > 0:
            return named.first
        return row.locator("button").last

    def open_add_row(self, region_name: str, network_name: str) -> str:
        """
        Expand the region, click the network's '+' to open Add Row.
        Returns the network ID read from the tree.
        """
        region_id = self.get_region_id(region_name)
        self.expand_region(region_name)
        network_id = self.get_network_id(region_id, network_name)

        button = self.add_row_button(region_id, network_name)
        expect(button).to_be_visible(timeout=15000)
        expect(button).to_be_enabled()
        button.click()

        self.opened_region_id = region_id
        self.opened_network_id = network_id
        return network_id

    # =================================================================
    # Open Network Details
    # =================================================================

    def open_for_network(
        self,
        region_name: str,
        network_name: str,
        wait_for_modal: bool = True,
    ) -> str:
        """
        Open Network Details for a network identified by region NAME
        and network NAME.

        Returns the network ID read from the Coverage tree.
        """

        region_id = self.get_region_id(region_name)

        self.expand_region(region_name)

        network_id = self.get_network_id(
            region_id,
            network_name
        )

        self.network_rows(
            region_id,
            network_name
        ).first.click()

        if wait_for_modal:
            expect(
                self.modal_heading
            ).to_be_visible(timeout=15000)

        self.opened_region_id = region_id
        self.opened_network_id = network_id

        return network_id

    # =================================================================
    # Modal actions
    # =================================================================

    def close_via_x(self):
        expect(self.close_icon).to_be_visible()
        self.close_icon.click()

    def close_via_button(self):
        expect(self.close_button).to_be_visible()
        self.close_button.click()

    def click_edit(self):
        expect(self.edit_button).to_be_visible()
        self.edit_button.click()

    def try_typing_into(
        self,
        locator: Locator,
        text: str
    ):
        """
        Click a field and try to type into it (read-only checks).
        """

        locator.click()
        self._page.keyboard.type(text)

    # =================================================================
    # Map actions
    # =================================================================

    def zoom_in(self, times: int = 1):
        for _ in range(times):
            self.zoom_in_button.click()

    def zoom_out(self, times: int = 1):
        for _ in range(times):
            self.zoom_out_button.click()

    def click_map_center(self):
        box = self.map.bounding_box()

        assert box is not None, (
            "Could not determine the Leaflet map bounding box."
        )

        self._page.mouse.click(
            box["x"] + box["width"] / 2,
            box["y"] + box["height"] / 2
        )

    def current_zoom(self) -> int:
        expect(
            self.map.locator(
                "img.leaflet-tile-loaded"
            ).first
        ).to_be_visible()

        zoom = self._page.evaluate(_CURRENT_ZOOM_JS)

        assert zoom is not None, (
            "Could not determine the current Leaflet zoom level."
        )

        return int(zoom)

    # =================================================================
    # Assertions
    # =================================================================

    def verify_modal_open(self):
        expect(self.modal_heading).to_be_visible()

    def verify_modal_closed(self):
        expect(self.modal_heading).to_be_hidden()

    def verify_network_details(
        self,
        region_name: str,
        network_name: str,
        status: str = td.STATUS_ACTIVE,
    ):
        """
        Verify every field of the Network Details modal.
        """

        assert (
            self.opened_network_id
            and self.opened_region_id
        ), (
            "No network opened via open_for_network()."
        )

        region_id = self.opened_region_id
        network_id = self.opened_network_id

        expect(
            self.path_text(
                region_id,
                region_name,
                network_id,
                network_name
            )
        ).to_be_visible()

        expect(self.id_label).to_be_visible()
        expect(self.id_value(network_id)).to_be_visible()

        expect(self.label_label).to_be_visible()
        expect(self.label_value(network_name)).to_be_visible()

        expect(self.region_label).to_be_visible()
        expect(self.region_value(region_id)).to_be_visible()

        expect(self.status_label).to_be_visible()
        expect(self.status_badge(status)).to_be_visible()

        expect(self.edit_button).to_be_visible()
        expect(self.close_button).to_be_visible()

    def verify_no_editable_focus(self):
        expect(
            self._page.locator(
                'input:focus, textarea:focus, '
                '[contenteditable="true"]:focus'
            )
        ).to_have_count(0)

    def verify_edit_modal_open(self):
        expect(
            self.edit_modal_heading
        ).to_be_visible()

    def verify_zoom_level(self, expected_zoom: int):
        self._page.wait_for_function(
            _ZOOM_REACHED_JS,
            arg=expected_zoom
        )

    # =================================================================
    # Long text overflow verification
    # =================================================================

    def verify_long_path_fits(
        self,
        path_locator: Locator,
        label_locator: Locator,
    ):
        """
        Verify that long Path and Label text do not overflow the modal.
        """

        for locator, field_name in (
            (path_locator, "Path"),
            (label_locator, "Label"),
        ):
            expect(locator).to_be_visible()

            dimensions = locator.evaluate(
                """el => ({
                    scrollWidth: el.scrollWidth,
                    clientWidth: el.clientWidth,
                    scrollHeight: el.scrollHeight,
                    clientHeight: el.clientHeight
                })"""
            )

            assert (
                dimensions["scrollWidth"]
                <= dimensions["clientWidth"] + 1
            ), (
                f"{field_name} text overflows horizontally: "
                f"scrollWidth={dimensions['scrollWidth']}, "
                f"clientWidth={dimensions['clientWidth']}"
            )

            assert (
                dimensions["scrollHeight"]
                <= dimensions["clientHeight"] + 1
            ), (
                f"{field_name} text overflows vertically: "
                f"scrollHeight={dimensions['scrollHeight']}, "
                f"clientHeight={dimensions['clientHeight']}"
            )

        # Verify modal controls remain visible and enabled.
        for control in (
            self.close_icon,
            self.edit_button,
            self.close_button
        ):
            expect(control).to_be_visible()
            expect(control).to_be_enabled()
            expect(control).to_be_in_viewport()
