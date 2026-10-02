import re

import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from modals.add_region_modal import AddRegionModal
from test_data import add_region_test_data as td


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------
def _login_and_open_add_region(
    page: Page, credentials: tuple[str, str]
) -> tuple[NetworkExplorerPage, AddRegionModal]:
    """Log in, open the Coverage panel, and open the Add Region modal."""
    login_page = LoginPage(page)
    explorer = NetworkExplorerPage(page)
    modal = AddRegionModal(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()

    modal.open()
    return explorer, modal


# ---------------------------------------------------------------------------
# TC_ADDREGION_001: Modal opens correctly
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_001_modal_opens_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)

    modal.verify_modal_open()
    expect(modal.region_name_input).to_be_visible()
    expect(modal.submit_button).to_be_visible()
    expect(modal.cancel_button).to_be_visible() 

# ---------------------------------------------------------------------------
# TC_ADDREGION_002: Modal title displays correctly
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_002_modal_title_displays_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    expect(modal.modal_heading).to_have_text(td.MODAL_TITLE)

# ---------------------------------------------------------------------------
# TC_ADDREGION_003: 'Close' (X) icon closes modal without saving
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_003_close_icon_closes_without_saving(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.REGION_NAME_CLOSE_ICON_TEST)
    modal.close_via_x()
 
    modal.verify_modal_closed()
 
    # Reopening should show a blank form (no data retained).
    modal.open()
    modal.verify_region_name_value("") 

# ---------------------------------------------------------------------------
# TC_ADDREGION_004: Modal is dismissible via Escape key
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_004_escape_key_closes_modal(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.REGION_NAME_ESC_TEST)
    page.keyboard.press("Escape")
 
    modal.verify_modal_closed() 

# ---------------------------------------------------------------------------
# TC_ADDREGION_005: Cancel discards all entered data
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_005_cancel_discards_entered_data(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.REGION_NAME_CANCEL_TEST)
    modal.cancel()
 
    modal.verify_modal_closed()
 
    expect(modal.region_tree_node(td.REGION_NAME_CANCEL_TEST)).to_have_count(0)

# ---------------------------------------------------------------------------
# TC_ADDREGION_006: Block submission when Region Name is empty
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_006_block_submission_empty_region_name(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.submit()
 
    modal.verify_modal_open()  # should NOT close on a failed submission
  
    expect(modal.region_name_required_error).to_be_visible()

# ---------------------------------------------------------------------------
# TC_ADDREGION_007: Block submission when Region Name is whitespace only
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_007_block_submission_whitespace_only(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.WHITESPACE_ONLY_REGION_NAME)
    modal.submit()
 
    modal.verify_modal_open()
    expect(modal.region_name_required_error).to_be_visible()

# ---------------------------------------------------------------------------
# TC_ADDREGION_008: Region Name accepts the maximum allowed length
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_008_region_name_accepts_max_length(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.MAX_LENGTH_REGION_NAME)
    modal.submit()
 
    modal.verify_modal_closed()
    expect(modal.region_tree_node(td.MAX_LENGTH_REGION_NAME)).to_be_visible() 

# ---------------------------------------------------------------------------
# TC_ADDREGION_009: Region Name exceeding maximum length is rejected/blocked
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_009_region_name_exceeding_max_length_rejected(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)

    # Enter a region name exceeding the maximum allowed length.
    modal.fill_region_name(td.OVER_MAX_LENGTH_REGION_NAME)

    # Verify the field accepts the complete input.
    actual_value = modal.region_name_input.input_value()

    assert actual_value == td.OVER_MAX_LENGTH_REGION_NAME

    # Submit the form.
    modal.submit()

    # The modal should remain open because the input is invalid.
    modal.verify_modal_open()

    # Verify the maximum-length validation message.
    expect(
        modal.name_too_long_error
    ).to_be_visible()

# ---------------------------------------------------------------------------
# TC_ADDREGION_010: Region Name sanitized against script/SQL injection
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_010_region_name_sanitized_against_injection(
    page: Page,
    credentials: tuple[str, str],
):
    payload = td.SCRIPT_INJECTION_PAYLOAD

    dialogs: list[str] = []

    page.on(
        "dialog",
        lambda dialog: (
            dialogs.append(dialog.message),
            dialog.dismiss(),
        ),
    )

    _, modal = _login_and_open_add_region(
        page,
        credentials,
    )

    # Enter malicious script payload.
    modal.fill_region_name(payload)

    # Submit the region.
    modal.submit()

    # No JavaScript dialog should be triggered.
    assert not dialogs, (
        "A JavaScript dialog was triggered. "
        "The script injection payload was executed."
    )

    # Region should be successfully created.
    modal.verify_modal_closed()

    # Payload should be rendered as plain text in the region tree.
    tree_node = modal.region_tree_node(payload)

    expect(tree_node).to_be_visible(
        timeout=15000,
    )

    # No script element should have been injected.
    expect(
        page.locator(
            "script",
            has_text="alert(1)",
        )
    ).to_have_count(0)

# ---------------------------------------------------------------------------
# TC_ADDREGION_011: Region Name accepts a minimum single-character value
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_011_region_name_accepts_single_character(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.SINGLE_CHARACTER_REGION_NAME)
    modal.submit()
 
    modal.verify_modal_closed()
    expect(modal.region_tree_node(td.SINGLE_CHARACTER_REGION_NAME)).to_be_visible() 

# ---------------------------------------------------------------------------
# TC_ADDREGION_012: Placeholder text displays and disappears correctly
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_012_placeholder_displays_and_disappears(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    expect(modal.region_name_input).to_have_attribute("placeholder", td.REGION_NAME_PLACEHOLDER)
    expect(modal.region_name_input).to_have_value("")
 
    modal.fill_region_name("H")
 
    expect(modal.region_name_input).to_have_value("H")

# ---------------------------------------------------------------------------
# TC_ADDREGION_013: Leading/trailing spaces are trimmed from Region Name
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_013_leading_trailing_spaces_trimmed(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.UNTRIMMED_REGION_NAME)
    modal.submit()
 
    modal.verify_modal_closed()
    expect(modal.region_tree_node(td.TRIMMED_REGION_NAME)).to_be_visible()
    expect(modal.region_tree_node(td.UNTRIMMED_REGION_NAME)).to_have_count(0) 

# ---------------------------------------------------------------------------
# TC_ADDREGION_014: Validation error auto-clears once a valid value is entered
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_014_validation_error_auto_clears(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.submit()
    expect(modal.region_name_required_error).to_be_visible()
 
    modal.fill_region_name(td.REGION_NAME_VALID_GENERIC)
 
    expect(modal.region_name_required_error).to_be_hidden() 

# ---------------------------------------------------------------------------
# TC_ADDREGION_015: Required-field asterisk is displayed for Region Name
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_015_required_field_asterisk_displayed(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    expect(modal.region_name_label).to_contain_text("*") 

# ---------------------------------------------------------------------------
# TC_ADDREGION_016: New region appears in hierarchy without a page refresh
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_016_new_region_appears_without_refresh(
    page: Page,
    credentials: tuple[str, str],
):
    region_name = td.REGION_NAME_NO_REFRESH_TEST
 
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(region_name)
    modal.submit()
 
    modal.verify_modal_closed()
    expect(modal.region_tree_node(region_name)).to_be_visible(timeout=5000) 

# ---------------------------------------------------------------------------
# TC_ADDREGION_017: Success/error notification is displayed after creation
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_017_success_notification_displayed_on_creation(
    page: Page,
    credentials: tuple[str, str],
):
    # NOTE: the equivalent Add Network test (TC_ADDNETWORK_037) FAILED in
    # UAT - no success confirmation was shown after creation. Included here
    # as a regression check for Add Region; expect this may also fail until
    # fixed.
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.REGION_NAME_NOTIFICATION_TEST)
    modal.submit()
 
    # Message text is confirmed (REGION_ADDED_SUCCESS_PATTERN); the
    # surrounding toast/banner DOM structure is still a guess - see the
    # TODO on AddRegionModal.success_toast.
    expect(modal.success_toast).to_be_visible(timeout=5000)

# ---------------------------------------------------------------------------
# TC_ADDREGION_018: Server/network failure shows a clear error and retains input
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_018_server_failure_shows_error_retains_input(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(td.REGION_NAME_OFFLINE_TEST)
 
    # Simulate a backend/network failure for the create-region request only.
    # NOTE: /api/map/regions is also used via GET to list regions, so the
    # handler must only abort the POST (create) call.
    def _abort_create_only(route):
        if route.request.method == "POST":
            route.abort()
        else:
            route.continue_()
 
    page.route(re.compile(td.CREATE_REGION_API_ROUTE_PATTERN), _abort_create_only)
 
    modal.submit()
 
    modal.verify_modal_open()
   
    expect(modal.server_unreachable_error_toast).to_be_visible(timeout=5000)
    modal.verify_region_name_value(td.REGION_NAME_OFFLINE_TEST) 

# ---------------------------------------------------------------------------
# TC_ADDREGION_019: Block duplicate Region Name
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_019_block_duplicate_region_name(
    page: Page,
    credentials: tuple[str, str],
    existing_region_name: str,  
    
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(existing_region_name)
    modal.submit()
 
    modal.verify_modal_open()
    expect(modal.duplicate_name_error).to_be_visible() 
    expect(modal.region_tree_node(existing_region_name)).to_have_count(1)

# ---------------------------------------------------------------------------
# TC_ADDREGION_020: Rapid double-submission does not create duplicate regions
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_020_rapid_double_submission_no_duplicates(
    page: Page,
    credentials: tuple[str, str],
):
    region_name = td.REGION_NAME_DOUBLE_CLICK_TEST
 
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(region_name)
 
    modal.submit_button.click()
    try:
        modal.submit_button.click(timeout=1000)
    except Exception:
        pass  # Expected if the modal already closed / button disabled.
 
    modal.verify_modal_closed()
    expect(modal.region_tree_node(region_name)).to_have_count(1)

# ---------------------------------------------------------------------------
# TC_ADDREGION_021: Add Region handled correctly after clearing session data
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_021_handles_cleared_session_data(
    page: Page,
    credentials: tuple[str, str],
):
    explorer, modal = _login_and_open_add_region(page, credentials)

    modal.fill_region_name(td.REGION_NAME_SESSION_CLEARED_TEST)

    explorer.clear_session_data()

    modal.submit()

    # Unauthenticated message should be displayed
    expect(page.get_by_text(td.NETWORK_ERROR_PATTERN)).to_be_visible() 

# ---------------------------------------------------------------------------
# TC_ADDREGION_022: Focus is set to Region Name automatically on modal open
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_022_focus_set_to_region_name_on_open(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)
 
    expect(modal.region_name_input).to_be_focused()

# ---------------------------------------------------------------------------
# TC_ADDREGION_023: Tab order moves logically through the modal
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_023_tab_order_moves_logically(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_add_region(page, credentials)

    # # Click inside the Region Name field to start keyboard navigation.
    modal.region_name_input.click()

    page.keyboard.press("Tab")

    # Region Name -> Zoom In
    page.keyboard.press("Tab")
    expect(modal.leaflet_zoom_in_button).to_be_focused()

    # Zoom In -> Zoom Out
    page.keyboard.press("Tab")
    expect(modal.leaflet_zoom_out_button).to_be_focused()

    # Zoom Out -> map/Leaflet controls
    page.keyboard.press("Tab")

    # Continue tabbing through the map controls
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")

    # Map controls -> Cancel
    page.keyboard.press("Tab")
    expect(modal.cancel_button).to_be_focused()

    # Cancel -> Add Region
    page.keyboard.press("Tab")
    expect(modal.submit_button).to_be_focused()

# ---------------------------------------------------------------------------
# TC_ADDREGION_024: Add Region button shows a loading state and disables
# ---------------------------------------------------------------------------

@pytest.mark.add_region
def test_TC_ADDREGION_024_submit_button_loading_state(
    page: Page,
    credentials: tuple[str, str],
):
   

    _, modal = _login_and_open_add_region(page, credentials)

    # Enter valid region name
    modal.fill_region_name(td.REGION_NAME_LOADING_STATE_TEST)

    # Delay only the create-region POST request
    def _delay_create_only(route):
        if route.request.method == "POST":
            page.wait_for_timeout(1500)

        route.continue_()

    page.route(
        re.compile(td.CREATE_REGION_API_ROUTE_PATTERN),
        _delay_create_only,
    )

    # Click Add Region
    modal.submit()

    # Verify button is disabled
    expect(
        modal.submit_button
    ).to_be_disabled(
        timeout=5000
    )

    # Verify loading text
    expect(
        modal.submit_button
    ).to_contain_text(
        "Please wait…",
        timeout=5000
    ) 

# ---------------------------------------------------------------------------
# TC_ADDREGION_025: End-to-end successful region creation
# ---------------------------------------------------------------------------
@pytest.mark.add_region
def test_TC_ADDREGION_025_end_to_end_successful_creation(
    page: Page,
    credentials: tuple[str, str],
):
    region_name = td.REGION_NAME_END_TO_END_TEST
 
    _, modal = _login_and_open_add_region(page, credentials)
 
    modal.fill_region_name(region_name)
    modal.submit()
 
    modal.verify_modal_closed()
    expect(modal.region_tree_node(region_name)).to_be_visible(timeout=5000)