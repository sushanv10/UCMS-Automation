import re

from playwright.sync_api import Page, Locator, expect
from test_data import add_region_test_data as td


class AddRegionModal:

    def __init__(self, page: Page):
        self.page = page
        self._page = page

        # -----------------------------------------------------------
        # Trigger - lives on the Coverage panel, opens this modal.
        # -----------------------------------------------------------
        self.add_region_trigger_button = page.get_by_role("button", name="Add region")

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close")

        # -----------------------------------------------------------
        # Region Name field - CONFIRMED
        # -----------------------------------------------------------
        self.region_name_label = page.get_by_text("Region Name")
        self.region_name_input = page.get_by_placeholder(td.REGION_NAME_PLACEHOLDER)

        # -----------------------------------------------------------
        # Coverage area map (Leaflet) - polygon drawing and keyboard controls
        # -----------------------------------------------------------
        self.map_container = page.locator(".leaflet-container").last
        self.leaflet_zoom_in_button = page.locator("a.leaflet-control-zoom-in")
        self.leaflet_zoom_out_button = page.locator("a.leaflet-control-zoom-out")

        # -----------------------------------------------------------
        # Actions - CONFIRMED
        # (the trigger button is also named "Add region", so the submit
        # button is found by its type instead)
        # -----------------------------------------------------------
        self.submit_button = page.locator('button[type="submit"]')
        self.cancel_button = page.get_by_role("button", name="Cancel")

        # -----------------------------------------------------------
        # Field validation errors
        # -----------------------------------------------------------
        self.region_name_required_error = page.get_by_text(
            re.compile(re.escape(td.REGION_NAME_REQUIRED), re.IGNORECASE)
        )
        self.duplicate_name_error = page.get_by_text(
            re.compile(re.escape(td.REGION_NAME_DUPLICATE), re.IGNORECASE)
        )
        self.name_too_long_error = (
            page.get_by_role("alert").filter(has_text=td.REGION_NAME_TOO_LONG)
        )

        # -----------------------------------------------------------
        # Submission notifications
        # -----------------------------------------------------------
        self.success_toast = page.get_by_text(td.REGION_ADDED_SUCCESS_PATTERN)
        # 401 - expired/cleared session (TC_021)
        self.unauthenticated_error_toast = page.get_by_text(
            td.UNAUTHENTICATED_MESSAGE, exact=True
        )
        # Offline / 5xx / aborted request (TC_018)
        self.server_unreachable_error_toast = page.get_by_text(
            td.SERVER_UNREACHABLE_MESSAGE, exact=True
        )
        # Permission denied for a user without create rights (TC_026)
        self.permission_error = page.get_by_text(td.PERMISSION_ERROR_PATTERN).first
        self.error_toast = page.get_by_role("alert")

        # -----------------------------------------------------------
        # Hierarchy tree
        # -----------------------------------------------------------
        self.hierarchy_heading = page.get_by_role("heading", name="Hierarchy")

    # =================================================================
    # Locators
    # =================================================================
    def region_tree_node(self, region_name: str) -> Locator:
        """Tree row of every region with this name ("Region: {ID} - {Name}")."""
        pattern = re.compile(rf"^Region:\s+\S+\s+-\s+{re.escape(region_name)}$")
        return self._page.get_by_text(pattern, exact=True)

    # =================================================================
    # Actions
    # =================================================================
    def open(self):
        expect(self.add_region_trigger_button).to_be_visible()
        self.add_region_trigger_button.click()
        expect(self.modal_heading).to_be_visible()

    def close_via_x(self):
        expect(self.close_button).to_be_visible()
        self.close_button.click()

    def cancel(self):
        expect(self.cancel_button).to_be_visible()
        self.cancel_button.click()

    def fill_region_name(self, name: str):
        expect(self.region_name_input).to_be_visible()
        self.region_name_input.fill(name)

    def clear_region_name(self):
        self.region_name_input.fill("")

    def draw_coverage_polygon(self, points: list[tuple[float, float]] | None = None):
        """Click the given relative positions on the modal map to draw a polygon."""
        points = points or td.POLYGON_POINTS
        expect(self.map_container).to_be_visible()

        box = self.map_container.bounding_box()
        for rel_x, rel_y in points:
            self.page.mouse.click(
                box["x"] + box["width"] * rel_x,
                box["y"] + box["height"] * rel_y,
            )
            self.page.wait_for_timeout(150)

    def submit(self):
        expect(self.submit_button).to_be_visible()
        self.submit_button.click()

    # =================================================================
    # Assertions
    # =================================================================
    def verify_modal_open(self):
        expect(self.modal_heading).to_be_visible()

    def verify_modal_closed(self):
        expect(self.modal_heading).to_be_hidden()

    def verify_hierarchy_panel_open(self):
        expect(self.hierarchy_heading).to_be_visible()

    def verify_region_tree_loaded(self):
        """At least one region row is listed in the Coverage tree."""
        expect(
            self._page.get_by_text(re.compile(r"^Region:\s+\S+\s+-\s+")).first
        ).to_be_visible(timeout=15000)

    def verify_region_name_value(self, expected: str):
        expect(self.region_name_input).to_have_value(expected)

    def verify_submit_disabled(self):
        expect(self.submit_button).to_be_disabled()

    def verify_submit_enabled(self):
        expect(self.submit_button).to_be_enabled()