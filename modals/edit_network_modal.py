import re

from playwright.sync_api import Page, expect

from test_data import edit_network_test_data as td


class EditNetworkModal:
    """
    Page Object for the Catalog - Edit Network modal.

    Opened from Network Details via the Edit button
    (see NetworkDetailsModal.click_edit).
    """

    def __init__(self, page: Page):
        self.page = page

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close").last

        # -----------------------------------------------------------
        # Form fields (labels / inputs)
        # -----------------------------------------------------------
        self.network_name_label = page.get_by_text(
            re.compile(r"^\s*Network Name\s*\*?\s*$")
        ).first
        self.network_name_input = page.get_by_label("Network Name")

        self.details_label = page.get_by_text(
            re.compile(r"^\s*Details\s*\*?\s*$")
        ).first
        self.details_input = page.get_by_label("Details")

        self.active_checkbox = page.get_by_role("checkbox", name="Active", exact=True)

        # -----------------------------------------------------------
        # Coverage area (map inside the modal)
        # TODO: confirm accessible names of the expand icon / Clear button
        #       and the wording of the vertex-count caption.
        # -----------------------------------------------------------
        self.coverage_label = page.get_by_text("Coverage area", exact=True)
        self.map_container = page.locator(".leaflet-container").last
        self.zoom_in_button = page.locator("a.leaflet-control-zoom-in").last
        self.zoom_out_button = page.locator("a.leaflet-control-zoom-out").last
        self.polygon_shapes = self.map_container.locator("path.leaflet-interactive")
        self.expand_map_button = page.get_by_role(
            "button",
            name=re.compile(r"^(expand|enlarge|full ?screen|maximi[sz]e)", re.IGNORECASE),
        ).last
        self.clear_button = page.get_by_role("button", name="Clear", exact=True).last
        self.vertex_caption = page.get_by_text(
            re.compile(r"\d+\s+vert(ex|ices)", re.IGNORECASE)
        ).first

        # -----------------------------------------------------------
        # Actions (the submit button text changes to "Please wait..." while
        # loading, so both labels are matched)
        # -----------------------------------------------------------
        self.update_button = page.get_by_role(
            "button", name=re.compile(r"^(Update Network|Please wait)", re.IGNORECASE)
        )
        self.cancel_button = page.get_by_role("button", name=td.CANCEL_BUTTON_LABEL)

        # -----------------------------------------------------------
        # Validation errors
        # -----------------------------------------------------------
        self.name_required_error = page.get_by_text(
            re.compile(re.escape(td.NETWORK_NAME_REQUIRED), re.IGNORECASE)
        ).first
        self.duplicate_name_error = page.get_by_text(td.DUPLICATE_ERROR_PATTERN).first
        self.name_too_long_error = page.get_by_text(td.NETWORK_NAME_TOO_LONG).first
        self.details_too_long_error = page.get_by_text(td.DETAILS_TOO_LONG_PATTERN).first

        # -----------------------------------------------------------
        # Notifications
        # -----------------------------------------------------------
        self.success_toast = page.get_by_text(td.SUCCESS_PATTERN).first
        self.unauthenticated_error_toast = page.get_by_text(
            td.UNAUTHENTICATED_MESSAGE, exact=True
        )
        self.server_unreachable_error_toast = page.get_by_text(
            td.SERVER_UNREACHABLE_MESSAGE, exact=True
        )
        self.error_toast = page.get_by_role("alert")
        # "an error showed up" - exact toast or any alert
        self.error_notification = self.server_unreachable_error_toast.or_(
            self.error_toast
        ).first

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

    # =================================================================
    # Form actions
    # =================================================================
    def fill_network_name(self, name: str):
        expect(self.network_name_input).to_be_visible()
        self.network_name_input.fill(name)

    def clear_network_name(self):
        self.network_name_input.fill("")

    def type_into_network_name(self, text: str):
        """Type at the end of the existing value (does not clear first)."""
        expect(self.network_name_input).to_be_visible()
        self.network_name_input.click()
        self.network_name_input.press("End")
        self.network_name_input.press_sequentially(text)

    def press_enter_on_name(self):
        self.network_name_input.press("Enter")

    def fill_details(self, text: str):
        expect(self.details_input).to_be_visible()
        self.details_input.fill(text)

    def set_active(self, checked: bool):
        expect(self.active_checkbox).to_be_visible()
        if checked:
            self.active_checkbox.check()
        else:
            self.active_checkbox.uncheck()

    def update(self):
        expect(self.update_button).to_be_visible()
        self.update_button.click()

    def add_polygon_vertex(self, point: tuple[float, float] = td.NEW_VERTEX_POINT):
        """Click the map to add one vertex (relative position in the map)."""
        box = self.map_container.bounding_box()
        assert box, "Coverage map is not visible"
        self.page.mouse.click(
            box["x"] + box["width"] * point[0],
            box["y"] + box["height"] * point[1],
        )

    def focus_order(self, max_steps: int = 15) -> list[str]:
        """
        Start in Network Name, press Tab repeatedly and return the labels of
        the known controls in the order they received focus.
        """
        known = {
            "name": self.network_name_input,
            "details": self.details_input,
            "active": self.active_checkbox,
            "zoom_in": self.zoom_in_button,
            "zoom_out": self.zoom_out_button,
            "cancel": self.cancel_button,
            "update": self.update_button,
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

    # =================================================================
    # Assertions
    # =================================================================
    def verify_network_name_value(self, expected: str):
        expect(self.network_name_input).to_have_value(expected)

    def verify_details_value(self, expected: str):
        expect(self.details_input).to_have_value(expected)

    def verify_vertex_count(self, count: int):
        expect(
            self.page.get_by_text(
                re.compile(rf"\b{count}\s+vert(ex|ices)", re.IGNORECASE)
            ).first
        ).to_be_visible()

    def verify_update_enabled(self):
        expect(self.update_button).to_be_enabled()

    def verify_update_disabled(self):
        expect(self.update_button).to_be_disabled()

    def verify_elements_visible(self):
        """Every element listed in TC_003."""
        expect(self.modal_heading).to_be_visible()
        expect(self.close_button).to_be_visible()
        expect(self.network_name_label).to_be_visible()
        expect(self.network_name_input).to_be_visible()
        expect(self.details_label).to_be_visible()
        expect(self.details_input).to_be_visible()
        expect(self.coverage_label).to_be_visible()
        expect(self.map_container).to_be_visible()
        expect(self.zoom_in_button).to_be_visible()
        expect(self.zoom_out_button).to_be_visible()
        expect(self.expand_map_button).to_be_visible()
        expect(self.clear_button).to_be_visible()
        expect(self.vertex_caption).to_be_visible()
        expect(self.active_checkbox).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        expect(self.update_button).to_be_visible()
