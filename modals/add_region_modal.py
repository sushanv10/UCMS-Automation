import re

from playwright.sync_api import Page, Locator, expect
from test_data import add_region_test_data as td


class AddRegionModal:

    def __init__(self, page: Page):
        self.page = page

        # -----------------------------------------------------------
        # Trigger - lives on the Coverage panel, opens this modal.
        # -----------------------------------------------------------
        self.add_region_trigger_button = page.get_by_role("button", name="Add region")

        # -----------------------------------------------------------
        # Modal chrome - CONFIRMED
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close")

        # -----------------------------------------------------------
        # Region Name field - CONFIRMED
        # -----------------------------------------------------------
        self.region_name_label = page.get_by_text("Region Name")
        self.region_name_input = page.get_by_placeholder(td.REGION_NAME_PLACEHOLDER)

        # -----------------------------------------------------------
        # Actions - CONFIRMED
        # (submit button needs exact=True: the trigger button is also
        # named "Add region", just lowercase "r")
        # -----------------------------------------------------------
        self.submit_button = page.locator('button[type="submit"]')
        self.cancel_button = page.get_by_role("button", name="Cancel")

        self.leaflet_zoom_in_button = page.locator(
            "a.leaflet-control-zoom-in"
        )
        self.leaflet_zoom_out_button = page.locator(
            "a.leaflet-control-zoom-out"
        )

        # -----------------------------------------------------------
        # Field validation errors - message text CONFIRMED, exact DOM
        # location still a best-effort guess (plain text node lookup).
        # -----------------------------------------------------------
        self.region_name_required_error = page.get_by_text(
            re.compile(re.escape(td.REGION_NAME_REQUIRED), re.IGNORECASE)
        )
        # "Already exists" is a fragment, not necessarily the full message
        # (e.g. could render as "Region name already exists") - kept as a
        # case-insensitive substring match rather than exact=True.
        self.duplicate_name_error = page.get_by_text(
            re.compile(re.escape(td.REGION_NAME_DUPLICATE), re.IGNORECASE)
        )
        
        self.name_too_long_error = (
            page.get_by_role("alert")
            .filter(has_text=td.REGION_NAME_TOO_LONG)
        )

        # -----------------------------------------------------------
        # Submission notifications - message text CONFIRMED.
        # TODO: confirm the actual toast/banner container role - these
        # currently just locate the message text itself, which is usually
        # enough, but wrap in a role="status"/role="alert" container lookup
        # if the app needs that for visibility timing / a11y assertions.
        # -----------------------------------------------------------
        self.success_toast = page.get_by_text(td.REGION_ADDED_SUCCESS_PATTERN)

        # Shown when the create-region request fails due to an expired/
        # cleared session (401 Unauthenticated) - used by the
        # cleared-session test (TC_ADDREGION_022).
        self.unauthenticated_error_toast = page.get_by_text(
            td.NETWORK_ERROR_PATTERN, exact=True
        )
        # Shown when the create-region request fails due to a network/server
        # issue (offline, 5xx, aborted request) - used by the server-failure
        # test (TC_ADDREGION_020).
        self.server_unreachable_error_toast = page.get_by_text(
            td.SESSION_ERROR_PATTERN, exact=True
        )
        # Generic fallback for any test that just needs "an error showed up"
        # without pinning the exact wording yet.
        self.error_toast = page.get_by_role("alert")

        # -----------------------------------------------------------
        # Hierarchy tree - CONFIRMED heading; row text format confirmed.
        # -----------------------------------------------------------
        self.hierarchy_heading = page.get_by_role("heading", name="Hierarchy")
        self._page = page

    def region_tree_node(self, region_name: str) -> Locator:
        pattern = re.compile(rf"^Region:\s+\S+\s+-\s+{re.escape(region_name)}$")
        return self._page.get_by_text(pattern, exact=True)

    def verify_hierarchy_panel_open(self):
        expect(self.hierarchy_heading).to_be_visible()

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

    def verify_region_name_value(self, expected: str):
        expect(self.region_name_input).to_have_value(expected)

    def verify_submit_disabled(self):
        expect(self.submit_button).to_be_disabled()

    def verify_submit_enabled(self):
        expect(self.submit_button).to_be_enabled()