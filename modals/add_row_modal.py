"""
Page Object for the Catalog - Add Row modal.

Opened from a network row's '+' control in the Coverage panel of
Network Explorer.
"""
import re

from playwright.sync_api import Page, expect

from test_data import add_row_test_data as td


class AddRowModal:
    """Page Object for Catalog - Add Row."""

    def __init__(self, page: Page):
        self.page = page

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close")

        self.network_banner = page.get_by_text(
            re.compile(r"^Creating row under network:", re.IGNORECASE)
        )

        # -----------------------------------------------------------
        # Form fields
        # -----------------------------------------------------------
        self.row_name_label = page.get_by_text(
            re.compile(r"^\s*Row Name\s*\*?\s*$")
        ).first
        self.row_name_input = page.get_by_placeholder(td.ROW_NAME_PLACEHOLDER)

        self.details_label = page.get_by_text(
            re.compile(r"^\s*Details\s*\*?\s*$")
        ).first
        self.details_input = page.get_by_label(td.DETAILS_LABEL)

        self.remarks_label = page.get_by_text(
            re.compile(r"^\s*Remarks\s*\*?\s*$")
        ).first
        self.remarks_input = page.get_by_label(td.REMARKS_LABEL)

        self.active_checkbox = page.get_by_role(
            "checkbox", name=td.ACTIVE_CHECKBOX_LABEL, exact=True
        )

        self.coverage_area_label = page.get_by_text(
            td.COVERAGE_AREA_LABEL, exact=True
        )
        self.map_container = page.locator(".leaflet-container").last
        self.leaflet_zoom_in_button = page.locator("a.leaflet-control-zoom-in").last
        self.leaflet_zoom_out_button = page.locator("a.leaflet-control-zoom-out").last
        self.clear_button = page.get_by_role("button", name="Clear", exact=True).last

        # -----------------------------------------------------------
        # Actions – use type=submit to avoid matching tree '+' buttons
        # -----------------------------------------------------------
        self.submit_button = page.locator('button[type="submit"]')
        self.cancel_button = page.get_by_role("button", name=td.CANCEL_BUTTON_LABEL)

        # -----------------------------------------------------------
        # Validation / notifications
        # -----------------------------------------------------------
        self.row_name_required_error = page.get_by_text(
            re.compile(re.escape(td.ROW_NAME_REQUIRED), re.IGNORECASE)
        ).first
        self.name_too_long_error = page.get_by_text(td.ROW_NAME_TOO_LONG).first
        self.parent_network_error = page.get_by_text(td.PARENT_NETWORK_INVALID).first
        self.success_toast = page.get_by_text(td.ROW_ADDED_SUCCESS_PATTERN).first
        self.unauthenticated_error_toast = page.get_by_text(
            td.UNAUTHENTICATED_MESSAGE, exact=True
        )
        self.server_unreachable_error_toast = page.get_by_text(
            td.SERVER_UNREACHABLE_MESSAGE, exact=True
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
        self.page.mouse.click(10, 10)

    # =================================================================
    # Form actions
    # =================================================================
    def fill_row_name(self, name: str):
        expect(self.row_name_input).to_be_visible()
        self.row_name_input.fill(name)

    def clear_row_name(self):
        self.row_name_input.fill("")

    def fill_details(self, text: str):
        expect(self.details_input).to_be_visible()
        self.details_input.fill(text)

    def fill_remarks(self, text: str):
        expect(self.remarks_input).to_be_visible()
        self.remarks_input.fill(text)

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
        self.row_name_input.press("Enter")

    def draw_coverage_polygon(self, points: list[tuple[float, float]] | None = None):
        """Click relative positions on the modal map to draw a 3-vertex polygon."""
        points = points or td.ROW_POLYGON_POINTS
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
        self.page.wait_for_timeout(400)

    # =================================================================
    # Assertions
    # =================================================================
    def verify_network_banner(self, network_name: str, network_id: str | None = None):
        expect(self.network_banner).to_be_visible()
        expect(self.network_banner).to_contain_text(network_name)
        if network_id:
            expect(self.network_banner).to_contain_text(network_id)

    def verify_default_form_state(self):
        expect(self.row_name_input).to_have_value("")
        expect(self.details_input).to_have_value("")
        expect(self.remarks_input).to_have_value("")
        expect(self.active_checkbox).to_be_checked()
        expect(self.row_name_required_error).to_have_count(0)

    def verify_row_name_value(self, expected: str):
        expect(self.row_name_input).to_have_value(expected)

    def verify_details_value(self, expected: str):
        expect(self.details_input).to_have_value(expected)

    def verify_remarks_value(self, expected: str):
        expect(self.remarks_input).to_have_value(expected)

    def verify_form_elements_visible(self):
        expect(self.modal_heading).to_be_visible()
        expect(self.close_button).to_be_visible()
        expect(self.network_banner).to_be_visible()
        expect(self.row_name_label).to_be_visible()
        expect(self.row_name_input).to_be_visible()
        expect(self.details_label).to_be_visible()
        expect(self.details_input).to_be_visible()
        expect(self.remarks_label).to_be_visible()
        expect(self.remarks_input).to_be_visible()
        expect(self.active_checkbox).to_be_visible()
        expect(self.coverage_area_label).to_be_visible()
        expect(self.map_container).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def verify_row_name_has_focus(self):
        try:
            expect(self.row_name_input).to_be_focused(timeout=3000)
        except AssertionError:
            is_active = self.row_name_input.evaluate(
                "el => el === document.activeElement"
            )
            assert is_active, "Row Name field does not have keyboard focus on modal open"

    def focus_order(self, max_steps: int = 20) -> list[str]:
        known = {
            "name": self.row_name_input,
            "details": self.details_input,
            "remarks": self.remarks_input,
            "active": self.active_checkbox,
            "zoom_in": self.leaflet_zoom_in_button,
            "zoom_out": self.leaflet_zoom_out_button,
            "cancel": self.cancel_button,
            "submit": self.submit_button,
        }
        self.row_name_input.focus()
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
