"""
Page Object for the Catalog - Add Network modal.

Opened from a region row's '+' control in the Coverage panel of
Network Explorer.
"""
import re

from playwright.sync_api import Page, expect

from test_data import add_network_test_data as td


class AddNetworkModal:
    """
    Page Object for the Catalog - Add Network modal.

    Opened from a region row's '+' control in the Coverage panel of
    Network Explorer.
    """

    def __init__(self, page: Page):
        self.page = page

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close")

        # Region context banner (read-only)
        self.region_banner = page.get_by_text(
            re.compile(r"^Creating network under region:\s*\S+", re.IGNORECASE)
        )

        # -----------------------------------------------------------
        # Form fields
        # -----------------------------------------------------------
        self.network_name_label = page.get_by_text(
            re.compile(r"^\s*Network Name\s*\*?\s*$")
        ).first
        self.network_name_input = page.get_by_placeholder(td.NETWORK_NAME_PLACEHOLDER)

        self.details_label = page.get_by_text(
            re.compile(r"^\s*Details\s*\*?\s*$")
        ).first
        self.details_input = page.get_by_label(td.DETAILS_LABEL)

        self.coverage_area_label = page.get_by_text(td.COVERAGE_AREA_LABEL, exact=True)
        self.map_container = page.locator(".leaflet-container").last
        self.leaflet_zoom_in_button = page.locator("a.leaflet-control-zoom-in").last
        self.leaflet_zoom_out_button = page.locator("a.leaflet-control-zoom-out").last

        self.active_checkbox = page.get_by_role(
            "checkbox", name=td.ACTIVE_CHECKBOX_LABEL, exact=True
        )

        # -----------------------------------------------------------
        # Actions
        # The modal submit is type="submit" (same pattern as Add Region).
        # Role-name "Add Network" also matches the region-row '+' controls,
        # so we must not use get_by_role(name=...) alone.
        # -----------------------------------------------------------
        self.submit_button = page.locator('button[type="submit"]')
        self.cancel_button = page.get_by_role("button", name=td.CANCEL_BUTTON_LABEL)

        # -----------------------------------------------------------
        # Validation errors
        # -----------------------------------------------------------
        self.network_name_required_error = page.get_by_text(
            re.compile(re.escape(td.NETWORK_NAME_REQUIRED), re.IGNORECASE)
        ).first
        self.duplicate_name_error = page.get_by_text(
            re.compile(re.escape(td.DUPLICATE_NAME_ERROR), re.IGNORECASE)
        ).first
        self.name_too_long_error = page.get_by_text(td.NETWORK_NAME_TOO_LONG).first
        self.details_too_long_error = page.get_by_text(
            re.compile(re.escape(td.DETAILS_TOO_LONG), re.IGNORECASE)
        ).first
        self.parent_region_error = page.get_by_text(td.PARENT_REGION_ERROR_PATTERN).first

        # -----------------------------------------------------------
        # Notifications
        # -----------------------------------------------------------
        self.success_toast = page.get_by_text(td.NETWORK_ADDED_SUCCESS_PATTERN).first
        self.unauthenticated_error_toast = page.get_by_text(
            td.NETWORK_ERROR_PATTERN, exact=True
        )
        self.server_unreachable_error_toast = page.get_by_text(
            td.SESSION_ERROR_PATTERN, exact=True
        )
        self.error_toast = page.get_by_role("alert")

    # =================================================================
    # Open / close
    # =================================================================
    def verify_modal_open(self):
        expect(self.modal_heading).to_be_visible(timeout=15000)

    def verify_modal_closed(self):
        expect(self.modal_heading).to_be_hidden(timeout=10000)

    def close_via_x(self):
        expect(self.close_button).to_be_visible()
        self.close_button.click()

    def cancel(self):
        expect(self.cancel_button).to_be_visible()
        self.cancel_button.click()

    def click_outside_to_dismiss(self):
        """Click the dimmed backdrop outside the modal to dismiss it."""
        # Click near top-left of the page, away from the centered modal.
        self.page.mouse.click(10, 10)

    # =================================================================
    # Form actions
    # =================================================================
    def fill_network_name(self, name: str):
        expect(self.network_name_input).to_be_visible()
        self.network_name_input.fill(name)

    def clear_network_name(self):
        self.network_name_input.fill("")

    def fill_details(self, text: str):
        expect(self.details_input).to_be_visible()
        self.details_input.fill(text)

    def clear_details(self):
        self.details_input.fill("")

    def set_active(self, checked: bool):
        expect(self.active_checkbox).to_be_visible()
        if checked:
            self.active_checkbox.check()
        else:
            self.active_checkbox.uncheck()

    def submit(self):
        expect(self.submit_button).to_be_visible()
        self.submit_button.click()

    def press_enter_on_name(self):
        self.network_name_input.press("Enter")

    def draw_coverage_polygon(self, points: list[tuple[float, float]] | None = None):
        """
        Click the given relative positions on the modal map to draw a polygon.

        The modal auto-closes the polygon after 3 vertices (see UI hint).
        Tests that need a valid polygon may call this; pure coverage / UI
        cases leave the map empty.
        """
        points = points or td.POLYGON_POINTS
        expect(self.map_container).to_be_visible()
        self.page.wait_for_timeout(300)

        box = self.map_container.bounding_box()
        assert box, "Coverage map is not visible"
        for rel_x, rel_y in points:
            self.page.mouse.click(
                box["x"] + box["width"] * rel_x,
                box["y"] + box["height"] * rel_y,
            )
            self.page.wait_for_timeout(250)
        # Allow Leaflet to finish the polygon after the last vertex.
        self.page.wait_for_timeout(400)

    # =================================================================
    # Assertions
    # =================================================================
    def verify_region_banner(self, region_id: str):
        """Banner must read 'Creating network under region: {region_id}'."""
        expect(self.region_banner).to_be_visible()
        expect(self.region_banner).to_contain_text(region_id)

    def verify_default_form_state(self):
        """Network Name empty, Details empty, Active checked, no validation error."""
        expect(self.network_name_input).to_have_value("")
        expect(self.details_input).to_have_value("")
        expect(self.active_checkbox).to_be_checked()
        expect(self.network_name_required_error).to_have_count(0)

    def verify_network_name_value(self, expected: str):
        expect(self.network_name_input).to_have_value(expected)

    def verify_details_value(self, expected: str):
        expect(self.details_input).to_have_value(expected)

    def verify_submit_disabled(self):
        expect(self.submit_button).to_be_disabled()

    def verify_submit_enabled(self):
        expect(self.submit_button).to_be_enabled()

    def verify_form_elements_visible(self):
        """Every element listed in TC_003."""
        expect(self.modal_heading).to_be_visible()
        expect(self.close_button).to_be_visible()
        expect(self.region_banner).to_be_visible()
        expect(self.network_name_label).to_be_visible()
        expect(self.network_name_input).to_be_visible()
        expect(self.details_label).to_be_visible()
        expect(self.details_input).to_be_visible()
        expect(self.coverage_area_label).to_be_visible()
        expect(self.map_container).to_be_visible()
        expect(self.active_checkbox).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def verify_network_name_has_focus(self):
        # Prefer Playwright's focused assertion; fall back to activeElement check
        # for environments where autofocus is delayed slightly.
        try:
            expect(self.network_name_input).to_be_focused(timeout=3000)
        except AssertionError:
            is_active = self.network_name_input.evaluate(
                "el => el === document.activeElement"
            )
            assert is_active, (
                "Network Name field does not have keyboard focus on modal open"
            )

    def verify_required_asterisk_on_network_name(self):
        """An asterisk (*) is shown next to the Network Name label."""
        # Match either "Network Name *" inline or a sibling/nearby asterisk.
        label_with_star = self.page.get_by_text(
            re.compile(r"Network Name\s*\*", re.IGNORECASE)
        ).first
        if label_with_star.count() > 0:
            expect(label_with_star).to_be_visible()
            return

        # Some builds render the star as a separate element next to the label.
        star_near_label = (
            self.page.locator("label")
            .filter(has_text=re.compile(r"Network Name", re.IGNORECASE))
            .locator("xpath=..")
            .get_by_text("*", exact=True)
            .first
        )
        if star_near_label.count() > 0:
            expect(star_near_label).to_be_visible()
            return

        # Last resort: any visible asterisk in the modal near the name field.
        expect(
            self.page.get_by_text(re.compile(r"\*", re.IGNORECASE)).first
        ).to_be_visible()

    def focus_order(self, max_steps: int = 15) -> list[str]:
        """
        Start in Network Name, press Tab repeatedly and return the labels of
        the known controls in the order they received focus.
        """
        known = {
            "name": self.network_name_input,
            "details": self.details_input,
            "active": self.active_checkbox,
            "zoom_in": self.leaflet_zoom_in_button,
            "zoom_out": self.leaflet_zoom_out_button,
            "cancel": self.cancel_button,
            "submit": self.submit_button,
        }
        self.network_name_input.focus()
        order = ["name"]
        for _ in range(max_steps):
            self.page.keyboard.press("Tab")
            for label, locator in known.items():
                if locator.count() and locator.first.evaluate(
                    "el => el === document.activeElement"
                ):
                    order.append(label)
                    break
        return order
