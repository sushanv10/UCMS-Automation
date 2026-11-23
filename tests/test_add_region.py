"""
Add Region automation (TC_NETWORK_EXPLORER_CATALOG_ADD_REGION_###).

* Tests that CREATE a region use a unique name (unique(base name from the
  test data)), so re-running the suite never collides with earlier runs.
* Tests that only type a name and then close/cancel/fail use the scenario's
  name as it is - nothing is created.
* All test data lives in test_data/add_region_test_data.py.
"""
import re
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, expect

from modals.add_region_modal import AddRegionModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import add_region_test_data as td
from utils.helpers import unique

pytestmark = pytest.mark.add_region


# ---------------------------------------------------------------------------
# Shared context and setup helper
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    """Shared objects and test data available to each Add Region test."""
    page: Page
    explorer: NetworkExplorerPage
    add: AddRegionModal


def _prepare(
    page: Page,
    credentials: tuple[str, str],
    *,
    open_add_region: bool = True,
) -> Ctx:
    """
    Log in and open the Coverage panel.

    By default, also open the Add Region modal. Set open_add_region=False
    for tests that need the Coverage panel without opening the modal first.
    """
    login_page = LoginPage(page)
    explorer = NetworkExplorerPage(page)
    add = AddRegionModal(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()
    add.verify_region_tree_loaded()

    if open_add_region:
        add.open()

    return Ctx(
        page=page,
        explorer=explorer,
        add=add,
    )


# ---------------------------------------------------------------------------
# TC_ADDREGION_001: Modal opens correctly
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_001_modal_opens_correctly(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.verify_modal_open()
    expect(ctx.add.region_name_input).to_be_visible()
    ctx.add.verify_region_name_value("")
    expect(ctx.add.map_container).to_be_visible()
    expect(ctx.add.submit_button).to_be_visible()
    expect(ctx.add.cancel_button).to_be_visible()


# ---------------------------------------------------------------------------
# TC_ADDREGION_002: Modal title displays correctly
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_002_modal_title_displays_correctly(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.add.modal_heading).to_have_text(td.MODAL_TITLE)


# ---------------------------------------------------------------------------
# TC_ADDREGION_003: 'Close' (X) icon closes modal without saving
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_003_close_icon_closes_without_saving(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(td.REGION_NAME_CLOSE_ICON_TEST)
    ctx.add.close_via_x()

    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(td.REGION_NAME_CLOSE_ICON_TEST)).to_have_count(0)

    # Reopening should show a blank form (no data retained).
    ctx.add.open()
    ctx.add.verify_region_name_value("")


# ---------------------------------------------------------------------------
# TC_ADDREGION_004: Modal is dismissible via Escape key
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_004_escape_key_closes_modal(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.page.keyboard.press("Escape")

    ctx.add.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_ADDREGION_005: Cancel discards all entered data
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_005_cancel_discards_entered_data(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(td.REGION_NAME_CANCEL_TEST)
    ctx.add.draw_coverage_polygon()
    ctx.add.cancel()

    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(td.REGION_NAME_CANCEL_TEST)).to_have_count(0)

    # Reopening 'Add region' shows a blank form.
    ctx.add.open()
    ctx.add.verify_region_name_value("")


# ---------------------------------------------------------------------------
# TC_ADDREGION_006: Block submission when Region Name is empty
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_006_block_submission_empty_region_name(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.submit()

    ctx.add.verify_modal_open()  # must NOT close on a failed submission
    expect(ctx.add.region_name_required_error).to_be_visible()


# ---------------------------------------------------------------------------
# TC_ADDREGION_007: Block submission when Region Name is whitespace only
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_007_block_submission_whitespace_only(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(td.WHITESPACE_ONLY_REGION_NAME)
    ctx.add.submit()

    ctx.add.verify_modal_open()
    expect(ctx.add.region_name_required_error).to_be_visible()


# ---------------------------------------------------------------------------
# TC_ADDREGION_008: Region Name accepts the maximum allowed length
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_008_region_name_accepts_max_length(page, credentials):
    region_name = td.long_name(td.MAX_REGION_NAME_LENGTH, td.MAX_LENGTH_FILLER)
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(region_name)
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(region_name)).to_be_visible()


# ---------------------------------------------------------------------------
# TC_ADDREGION_009: Region Name exceeding maximum length is rejected/blocked
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_009_region_name_exceeding_max_length_rejected(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(td.OVER_MAX_LENGTH_REGION_NAME)

    if len(ctx.add.region_name_input.input_value()) > td.MAX_REGION_NAME_LENGTH:
        ctx.add.submit()
        ctx.add.verify_modal_open()
        expect(ctx.add.name_too_long_error).to_be_visible()
    else:
        # The field stopped accepting characters at the limit - also acceptable.
        assert len(ctx.add.region_name_input.input_value()) == td.MAX_REGION_NAME_LENGTH


# ---------------------------------------------------------------------------
# TC_ADDREGION_010: Region Name sanitized against script injection
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_010_region_name_sanitized_against_injection(page, credentials):
    payload = unique(td.SCRIPT_INJECTION_PAYLOAD)
    dialogs: list[str] = []
    ctx.page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))

    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(payload)
    ctx.add.submit()

    assert not dialogs, "A JavaScript dialog was triggered - the payload was executed."

    ctx.add.verify_modal_closed()
    # The payload is displayed as plain text in the region tree.
    expect(ctx.add.region_tree_node(payload)).to_be_visible(timeout=15000)
    # No script element was injected.
    expect(
        ctx.page.locator("script", has_text=td.SCRIPT_PAYLOAD_TEXT)
    ).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_ADDREGION_011: Region Name accepts a minimum single-character value
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_011_region_name_accepts_single_character(page, credentials):
    ctx = _prepare(page, credentials)

    # A one-character name cannot carry a unique suffix, so check that exactly
    # one more region with this name appears after saving.
    node = ctx.add.region_tree_node(td.SINGLE_CHARACTER_REGION_NAME)
    count_before = node.count()

    ctx.add.fill_region_name(td.SINGLE_CHARACTER_REGION_NAME)
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    expect(node).to_have_count(count_before + 1)


# ---------------------------------------------------------------------------
# TC_ADDREGION_012: Placeholder text displays and disappears correctly
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_012_placeholder_displays_and_disappears(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.add.region_name_input).to_have_attribute(
        "placeholder", td.REGION_NAME_PLACEHOLDER
    )
    expect(ctx.add.region_name_input).to_have_value("")

    ctx.add.fill_region_name(td.PLACEHOLDER_TYPED_CHAR)

    expect(ctx.add.region_name_input).to_have_value(td.PLACEHOLDER_TYPED_CHAR)


# ---------------------------------------------------------------------------
# TC_ADDREGION_013: Leading/trailing spaces are trimmed from Region Name
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_013_leading_trailing_spaces_trimmed(page, credentials):
    trimmed_name = unique(td.TRIMMED_REGION_NAME)
    untrimmed_name = f"{td.LEADING_TRAILING_SPACES}{trimmed_name}{td.LEADING_TRAILING_SPACES}"
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(untrimmed_name)
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    # Exactly one region, listed under the trimmed name.
    expect(ctx.add.region_tree_node(trimmed_name)).to_have_count(1)


# ---------------------------------------------------------------------------
# TC_ADDREGION_014: Validation error auto-clears once a valid value is entered
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_014_validation_error_auto_clears(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.submit()
    expect(ctx.add.region_name_required_error).to_be_visible()

    ctx.add.fill_region_name(td.REGION_NAME_VALID_AFTER_ERROR)

    expect(ctx.add.region_name_required_error).to_be_hidden()


# ---------------------------------------------------------------------------
# TC_ADDREGION_015: Required-field asterisk is displayed for Region Name
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_015_required_field_asterisk_displayed(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.add.region_name_label).to_contain_text(td.REQUIRED_ASTERISK)


# ---------------------------------------------------------------------------
# TC_ADDREGION_016: New region appears in hierarchy without a page refresh
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_016_new_region_appears_without_refresh(page, credentials):
    region_name = unique(td.REGION_NAME_NO_REFRESH_TEST)
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(region_name)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(region_name)).to_be_visible(timeout=5000)


# ---------------------------------------------------------------------------
# TC_ADDREGION_017: Success notification is displayed after creation
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_017_success_notification_displayed_on_creation(page, credentials):
    region_name = unique(td.REGION_NAME_NOTIFICATION_TEST)
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(region_name)
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    expect(ctx.add.success_toast).to_be_visible(timeout=5000)
    expect(ctx.add.region_tree_node(region_name)).to_be_visible()


# ---------------------------------------------------------------------------
# TC_ADDREGION_018: Server/network failure shows a clear error and retains input
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_018_server_failure_shows_error_retains_input(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(td.REGION_NAME_OFFLINE_TEST)
    ctx.add.draw_coverage_polygon()

    # Simulate a failure of the create-region request only: the same URL is
    # also used with GET to list regions, so only the POST is aborted.
    def _abort_create_only(route):
        if route.request.method == "POST":
            route.abort()
        else:
            route.continue_()

    ctx.page.route(re.compile(td.CREATE_REGION_API_ROUTE_PATTERN), _abort_create_only)

    ctx.add.submit()

    ctx.add.verify_modal_open()
    expect(ctx.add.server_unreachable_error_toast).to_be_visible(timeout=5000)
    ctx.add.verify_region_name_value(td.REGION_NAME_OFFLINE_TEST)
    expect(ctx.add.region_tree_node(td.REGION_NAME_OFFLINE_TEST)).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_ADDREGION_019: Duplicate Region Name is not blocked (as per flexibility)
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_019_duplicate_region_name_is_allowed(page, credentials):
    region_name = unique(td.REGION_NAME_DUPLICATE_TEST)
    ctx = _prepare(page, credentials)

    # Precondition: a region with this name exists (created here).
    ctx.add.fill_region_name(region_name)
    ctx.add.submit()
    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(region_name)).to_have_count(1)

    # Add a second region with the same name.
    ctx.add.open()
    ctx.add.fill_region_name(region_name)
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(region_name)).to_have_count(2)


# ---------------------------------------------------------------------------
# TC_ADDREGION_020: Rapid double-submission does not create duplicate regions
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_020_rapid_double_submission_no_duplicates(page, credentials):
    region_name = unique(td.REGION_NAME_DOUBLE_CLICK_TEST)
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(region_name)
    ctx.add.draw_coverage_polygon()

    ctx.add.submit_button.click()
    try:
        ctx.add.submit_button.click(timeout=1000)
    except Exception:
        pass  # Expected if the modal already closed / the button is disabled.

    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(region_name)).to_have_count(1)


# ---------------------------------------------------------------------------
# TC_ADDREGION_021: Add Region handled correctly after clearing session data
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_021_handles_cleared_session_data(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(td.REGION_NAME_SESSION_CLEARED_TEST)
    ctx.add.draw_coverage_polygon()

    ctx.explorer.clear_session_data()
    ctx.add.submit()

    expect(ctx.add.unauthenticated_error_toast).to_be_visible()
    expect(ctx.add.region_tree_node(td.REGION_NAME_SESSION_CLEARED_TEST)).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_ADDREGION_022: Focus is set to Region Name automatically on modal open
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_022_focus_set_to_region_name_on_open(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.add.region_name_input).to_be_focused()


# ---------------------------------------------------------------------------
# TC_ADDREGION_023: Tab order moves logically through the modal
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_023_tab_order_moves_logically(page, credentials):
    ctx = _prepare(page, credentials)

    # Click inside the Region Name field to start keyboard navigation.
    ctx.add.region_name_input.click()

    ctx.page.keyboard.press("Tab")

    # Region Name -> Zoom In
    ctx.page.keyboard.press("Tab")
    expect(ctx.add.leaflet_zoom_in_button).to_be_focused()

    # Zoom In -> Zoom Out
    ctx.page.keyboard.press("Tab")
    expect(ctx.add.leaflet_zoom_out_button).to_be_focused()

    # Zoom Out -> remaining map controls
    ctx.page.keyboard.press("Tab")
    ctx.page.keyboard.press("Tab")
    ctx.page.keyboard.press("Tab")

    # Map controls -> Cancel
    ctx.page.keyboard.press("Tab")
    expect(ctx.add.cancel_button).to_be_focused()

    # Cancel -> Add Region
    ctx.page.keyboard.press("Tab")
    expect(ctx.add.submit_button).to_be_focused()


# ---------------------------------------------------------------------------
# TC_ADDREGION_024: Add Region button shows a loading state and is disabled
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_024_submit_button_loading_state(page, credentials):
    region_name = unique(td.REGION_NAME_LOADING_STATE_TEST)
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(region_name)
    ctx.add.draw_coverage_polygon()

    # Delay only the create-region POST request.
    def _delay_create_only(route):
        if route.request.method == "POST":
            ctx.page.wait_for_timeout(td.LOADING_DELAY_MS)
        route.continue_()

    ctx.page.route(re.compile(td.CREATE_REGION_API_ROUTE_PATTERN), _delay_create_only)

    ctx.add.submit()

    expect(ctx.add.submit_button).to_be_disabled(timeout=5000)
    expect(ctx.add.submit_button).to_contain_text(td.LOADING_TEXT, timeout=5000)

    # The request completes and the region is created once.
    ctx.add.verify_modal_closed()
    expect(ctx.add.region_tree_node(region_name)).to_have_count(1)


# ---------------------------------------------------------------------------
# TC_ADDREGION_025: End-to-end successful region creation
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_025_end_to_end_successful_creation(page, credentials):
    region_name = unique(td.REGION_NAME_END_TO_END_TEST)
    ctx = _prepare(page, credentials)

    ctx.add.fill_region_name(region_name)
    ctx.add.submit()

    ctx.add.verify_modal_closed()
    expect(ctx.add.success_toast).to_be_visible(timeout=5000)
    expect(ctx.add.region_tree_node(region_name)).to_be_visible(timeout=5000)


# ---------------------------------------------------------------------------
# TC_ADDREGION_026: Unauthorized user cannot add a region
# ---------------------------------------------------------------------------
def test_TC_ADDREGION_026_unauthorized_user_cannot_add_region(page, restricted_credentials):
    region_name = unique(td.REGION_NAME_UNAUTHORIZED_TEST)
    ctx = _prepare(page, restricted_credentials, open_add_region=False)

    trigger = ctx.add.add_region_trigger_button
    if trigger.count() == 0 or not trigger.is_visible() or trigger.is_disabled():
        # The action is not available to this user - creation is prevented.
        expect(ctx.add.region_tree_node(region_name)).to_have_count(0)
        return

    # The button is available: the request itself must be rejected.
    ctx.add.open()
    ctx.add.fill_region_name(region_name)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()

    expect(ctx.add.permission_error).to_be_visible(timeout=5000)
    ctx.add.verify_modal_open()
    expect(ctx.add.region_tree_node(region_name)).to_have_count(0)
