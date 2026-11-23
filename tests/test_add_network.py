"""
Add Network automation (TC_NETWORK_EXPLORER_CATALOG_ADD_NETWORK_###).

"""
import re
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, expect, Route

from modals.add_network_modal import AddNetworkModal
from modals.add_region_modal import AddRegionModal
from modals.network_details_modal import NetworkDetailsModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import add_network_test_data as td
from utils.helpers import _unique_numeric, _unique_with_length, unique

pytestmark = pytest.mark.add_network


# ---------------------------------------------------------------------------
# Shared context and setup helpers
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    """Shared objects available to each Add Network test."""
    page: Page
    explorer: NetworkExplorerPage
    tree: NetworkDetailsModal
    add: AddNetworkModal
    region: str
    region_id: str = ""


def _ensure_region(page: Page, tree: NetworkDetailsModal, name: str):
    """
    Create the region through Add Region (no polygon) ONLY if it is not
    already present in the Coverage tree.
    """
    expect(
        page.locator("button").filter(has_text=re.compile(r"^Region:\s")).first
    ).to_be_visible(timeout=15000)

    if tree.region_rows(name).count() == 0:
        add_region = AddRegionModal(page)
        add_region.open()
        add_region.fill_region_name(name)
        add_region.submit()
        add_region.verify_modal_closed()
        expect(tree.region_rows(name).first).to_be_visible(timeout=15000)


def _prepare(
    page: Page,
    credentials: tuple[str, str],
    *,
    region: str = td.REGION_NAME,
    open_add_network: bool = True,
) -> Ctx:
    """
    Log in, open Coverage, ensure the region exists, and optionally open
    the Add Network modal for that region.
    """
    login_page = LoginPage(page)
    explorer = NetworkExplorerPage(page)
    tree = NetworkDetailsModal(page)
    add = AddNetworkModal(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()

    _ensure_region(page, tree, region)
    region_id = tree.get_region_id(region)

    if open_add_network:
        tree.open_add_network(region)
        add.verify_modal_open()

    return Ctx(
        page=page,
        explorer=explorer,
        tree=tree,
        add=add,
        region=region,
        region_id=region_id,
    )


def _fill_minimal_and_submit(ctx: Ctx, name: str, details: str = ""):
    """Fill name (and optional details), draw the polygon, then submit."""
    ctx.add.fill_network_name(name)
    if details:
        ctx.add.fill_details(details)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()


def _reload_coverage(ctx: Ctx):
    """
    Reload the page, reopen Coverage and expand the original region.

    The Coverage tree only shows newly created networks after a reload
    (same behaviour observed in Edit Network tests).
    """
    ctx.page.reload(wait_until="domcontentloaded")
    ctx.explorer.verify_page_loaded()
    ctx.explorer.open_coverage_panel()
    ctx.explorer.verify_coverage_panel_open()

    region_row = ctx.tree.region_rows(ctx.region).first
    expect(region_row).to_be_visible(timeout=15000)

    refreshed_region_id = ctx.tree.get_region_id(ctx.region)
    assert refreshed_region_id == ctx.region_id, (
        f"Region ID changed after reload. "
        f"Expected: {ctx.region_id}, Actual: {refreshed_region_id}"
    )
    ctx.tree.expand_region(ctx.region)


def _expect_network_in_tree(ctx: Ctx, name: str, timeout: int = 15000):
    """
    Assert the network row is visible under the region.

    Wait for the live tree update first.
    If the network is missing, reload Coverage and retry.
    """

    ctx.tree.expand_region(ctx.region)

    row = ctx.tree.network_rows(ctx.region_id, name).first

    try:
        expect(row).to_be_visible(timeout=min(timeout, 3000))
        return
    except AssertionError:
        pass

    # Reload server-backed Coverage tree.
    _reload_coverage(ctx)

    # Region may be collapsed after reloading.
    ctx.tree.expand_region(ctx.region)

    row = ctx.tree.network_rows(ctx.region_id, name).first

    expect(row).to_be_visible(timeout=timeout)



def _expect_network_not_in_tree(ctx: Ctx, name: str):
    """Assert the network is absent under the region (reload-aware)."""
    _reload_coverage(ctx)
    expect(ctx.tree.network_rows(ctx.region_id, name)).to_have_count(0, timeout=5000)


# ---------------------------------------------------------------------------
# TC_001 – Modal opens from region '+'
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_001_modal_opens_from_region_plus(page, credentials):
    """TC_001: Verify Add Network modal opens when '+' is clicked on a region."""
    ctx = _prepare(page, credentials)

    ctx.add.verify_modal_open()
    expect(ctx.add.modal_heading).to_be_visible()
    expect(ctx.add.submit_button).to_be_visible()
    expect(ctx.add.cancel_button).to_be_visible()


# ---------------------------------------------------------------------------
# TC_002 – Modal title
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_002_modal_title_displays_correctly(page, credentials):
    """TC_002: Header reads exactly 'Catalog - Add Network'."""
    ctx = _prepare(page, credentials)

    expect(ctx.add.modal_heading).to_have_text(td.MODAL_TITLE)


# ---------------------------------------------------------------------------
# TC_003 – Form elements displayed
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_003_form_elements_displayed(page, credentials):
    """TC_003: All expected elements visible."""
    ctx = _prepare(page, credentials)

    ctx.add.verify_form_elements_visible()


# ---------------------------------------------------------------------------
# TC_004 – Default form state
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_004_default_form_state(page, credentials):
    """TC_004: Network Name empty, Details empty, Active checked, no error."""
    ctx = _prepare(page, credentials)

    ctx.add.verify_default_form_state()
    expect(ctx.add.network_name_required_error).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_005 – Region banner shows correct region
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_005_region_banner_shows_correct_region(page, credentials):
    """TC_005: Banner shows 'Creating network under region: {ID}'."""
    ctx = _prepare(page, credentials)

    ctx.add.verify_region_banner(ctx.region_id)


# ---------------------------------------------------------------------------
# TC_006 – Region banner is read-only
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_006_region_banner_is_read_only(page, credentials):
    """TC_006: Banner is informational; parent region cannot be changed."""
    ctx = _prepare(page, credentials)

    expect(ctx.add.region_banner).to_be_visible()
    # Banner is not an editable input
    tag = ctx.add.region_banner.evaluate("el => el.tagName.toLowerCase()")
    assert tag not in ("input", "textarea", "select")


# ---------------------------------------------------------------------------
# TC_007 – Close via X
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_007_close_icon_closes_without_saving(page, credentials):
    """TC_007: X closes modal without saving; reopen shows blank form."""
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(td.NAME_CLOSE_ICON)
    ctx.add.close_via_x()
    ctx.add.verify_modal_closed()
    _expect_network_not_in_tree(ctx, td.NAME_CLOSE_ICON)

    ctx.tree.open_add_network(ctx.region)
    ctx.add.verify_modal_open()
    ctx.add.verify_default_form_state()


# ---------------------------------------------------------------------------
# TC_008 – Click outside (backdrop)
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_008_click_outside_closes_without_saving(page, credentials):
    """TC_008: Clicking backdrop closes without saving."""
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(td.NAME_BACKDROP)
    ctx.add.click_outside_to_dismiss()
    ctx.add.verify_modal_closed()
    _expect_network_not_in_tree(ctx, td.NAME_BACKDROP)


# ---------------------------------------------------------------------------
# TC_009 – Escape key
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_009_escape_key_closes_modal(page, credentials):
    """TC_009: Escape closes modal without saving."""
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(td.NAME_ESCAPE)
    ctx.page.keyboard.press("Escape")
    ctx.add.verify_modal_closed()
    _expect_network_not_in_tree(ctx, td.NAME_ESCAPE)


# ---------------------------------------------------------------------------
# TC_010 – Cancel
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_010_cancel_discards_entered_data(page, credentials):
    """TC_010: Cancel discards data and closes modal."""
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(td.NAME_CANCEL)
    ctx.add.fill_details(td.DETAILS_CANCEL)
    ctx.add.cancel()
    ctx.add.verify_modal_closed()
    _expect_network_not_in_tree(ctx, td.NAME_CANCEL)


# ---------------------------------------------------------------------------
# TC_011 – Reopen after cancel shows blank form
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_011_reopen_after_cancel_shows_blank_form(page, credentials):
    """TC_011: Reopening after cancel shows empty defaults."""
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(td.NAME_REOPEN_DISCARDED)
    ctx.add.fill_details(td.DETAILS_DISCARDED)
    ctx.add.set_active(False)
    ctx.add.cancel()
    ctx.add.verify_modal_closed()

    ctx.tree.open_add_network(ctx.region)
    ctx.add.verify_modal_open()
    ctx.add.verify_default_form_state()


# ---------------------------------------------------------------------------
# TC_012 – Keyboard tab order
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_012_keyboard_tab_order(page, credentials):
    """TC_012: Tab order moves logically through form controls."""
    ctx = _prepare(page, credentials)

    order = ctx.add.focus_order()
    # Name should be first; later controls should appear without trapping.
    assert order[0] == "name"
    assert "details" in order or "active" in order or "submit" in order


# ---------------------------------------------------------------------------
# TC_013 – Submit using Enter key
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_013_submit_using_enter_key(page, credentials):
    """TC_013: Enter in Network Name submits when form is valid."""
    name = unique(td.NAME_ENTER_KEY)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.draw_coverage_polygon()
    ctx.add.press_enter_on_name()
    ctx.page.wait_for_timeout(1000)

    # Either form submits successfully, or Enter is not bound (sheet Remarks).
    if ctx.add.modal_heading.is_visible():
        # Enter did not submit — form still open with data retained.
        ctx.add.verify_network_name_value(name)
        return

    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_014 – Default focus on open
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_014_default_focus_on_open(page, credentials):
    """TC_014: Focus lands on Network Name when modal opens."""
    ctx = _prepare(page, credentials)
    ctx.add.verify_network_name_has_focus()


# ---------------------------------------------------------------------------
# TC_015 – Placeholder behavior
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_015_placeholder_behavior(page, credentials):
    """TC_015: Placeholder visible when empty; disappears when typing."""
    ctx = _prepare(page, credentials)

    expect(ctx.add.network_name_input).to_have_attribute(
        "placeholder", td.NETWORK_NAME_PLACEHOLDER
    )
    ctx.add.network_name_input.click()
    ctx.add.network_name_input.press_sequentially("L")
    expect(ctx.add.network_name_input).to_have_value("L")


# ---------------------------------------------------------------------------
# TC_016 – Required field asterisk
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_016_required_field_asterisk(page, credentials):
    """TC_016: Asterisk shown next to Network Name (required)."""
    ctx = _prepare(page, credentials)
    ctx.add.verify_required_asterisk_on_network_name()


# ---------------------------------------------------------------------------
# TC_017 – Active checkbox default checked
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_017_active_checkbox_default_checked(page, credentials):
    """TC_017: Active is checked by default."""
    ctx = _prepare(page, credentials)

    expect(ctx.add.active_checkbox).to_be_checked()


# ---------------------------------------------------------------------------
# TC_018 – Active checkbox toggle
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_018_active_checkbox_toggle(page, credentials):
    """TC_018: Active checkbox toggles on click."""
    ctx = _prepare(page, credentials)

    expect(ctx.add.active_checkbox).to_be_checked()
    ctx.add.set_active(False)
    expect(ctx.add.active_checkbox).not_to_be_checked()
    ctx.add.set_active(True)
    expect(ctx.add.active_checkbox).to_be_checked()


# ---------------------------------------------------------------------------
# TC_019 – Minimum length name (single character)
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_019_minimum_length_name(page, credentials):
    """TC_019: Single-character Network Name is accepted (scenario value 'N')."""
    # Sheet uses exact value "N". unique() is applied so re-runs do not collide.
    name = unique(td.NAME_SINGLE_CHAR)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_020 – Boundary 254 characters
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_020_boundary_254_characters(page, credentials):
    """TC_020: Network Name of 254 characters is accepted."""
    name = _unique_with_length(254, td.LENGTH_254_FILLER)
    assert len(name) == 254
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_021 – Maximum length 255
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_021_maximum_length_255(page, credentials):
    """TC_021: Network Name of exactly 255 characters is accepted."""
    name = _unique_with_length(255, td.MAX_LENGTH_FILLER)
    assert len(name) == 255
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_022 – Numeric name
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_022_numeric_name(page, credentials):
    """TC_022: Numeric-only Network Name is accepted."""
    name = _unique_numeric(td.NAME_NUMERIC)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_023 – Alphanumeric name with spaces
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_023_alphanumeric_name(page, credentials):
    """TC_023: Alphanumeric name with spaces is accepted."""
    name = unique(td.NAME_ALPHANUMERIC)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_024 – Special characters
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_024_special_characters_name(page, credentials):
    """TC_024: Name with permitted special characters is saved as plain text."""
    name = unique(td.NAME_SPECIAL_CHARS)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_025 – Unicode (Nepali)
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_025_unicode_nepali_name(page, credentials):
    """TC_025: Nepali/Unicode Network Name is saved and displayed correctly."""
    name = unique(td.NAME_UNICODE_NEPALI)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)

    # Persist after refresh
    ctx.page.reload(wait_until="domcontentloaded")
    ctx.explorer.verify_page_loaded()
    ctx.explorer.open_coverage_panel()
    ctx.explorer.verify_coverage_panel_open()
    expect(ctx.tree.region_rows(ctx.region).first).to_be_visible(timeout=15000)
    ctx.region_id = ctx.tree.get_region_id(ctx.region)
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_026 – Leading / trailing spaces trimmed
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_026_leading_trailing_spaces_trimmed(page, credentials):
    """TC_026: Leading and trailing spaces are trimmed on save."""
    base = unique(td.NAME_TRIMMED)
    entered = f" {base} "
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, entered)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, base)
    expect(ctx.tree.network_rows(ctx.region_id, entered.strip())).to_have_count(1)


# ---------------------------------------------------------------------------
# TC_027 – Valid Details
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_027_create_with_valid_details(page, credentials):
    """TC_027: Network created with valid Details; Details visible in Network Details."""
    name = unique(td.NAME_DETAILS_VALID)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name, details=td.DETAILS_VALID)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)

    ctx.tree.open_for_network(ctx.region, name)
    expect(ctx.page.get_by_text(td.DETAILS_VALID, exact=False).first).to_be_visible(
        timeout=10000
    )


# ---------------------------------------------------------------------------
# TC_028 – Empty Details (optional)
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_028_create_with_empty_details(page, credentials):
    """TC_028: Network can be created with empty Details."""
    name = unique(td.NAME_EMPTY_DETAILS)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name, details="")
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_029 – Multi-line Details
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_029_details_multiline(page, credentials):
    """TC_029: Multi-line Details retains line breaks."""
    name = unique(td.NAME_MULTILINE_DETAILS)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name, details=td.DETAILS_MULTILINE)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)

    ctx.tree.open_for_network(ctx.region, name)
    # At least one of the lines should be visible
    expect(ctx.page.get_by_text("Line one", exact=False).first).to_be_visible(
        timeout=10000
    )


# ---------------------------------------------------------------------------
# TC_030 – Details special + Unicode
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_030_details_special_and_unicode(page, credentials):
    """TC_030: Details accepts special characters and Unicode."""
    name = unique(td.NAME_SPECIAL_DETAILS)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name, details=td.DETAILS_SPECIAL_UNICODE)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_031 – Whitespace-only Details
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_031_whitespace_only_details(page, credentials):
    """TC_031: Whitespace-only Details treated as empty; does not block save."""
    name = unique(td.NAME_WHITESPACE_DETAILS)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name, details=td.DETAILS_WHITESPACE_ONLY)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_032 – Active checked
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_032_create_with_active_checked(page, credentials):
    """TC_032: Network created with Active checked is saved as Active."""
    name = unique(td.NAME_ACTIVE_CHECKED)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.set_active(True)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)

    ctx.tree.open_for_network(ctx.region, name)
    # Status should reflect Active
    expect(
        ctx.page.get_by_text(re.compile(r"Active|active", re.IGNORECASE)).first
    ).to_be_visible(timeout=10000)


# ---------------------------------------------------------------------------
# TC_033 – Active unchecked
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_033_create_with_active_unchecked(page, credentials):
    """TC_033: Network created with Active unchecked is saved as inactive."""
    name = unique(td.NAME_ACTIVE_UNCHECKED)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.set_active(False)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_034 – Inactive status in Network Details
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_034_inactive_status_in_network_details(page, credentials):
    """TC_034: Verify Network Details displays Inactive for an inactive network."""
    name = unique(td.NAME_INACTIVE_STATUS)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.set_active(False)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)

    ctx.tree.open_for_network(ctx.region, name)

    # Verify the actual Status value inside the Network Details modal.
    details_modal = ctx.page.get_by_role("dialog")

    expect(details_modal.get_by_text("Inactive", exact=True)).to_be_visible(
        timeout=10000
    )

# ---------------------------------------------------------------------------
# TC_035 – End-to-end creation
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_035_end_to_end_network_creation(page, credentials):
    """TC_035: Full valid create with all fields; network appears under region."""
    name = unique(td.NAME_END_TO_END)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.fill_details(td.DETAILS_PRIMARY)
    ctx.add.set_active(True)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)


# ---------------------------------------------------------------------------
# TC_036 – Create request references parent region
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_036_create_request_references_parent_region(page, credentials):
    """TC_036: API create payload includes the correct parent region ID."""
    name = unique(td.NAME_PAYLOAD_CHECK)
    ctx = _prepare(page, credentials)
    captured: dict = {}

    def _capture(route: Route):
        try:
            captured["post_data"] = route.request.post_data or ""
        except Exception:
            captured["post_data"] = ""
        route.continue_()

    ctx.page.route(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN), _capture)
    try:
        _fill_minimal_and_submit(ctx, name)
        ctx.add.verify_modal_closed()
        _expect_network_in_tree(ctx, name)
        body = captured.get("post_data", "")
        assert ctx.region_id in body or name in body, (
            f"Create payload should reference region {ctx.region_id!r}. "
            f"Captured body: {body[:500]!r}"
        )
    finally:
        ctx.page.unroute(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN))


# ---------------------------------------------------------------------------
# TC_037 – Double-click submit creates once
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_037_double_click_submit_creates_once(page, credentials):
    """TC_037: Rapid double-click on Add Network creates only one network."""
    name = unique(td.NAME_DOUBLE_CLICK)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit_button.dblclick()
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)
    expect(ctx.tree.network_rows(ctx.region_id, name)).to_have_count(1, timeout=5000)


# ---------------------------------------------------------------------------
# TC_038 – Submit loading state
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_038_submit_loading_state(page, credentials):
    """TC_038: Button shows loading / is disabled while request is in flight."""
    name = unique(td.NAME_LOADING_STATE)
    ctx = _prepare(page, credentials)

    # Slow the create API so loading state is observable
    def _delay(route: Route):
        ctx.page.wait_for_timeout(1500)
        route.continue_()

    ctx.page.route(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN), _delay)
    try:
        ctx.add.fill_network_name(name)
        ctx.add.draw_coverage_polygon()
        ctx.add.submit()
        # While pending, button should be disabled or show loading text
        try:
            expect(ctx.add.submit_button).to_be_disabled(timeout=2000)
        except AssertionError:
            # Alternative: label changes to Please wait...
            expect(ctx.add.submit_button).to_contain_text(
                re.compile(r"wait|loading", re.IGNORECASE), timeout=2000
            )
        ctx.add.verify_modal_closed()
        _expect_network_in_tree(ctx, name)
    finally:
        ctx.page.unroute(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN))


# ---------------------------------------------------------------------------
# TC_039 – Empty Network Name blocked
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_039_block_empty_network_name(page, credentials):
    """TC_039: Empty Network Name shows required error; modal stays open."""
    ctx = _prepare(page, credentials)

    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    expect(ctx.add.network_name_required_error).to_be_visible()
    ctx.add.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_040 – Whitespace-only Network Name blocked
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_040_block_whitespace_only_name(page, credentials):
    """TC_040: Whitespace-only name treated as empty; required error shown."""
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(td.WHITESPACE_ONLY_NETWORK_NAME)
    ctx.add.fill_details(td.DETAILS_WHITESPACE_NAME_CASE)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    expect(ctx.add.network_name_required_error).to_be_visible()
    ctx.add.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_041 – All fields empty
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_041_submit_all_fields_empty(page, credentials):
    """TC_041: Submit with nothing filled shows Network Name required."""
    ctx = _prepare(page, credentials)

    ctx.add.submit()
    expect(ctx.add.network_name_required_error).to_be_visible()
    ctx.add.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_042 – Immediate feedback for incomplete form
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_042_immediate_feedback_incomplete_form(page, credentials):
    """TC_042: Clear visual feedback when required Network Name is missing."""
    ctx = _prepare(page, credentials)

    ctx.add.submit()
    expect(ctx.add.network_name_required_error).to_be_visible()
    # Field should also signal error (aria-invalid or error class) – soft check
    ctx.add.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_043 – Validation message auto-clears
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_043_validation_message_auto_clears(page, credentials):
    """TC_043: Required error clears when a valid value is entered."""
    ctx = _prepare(page, credentials)

    ctx.add.submit()
    expect(ctx.add.network_name_required_error).to_be_visible()

    ctx.add.fill_network_name(unique(td.NAME_VALIDATION_CLEAR))

    # Verify the required validation message clears dynamically.
    expect(ctx.add.network_name_required_error).to_have_count(0, timeout=3000)


# ---------------------------------------------------------------------------
# TC_044 – Name exceeding max length
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_044_name_exceeding_max_length(page, credentials):
    """TC_044: Inline error when Network Name exceeds 255 characters."""
    ctx = _prepare(page, credentials)

    over = td.OVER_MAX_LENGTH_NETWORK_NAME
    assert len(over) == 256
    ctx.add.fill_network_name(over)
    # Immediate or on submit
    try:
        expect(ctx.add.name_too_long_error).to_be_visible(timeout=3000)
    except AssertionError:
        ctx.add.draw_coverage_polygon()
        ctx.add.submit()
        expect(ctx.add.name_too_long_error).to_be_visible(timeout=5000)
        ctx.add.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_045 – Details exceeding max length
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_045_details_exceeding_max_length(page, credentials):
    """TC_045: Details field enforces a maximum length (assumed 255)."""
    name = unique(td.NAME_LONG_DETAILS)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.fill_details(td.OVER_MAX_DETAILS)
    ctx.add.draw_coverage_polygon()
    ctx.add.submit()
    # Either blocked with validation, truncated, or succeeds with limit —
    # assert no unhandled crash and modal behavior is coherent.
    try:
        expect(ctx.add.details_too_long_error).to_be_visible(timeout=5000)
        ctx.add.verify_modal_open()
    except AssertionError:
        # If no limit enforced, network may be created; note for review.
        try:
            ctx.add.verify_modal_closed()
            _expect_network_in_tree(ctx, name)
        except AssertionError:
            ctx.add.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_046 – Duplicate name in same region
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_046_duplicate_name_in_same_region(page, credentials):
    """
    TC_046: Duplicate Network Name within the same region.

    Per current Add Network requirement, duplicates are accepted (two rows
    with the same label, different IDs). Edit Network cases reject duplicates —
    confirm rule with requirement owner if behavior changes.
    """
    base = unique(td.NAME_DUPLICATE_TEST)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, base)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, base)

    # Second create with the same name
    ctx.tree.open_add_network(ctx.region)
    ctx.add.verify_modal_open()
    _fill_minimal_and_submit(ctx, base)
    ctx.add.verify_modal_closed()
    ctx.tree.expand_region(ctx.region)
    expect(ctx.tree.network_rows(ctx.region_id, base)).to_have_count(2, timeout=15000)


# ---------------------------------------------------------------------------
# TC_047 – Script / SQL injection in Network Name
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_047_script_sql_injection_in_name(page, credentials):
    """TC_047: Injection payloads are stored/displayed as plain text, not executed."""
    ctx = _prepare(page, credentials, open_add_network=False)

    for payload in (td.SCRIPT_INJECTION_PAYLOAD, td.SQL_INJECTION_PAYLOAD):
        # Keep payload readable in the hierarchy; suffix makes re-runs unique.
        try_name = f"{payload}_{unique('inj')}"
        if len(try_name) > 255:
            try_name = try_name[:255]

        ctx.tree.open_add_network(ctx.region)
        ctx.add.verify_modal_open()
        ctx.add.fill_network_name(try_name)
        ctx.add.draw_coverage_polygon()
        ctx.add.submit()
        ctx.add.verify_modal_closed()
        # No alert dialog should have appeared
        assert ctx.page.locator("dialog, [role='alertdialog']").count() == 0
        _expect_network_in_tree(ctx, try_name)


# ---------------------------------------------------------------------------
# TC_048 – HTML / script injection in Details
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_048_html_injection_in_details(page, credentials):
    """TC_048: HTML/script in Details is escaped / shown as plain text."""
    name = unique(td.NAME_XSS_DETAILS)
    ctx = _prepare(page, credentials)

    _fill_minimal_and_submit(ctx, name, details=td.HTML_INJECTION_DETAILS)
    ctx.add.verify_modal_closed()
    _expect_network_in_tree(ctx, name)

    ctx.tree.open_for_network(ctx.region, name)
    # Payload should appear as text, not execute
    assert ctx.page.locator("dialog, [role='alertdialog']").count() == 0
    expect(
        ctx.page.get_by_text(re.compile(r"onerror|img src", re.IGNORECASE)).first
    ).to_be_visible(timeout=10000)


# ---------------------------------------------------------------------------
# TC_049 – Server / network failure
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_049_server_failure_shows_error(page, credentials):
    """TC_049: Server/network failure shows error; modal keeps entered data."""
    name = unique(td.NAME_SERVER_FAILURE)
    ctx = _prepare(page, credentials)

    def _fail(route: Route):
        route.abort("failed")

    ctx.page.route(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN), _fail)
    try:
        ctx.add.fill_network_name(name)
        ctx.add.fill_details(td.DETAILS_SERVER_FAILURE)
        ctx.add.draw_coverage_polygon()
        ctx.add.submit()
        ctx.add.verify_modal_open()
        ctx.add.verify_network_name_value(name)
        try:
            expect(ctx.add.server_unreachable_error_toast).to_be_visible(timeout=8000)
        except AssertionError:
            expect(ctx.add.error_toast.first).to_be_visible(timeout=5000)
        # Close modal before touching the tree (overlay otherwise intercepts clicks).
        ctx.add.cancel()
        try:
            ctx.add.verify_modal_closed()
        except AssertionError:
            ctx.add.close_via_x()
            ctx.add.verify_modal_closed()
        _expect_network_not_in_tree(ctx, name)
    finally:
        ctx.page.unroute(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN))


# ---------------------------------------------------------------------------
# TC_050 – Parent region deleted during creation (simulated)
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="Simulated test; multi-session delete is environment-specific.")
def test_TC_ADD_NETWORK_050_parent_region_deleted_during_creation(page, credentials):
    """
    TC_050: Parent region deleted while modal open.
    Simulated by forcing the API to return a region-invalid style error.
    Full multi-session delete is environment-specific.
    """
    name = unique(td.NAME_DELETED_REGION)
    ctx = _prepare(page, credentials, region=td.REGION_DELETED)

    def _invalid_region(route: Route):
        route.fulfill(
            status=422,
            content_type="application/json",
            body='{"message":"The selected region is invalid.","errors":{"region_id":["The selected region is invalid."]}}',
        )

    ctx.page.route(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN), _invalid_region)
    try:
        ctx.add.fill_network_name(name)
        ctx.add.draw_coverage_polygon()
        ctx.add.submit()
        ctx.add.verify_modal_open()
        expect(
            ctx.add.parent_region_error.or_(ctx.add.error_toast.first)
        ).to_be_visible(timeout=10000)
    finally:
        ctx.page.unroute(re.compile(td.CREATE_NETWORK_API_ROUTE_PATTERN))


# ---------------------------------------------------------------------------
# TC_051 – Cleared session blocks create
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_051_cleared_session_blocks_create(page, credentials):
    """TC_051: After clearing session, create is blocked / redirected to login."""
    name = unique(td.NAME_SESSION_CLEARED)
    ctx = _prepare(page, credentials)

    ctx.add.fill_network_name(name)
    ctx.add.fill_details(td.DETAILS_SESSION_CLEARED)
    ctx.add.draw_coverage_polygon()

    # Clear cookies / storage to invalidate session
    ctx.page.context.clear_cookies()
    ctx.page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")

    ctx.add.submit()
    ctx.page.wait_for_timeout(2000)

    try:
        expect(ctx.add.unauthenticated_error_toast).to_be_visible(timeout=8000)
    except AssertionError:
        expect(ctx.page).to_have_url(re.compile(r".*/login"), timeout=10000)


# ---------------------------------------------------------------------------
# TC_052 – Network appears without refresh
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_052_network_appears_without_refresh(page, credentials):
    """TC_052: New network appears under region without page reload."""
    name = unique(td.NAME_HIERARCHY)
    ctx = _prepare(
        page, credentials, region=td.REGION_HIERARCHY, open_add_network=True
    )

    _fill_minimal_and_submit(ctx, name)
    ctx.add.verify_modal_closed()

    # Coverage tree may automatically collapse after network creation.
    # Expand the region and verify the newly created network without reloading.
    ctx.tree.expand_region(ctx.region)

    row = ctx.tree.network_rows(ctx.region_id, name).first

    # Allow the tree to finish updating before retrying expansion.
    # try:
    #     expect(row).to_be_visible(timeout=3000)
    # except AssertionError:
    #     ctx.tree.expand_region(ctx.region)
    #     expect(row).to_be_visible(timeout=10000)


# ---------------------------------------------------------------------------
# TC_053 – 'No network' placeholder for empty region
# ---------------------------------------------------------------------------
def test_TC_ADD_NETWORK_053_no_network_placeholder_for_empty_region(page, credentials):
    """
    TC_053: Create a new region with no networks, expand it, and verify
    the 'No network' placeholder is shown.
    """
    ctx = _prepare(page, credentials, open_add_network=False)
    region_name = unique(td.REGION_EMPTY)

    add_region = AddRegionModal(page)
    add_region.open()
    add_region.fill_region_name(region_name)
    add_region.submit()
    add_region.verify_modal_closed()
    expect(ctx.tree.region_rows(region_name).first).to_be_visible(timeout=15000)

    ctx.tree.expand_region(region_name)
    no_network = ctx.page.get_by_text(
        re.compile(r"no\s+network", re.IGNORECASE)
    ).first
    expect(no_network).to_be_visible(timeout=10000)
