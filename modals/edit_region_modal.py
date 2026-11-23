import re

from playwright.sync_api import Page, Locator, expect

from test_data import edit_region_test_data as td

# Describes the focused element (used for the Tab-order check).
_FOCUS_JS = """
() => {
    const el = document.activeElement;
    if (!el) return "";
    return [el.tagName, el.type || "", el.id || "", el.title || "",
            (el.textContent || "").trim().slice(0, 30)].join("|");
}
"""


class EditRegionModal:
    """
    Page Object for the Catalog - Edit Region modal.

    Opened from Region Details via the Edit button
    (see RegionDetailsModal.click_edit).
    """

    def __init__(self, page: Page):
        self.page = page
        self._page = page

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close").last

        # -----------------------------------------------------------
        # Region Name field - CONFIRMED via Playwright codegen
        # -----------------------------------------------------------
        self.region_name_label = page.get_by_text("Region Name").first
        self.region_name_input = page.get_by_label("Region Name")

        # -----------------------------------------------------------
        # Coverage area
        # -----------------------------------------------------------
        self.map_container = page.locator(".leaflet-container").last
        self.leaflet_zoom_in_button = page.locator("a.leaflet-control-zoom-in").last
        self.leaflet_zoom_out_button = page.locator("a.leaflet-control-zoom-out").last
        self.expand_map_button = page.locator("button[title='Fullscreen'] svg")
        self.map_helper_text = page.get_by_text(td.MAP_HELPER_TEXT)
        self.map_caption = page.get_by_text(td.MAP_CAPTION_TEXT)

        # -----------------------------------------------------------
        # Actions - CONFIRMED via Playwright codegen
        # (the save button text changes to "Please wait..." while loading)
        # -----------------------------------------------------------
        self.save_changes_button = page.get_by_role(
            "button",
            name=re.compile(rf"^({td.SAVE_BUTTON_LABEL}|{td.LOADING_BUTTON_TEXT})", re.IGNORECASE),
        )
        self.cancel_button = page.get_by_role("button", name=td.CANCEL_BUTTON_LABEL)

        # -----------------------------------------------------------
        # Field validation errors (inside role="alert" so that region names
        # such as 'Edit_Region_Duplicate_Test' in the tree are never matched)
        # -----------------------------------------------------------
        self.region_name_required_error = page.get_by_text(
            re.compile(re.escape(td.REGION_NAME_REQUIRED), re.IGNORECASE)
        ).first
        self.duplicate_name_error = page.get_by_role("alert").filter(
            has_text=td.DUPLICATE_PATTERN
        ).first
        self.name_too_long_error = page.get_by_role("alert").filter(
            has_text=td.REGION_NAME_TOO_LONG
        ).first
        self.validation_alert = page.get_by_role("alert").first

        # -----------------------------------------------------------
        # Notifications
        # -----------------------------------------------------------
        self.success_toast = page.get_by_text(td.REGION_UPDATED_SUCCESS_PATTERN).first
        self.unauthenticated_error_toast = page.get_by_text(
            td.UNAUTHENTICATED_MESSAGE, exact=True
        )
        self.server_unreachable_error_toast = page.get_by_text(
            td.SERVER_UNREACHABLE_MESSAGE, exact=True
        )
        self.permission_error = page.get_by_text(td.PERMISSION_PATTERN).first
        self.error_notification = self.server_unreachable_error_toast.or_(
            self.validation_alert
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
    def fill_region_name(self, name: str):
        expect(self.region_name_input).to_be_visible()
        self.region_name_input.fill(name)

    def clear_region_name(self):
        self.region_name_input.fill("")

    def type_at_end(self, text: str):
        """Type after the existing Region Name (the caret is not at the end by default)."""
        expect(self.region_name_input).to_be_visible()
        self.region_name_input.click()
        self.region_name_input.press("End")
        self.region_name_input.press_sequentially(text)

    def paste_into_region_name(self, text: str):
        """Copy `text` to the clipboard, select all in the field and paste with Ctrl+V."""
        self.page.context.grant_permissions(["clipboard-read", "clipboard-write"])
        self.page.evaluate("(value) => navigator.clipboard.writeText(value)", text)
        self.region_name_input.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Control+V")

    def press_enter_on_name(self):
        self.region_name_input.press("Enter")

    def save(self):
        expect(self.save_changes_button).to_be_visible()
        self.save_changes_button.click()

    def focus_order(self, max_steps: int = 15) -> list[str]:
        """Start in Region Name, press Tab repeatedly, return the order of the known controls."""
        known = {
            "name": self.region_name_input,
            "zoom_in": self.leaflet_zoom_in_button,
            "zoom_out": self.leaflet_zoom_out_button,
            "cancel": self.cancel_button,
            "save": self.save_changes_button,
        }
        self.region_name_input.focus()
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

    def submit_outcome(self, attempts: int = 20) -> str:
        """After clicking Save: 'saved' (modal closed), 'error' (an alert) or 'timeout'."""
        for _ in range(attempts):
            if not self.modal_heading.is_visible():
                return "saved"
            if self.validation_alert.is_visible():
                return "error"
            self.page.wait_for_timeout(500)
        return "timeout"

    # =================================================================
    # Assertions
    # =================================================================
    def verify_region_name_value(self, expected: str):
        expect(self.region_name_input).to_have_value(expected)

    def verify_save_enabled(self):
        expect(self.save_changes_button).to_be_enabled()

    def verify_save_disabled(self):
        expect(self.save_changes_button).to_be_disabled()

    def verify_elements_visible(self):
        """Every element listed in TC_003 - reports ALL missing ones by name."""
        elements = {
            "heading": self.modal_heading,
            "close icon": self.close_button,
            "Region Name label": self.region_name_label,
            "Region Name input": self.region_name_input,
            "map": self.map_container,
            "zoom in": self.leaflet_zoom_in_button,
            "zoom out": self.leaflet_zoom_out_button,
            "expand icon": self.expand_map_button,
            "map helper text": self.map_helper_text,
            "map caption": self.map_caption,
            "Cancel button": self.cancel_button,
            "Save Changes button": self.save_changes_button,
        }
        missing = []
        for name, locator in elements.items():
            try:
                expect(locator).to_be_visible(timeout=3000)
            except AssertionError:
                missing.append(name)
        assert not missing, f"Not visible in the Edit Region modal: {missing}"