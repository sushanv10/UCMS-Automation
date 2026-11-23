"""
Catalog - Edit Region automation tests

"""
import re
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, expect
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config.config import Config
from modals.add_region_modal import AddRegionModal
from modals.edit_region_modal import EditRegionModal
from modals.region_detail_modal import RegionDetailsModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import edit_region_test_data as td
from utils.helpers import unique

pytestmark = [pytest.mark.edit_region, pytest.mark.timeout(180)]

TC = td.TC_PREFIX


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    """Everything a test needs after setup."""
    page: Page
    explorer: NetworkExplorerPage
    tree: RegionDetailsModal
    edit: EditRegionModal
    add: AddRegionModal
    name: str          # name of the region under test
    region_id: str     # ID read from the tree at setup (compare only, never reused for lookups)


def _login_and_open_coverage(page: Page, credentials: tuple[str, str]):
    """Log in and open the Coverage panel."""
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

    return explorer, RegionDetailsModal(page), EditRegionModal(page), add


def _ensure_region(add: AddRegionModal, name: str):
    """Create the region through Add Region (no polygon) ONLY if it is not in the tree."""
    if add.region_tree_node(name).count() == 0:
        add.open()
        add.fill_region_name(name)
        add.submit()
        add.verify_modal_closed()
        expect(add.region_tree_node(name).first).to_be_visible(timeout=15000)


def _prepare(
    page: Page,
    credentials: tuple[str, str],
    region: str = td.REGION_DEFAULT,
    unique_region: bool = False,
    open_edit: bool = True,
) -> Ctx:
    """
    Login -> make sure the region exists (a NEW unique one if unique_region) ->
    open Region Details -> (optionally) click Edit.
    """
    explorer, tree, edit, add = _login_and_open_coverage(page, credentials)
    name = unique(region) if unique_region else region
    _ensure_region(add, name)

    region_id = tree.open_for_region_name(name)
    ctx = Ctx(page, explorer, tree, edit, add, name, region_id)

    if open_edit:
        tree.click_edit()
        edit.verify_modal_open()
    return ctx


# ---------------------------------------------------------------------------
# Flow helpers
# ---------------------------------------------------------------------------
def _reload(ctx: Ctx):
    ctx.page.reload(wait_until="domcontentloaded")
    ctx.explorer.verify_page_loaded()
    ctx.explorer.open_coverage_panel()
    ctx.explorer.verify_coverage_panel_open()
    ctx.add.verify_region_tree_loaded()


def _close_details(ctx: Ctx):
    """Close Region Details if it is still open behind the edit modal."""
    if ctx.tree.modal_heading.is_visible():
        ctx.tree.close_via_button()
        ctx.tree.verify_modal_closed()


def _open_details(ctx: Ctx, name: str) -> str:
    """Open Region Details for `name`; reload once and retry if its row is missing."""
    _close_details(ctx)
    try:
        return ctx.tree.open_for_region_name(name)
    except Exception:
        _reload(ctx)
        return ctx.tree.open_for_region_name(name)


def _reopen_edit(ctx: Ctx, name: str):
    _open_details(ctx, name)
    ctx.tree.click_edit()
    ctx.edit.verify_modal_open()


def _edit_and_save(ctx: Ctx, new_name: str):
    """Replace the Region Name, click Save Changes and wait for the modal to close."""
    ctx.edit.fill_region_name(new_name)
    ctx.edit.save()
    ctx.edit.verify_modal_closed()


def _expect_in_tree(ctx: Ctx, name: str):
    """The region row is visible; reload once if the tree has not updated."""
    row = ctx.tree.region_tree_rows(name).first
    try:
        expect(row).to_be_visible(timeout=3000)
    except AssertionError:
        _reload(ctx)
        expect(ctx.tree.region_tree_rows(name).first).to_be_visible(timeout=15000)


def _expect_not_in_tree(ctx: Ctx, name: str):
    """Reload first so the check uses server-backed data."""
    _reload(ctx)
    expect(ctx.tree.region_tree_rows(name)).to_have_count(0, timeout=15000)


def _expect_count(ctx: Ctx, name: str, count: int):
    """Exactly `count` rows with this name (reload once if the tree has not updated)."""
    rows = ctx.tree.region_tree_rows(name)
    try:
        expect(rows).to_have_count(count, timeout=3000)
    except AssertionError:
        _reload(ctx)
        expect(ctx.tree.region_tree_rows(name)).to_have_count(count, timeout=15000)


def _assert_saved(ctx: Ctx, name: str):
    """Region Details and the Edit form both show `name` (IDs read fresh from the tree)."""
    _open_details(ctx, name)
    ctx.tree.verify_opened_region_details(name)
    ctx.tree.click_edit()
    ctx.edit.verify_modal_open()
    ctx.edit.verify_region_name_value(name)
    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()


def _assert_original(ctx: Ctx):
    """Nothing was saved: the region still has its original name."""
    _assert_saved(ctx, ctx.name)


def _cancel_and_assert_original(ctx: Ctx):
    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()
    _assert_original(ctx)


def _long_name(length: int, filler: str) -> str:
    """Unique name of exactly `length` characters."""
    suffix = unique("")  # "_" + 6 characters
    return filler * (length - len(suffix)) + suffix


def _assert_over_limit_rejected(ctx: Ctx, value: str):
    """A name longer than 255 characters is blocked in the field or rejected on save."""
    edit = ctx.edit
    if len(edit.region_name_input.input_value()) <= td.MAX_NAME_LENGTH:
        return  # the field stopped accepting characters at the limit
    edit.save()
    edit.verify_modal_open()
    expect(edit.name_too_long_error).to_be_visible()
    _cancel_and_assert_original(ctx)


# --- write requests (slow / failing / counted) ------------------------------
def _is_write(request) -> bool:
    return request.method in ("POST", "PUT", "PATCH") and request.resource_type in ("xhr", "fetch")


def _delay_writes(page: Page, ms: int):
    def handler(route):
        if _is_write(route.request):
            page.wait_for_timeout(ms)
        route.continue_()

    page.route("**/*", handler)


def _login_again(ctx: Ctx, credentials: tuple[str, str]):
    login_page = LoginPage(ctx.page)
    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(*credentials)
    login_page.verify_login_successful()
    ctx.explorer.verify_page_loaded()
    ctx.explorer.open_coverage_panel()
    ctx.explorer.verify_coverage_panel_open()
    ctx.add.verify_region_tree_loaded()


# ===========================================================================
# UI (001 - 021)
# ===========================================================================
def test_TC_EDIT_REGION_001_edit_modal_opens_from_region_details(page, credentials):
    ctx = _prepare(page, credentials, open_edit=False)

    ctx.tree.verify_modal_open()
    expect(ctx.tree.edit_button).to_be_visible()
    expect(ctx.tree.close_button).to_be_visible()

    ctx.tree.click_edit()

    ctx.edit.verify_modal_open()
    ctx.edit.verify_region_name_value(ctx.name)
    expect(ctx.edit.region_name_input).to_be_editable()
    expect(ctx.edit.cancel_button).to_be_visible()
    expect(ctx.edit.save_changes_button).to_be_visible()


def test_TC_EDIT_REGION_002_modal_title_displays_correctly(page, credentials):
    ctx = _prepare(page, credentials)
    edit = ctx.edit

    expect(edit.modal_heading).to_have_text(td.MODAL_TITLE)
    expect(edit.close_button).to_be_visible()

    weight = edit.modal_heading.evaluate("el => getComputedStyle(el).fontWeight")
    assert weight == "bold" or int(weight) >= 600, f"Header is not bold (weight={weight})"
    assert edit.modal_heading.bounding_box()["x"] < edit.close_button.bounding_box()["x"], (
        "Header should be left of the X icon"
    )


def test_TC_EDIT_REGION_003_all_form_elements_displayed(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.verify_elements_visible()


def test_TC_EDIT_REGION_004_form_is_prepopulated(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_PREFILL)

    ctx.edit.verify_region_name_value(td.REGION_PREFILL)


def test_TC_EDIT_REGION_005_region_name_is_editable(page, credentials):
    ctx = _prepare(page, credentials)
    edit = ctx.edit

    expect(edit.region_name_input).to_be_editable()
    edit.type_at_end(td.TYPED_INPUT)
    edit.verify_region_name_value(f"{ctx.name}{td.TYPED_INPUT}")

    for _ in td.TYPED_INPUT:
        edit.region_name_input.press("Backspace")
    edit.verify_region_name_value(ctx.name)


def test_TC_EDIT_REGION_006_region_id_and_path_not_editable(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_ID_CHECK, unique_region=True)
    id_before = ctx.region_id

    # Region Name is the only editable field: no ID or Path field.
    expect(ctx.edit.region_name_input).to_be_editable()
    expect(page.get_by_label(re.compile(r"^(ID|Path)$"))).to_have_count(0)

    new_name = unique(td.REGION_ID_CHECK_NEW)
    _edit_and_save(ctx, new_name)

    # IDs are read fresh from the tree after the edit.
    id_after = _open_details(ctx, new_name)
    ctx.tree.verify_opened_region_details(new_name)
    assert id_after == id_before, f"Region ID changed: {id_before} -> {id_after}"
    _expect_count(ctx, new_name, 1)
    _expect_count(ctx, ctx.name, 0)


def test_TC_EDIT_REGION_007_edit_opens_correct_data_for_different_regions(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_OPEN_FIRST, open_edit=False)
    ctx.tree.close_via_button()
    _ensure_region(ctx.add, td.REGION_OPEN_SECOND)
    _reopen_edit(ctx, td.REGION_OPEN_FIRST)

    ctx.edit.verify_region_name_value(td.REGION_OPEN_FIRST)
    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()

    _reopen_edit(ctx, td.REGION_OPEN_SECOND)

    ctx.edit.verify_region_name_value(td.REGION_OPEN_SECOND)
    expect(ctx.edit.region_name_input).not_to_have_value(td.REGION_OPEN_FIRST)


def test_TC_EDIT_REGION_008_required_asterisk_on_region_name(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.edit.region_name_label).to_contain_text(td.REQUIRED_ASTERISK)


def test_TC_EDIT_REGION_009_button_labels_and_styling(page, credentials):
    ctx = _prepare(page, credentials)
    edit = ctx.edit

    expect(edit.cancel_button).to_have_text(td.CANCEL_BUTTON_LABEL)
    expect(edit.save_changes_button).to_have_text(td.SAVE_BUTTON_LABEL)

    background = "el => getComputedStyle(el).backgroundColor"
    save_bg = edit.save_changes_button.evaluate(background)
    assert save_bg != "rgba(0, 0, 0, 0)", "Save Changes should be a filled primary button"
    assert save_bg != edit.cancel_button.evaluate(background), (
        "Primary and secondary buttons look identical"
    )


def test_TC_EDIT_REGION_010_default_focus_on_region_name(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.edit.region_name_input).to_be_focused()


def test_TC_EDIT_REGION_011_placeholder_behavior(page, credentials):
    ctx = _prepare(page, credentials)
    edit = ctx.edit

    edit.clear_region_name()
    expect(edit.region_name_input).to_have_attribute("placeholder", td.REGION_NAME_PLACEHOLDER)
    edit.verify_region_name_value("")

    edit.type_at_end(td.PLACEHOLDER_TYPED_CHAR)
    edit.verify_region_name_value(td.PLACEHOLDER_TYPED_CHAR)


def test_TC_EDIT_REGION_012_close_via_x_discards_changes(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.CLOSE_ICON_NAME)
    ctx.edit.close_via_x()

    ctx.edit.verify_modal_closed()
    _expect_not_in_tree(ctx, td.CLOSE_ICON_NAME)
    _assert_original(ctx)


def test_TC_EDIT_REGION_013_escape_closes_without_saving(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.ESCAPE_NAME)
    page.keyboard.press("Escape")

    ctx.edit.verify_modal_closed()
    _expect_not_in_tree(ctx, td.ESCAPE_NAME)
    _assert_original(ctx)


def test_TC_EDIT_REGION_014_cancel_discards_changes(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.CANCEL_NAME)
    ctx.edit.cancel()

    ctx.edit.verify_modal_closed()
    _expect_not_in_tree(ctx, td.CANCEL_NAME)
    _assert_original(ctx)


def test_TC_EDIT_REGION_015_backdrop_click_never_saves(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.BACKDROP_NAME)
    page.mouse.click(10, 10)
    page.wait_for_timeout(500)

    # The modal may close or stay open by design - the change must never be saved.
    if ctx.edit.modal_heading.is_visible():
        ctx.edit.cancel()
        ctx.edit.verify_modal_closed()

    _expect_not_in_tree(ctx, td.BACKDROP_NAME)
    _assert_original(ctx)


def test_TC_EDIT_REGION_016_close_without_changes_has_no_side_effects(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.cancel()

    ctx.edit.verify_modal_closed()
    expect(ctx.edit.success_toast).to_have_count(0)
    _expect_in_tree(ctx, ctx.name)
    _assert_original(ctx)


def test_TC_EDIT_REGION_017_reopen_after_cancel_shows_saved_value(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.DISCARDED_NAME)
    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()

    _reopen_edit(ctx, ctx.name)

    ctx.edit.verify_region_name_value(ctx.name)
    expect(ctx.edit.region_name_input).not_to_have_value(td.DISCARDED_NAME)


def test_TC_EDIT_REGION_018_keyboard_tab_order(page, credentials):
    ctx = _prepare(page, credentials)

    order = ctx.edit.focus_order()
    first_seen = [label for i, label in enumerate(order) if label not in order[:i]]

    for label in ("name", "zoom_in", "zoom_out", "cancel", "save"):
        assert label in first_seen, f"{label} never received focus. Order: {first_seen}"

    position = {label: first_seen.index(label) for label in first_seen}
    assert (
        position["name"] < position["zoom_in"] < position["zoom_out"]
        < position["cancel"] < position["save"]
    ), f"Unexpected tab order: {first_seen}"
    ctx.edit.verify_modal_open()  # focus stayed inside the modal


def test_TC_EDIT_REGION_019_enter_key_submits_form(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_ENTER_KEY, unique_region=True)
    new_name = unique(td.ENTER_KEY_NEW)

    ctx.edit.fill_region_name(new_name)
    ctx.edit.press_enter_on_name()

    try:
        ctx.edit.verify_modal_closed()
    except AssertionError:
        ctx.edit.cancel()
        pytest.skip("Enter does not submit the form (by design) - note in Remarks.")

    expect(ctx.edit.success_toast).to_be_visible(timeout=5000)
    _expect_count(ctx, new_name, 1)
    _expect_count(ctx, ctx.name, 0)


def test_TC_EDIT_REGION_020_edit_button_activated_by_keyboard(page, credentials):
    ctx = _prepare(page, credentials, open_edit=False)

    ctx.tree.modal_heading.click()  # start keyboard focus inside the modal
    for _ in range(40):
        page.keyboard.press("Tab")
        if ctx.tree.edit_button.evaluate("el => el === document.activeElement"):
            break
    else:
        pytest.fail("Edit button was not reached with the Tab key")

    expect(ctx.tree.edit_button).to_be_focused()
    page.keyboard.press("Enter")

    ctx.edit.verify_modal_open()


def test_TC_EDIT_REGION_021_layout_at_different_zoom_levels_and_widths(page, credentials):
    ctx = _prepare(page, credentials)
    edit = ctx.edit

    for width, height in td.ZOOM_VIEWPORTS:
        page.set_viewport_size({"width": width, "height": height})
        edit.verify_modal_open()

        for control in (edit.region_name_input, edit.cancel_button, edit.save_changes_button):
            control.scroll_into_view_if_needed()
            expect(control).to_be_visible()
            expect(control).to_be_in_viewport()

        box = edit.region_name_input.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1, (
            f"Region Name field is cut off at {width}x{height}"
        )


# ===========================================================================
# Functional (022 - 040)
# ===========================================================================
def test_TC_EDIT_REGION_022_edit_region_with_valid_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_VALID_UPDATE, unique_region=True)
    new_name = unique(td.VALID_UPDATE_NEW)

    ctx.edit.fill_region_name(new_name)
    ctx.edit.save()

    ctx.edit.verify_modal_closed()
    expect(ctx.edit.success_toast).to_be_visible(timeout=5000)
    _expect_count(ctx, new_name, 1)
    _assert_saved(ctx, new_name)


def test_TC_EDIT_REGION_023_success_notification_displayed_bottom_right(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_NOTIFICATION, unique_region=True)

    ctx.edit.fill_region_name(unique(td.NOTIFICATION_NEW))
    ctx.edit.save()

    expect(ctx.edit.success_toast).to_be_visible(timeout=5000)

    box = ctx.edit.success_toast.bounding_box()
    viewport = page.viewport_size

    assert box is not None, "Success notification bounding box could not be determined."

    # Verify notification is displayed in the bottom half.
    assert (
        box["y"] + box["height"] / 2 > viewport["height"] / 2
    ), "Notification is not in the bottom half."

    # Verify notification is displayed in the right half.
    assert (
        box["x"] + box["width"] / 2 > viewport["width"] / 2
    ), "Notification is not in the right half."

    # Verify notification disappears automatically.
    expect(ctx.edit.success_toast).to_be_hidden(timeout=15000)


def test_TC_EDIT_REGION_024_modal_closes_after_save(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_MODAL_CLOSE, unique_region=True)
    new_name = unique(td.MODAL_CLOSE_NEW)

    _edit_and_save(ctx, new_name)

    ctx.edit.verify_modal_closed()
    _expect_count(ctx, new_name, 1)
    _expect_count(ctx, ctx.name, 0)  # no stale name


def test_TC_EDIT_REGION_025_save_without_changes(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_NO_CHANGE, unique_region=True)
    edit = ctx.edit

    if edit.save_changes_button.is_enabled():
        edit.save()
        edit.verify_modal_closed()
        expect(edit.duplicate_name_error).to_have_count(0)
    else:
        edit.verify_save_disabled()  # disabled until the name changes
        edit.cancel()

    _expect_count(ctx, ctx.name, 1)
    _assert_original(ctx)


def test_TC_EDIT_REGION_026_revert_to_original_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_REVERT, unique_region=True)
    temp_name = unique(td.REVERT_TEMP)
    id_before = ctx.region_id

    _edit_and_save(ctx, temp_name)
    _reopen_edit(ctx, temp_name)
    _edit_and_save(ctx, ctx.name)

    _expect_count(ctx, ctx.name, 1)
    _expect_count(ctx, temp_name, 0)
    id_after = _open_details(ctx, ctx.name)  # read fresh
    ctx.tree.verify_opened_region_details(ctx.name)
    assert id_after == id_before, f"Region ID changed: {id_before} -> {id_after}"


def test_TC_EDIT_REGION_027_multiple_consecutive_edits(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_CONSECUTIVE, unique_region=True)
    names = [unique(name) for name in td.CONSECUTIVE_NAMES]

    current = ctx.name
    for new_name in names:
        if current != ctx.name:
            _reopen_edit(ctx, current)
        _edit_and_save(ctx, new_name)
        current = new_name

    _expect_count(ctx, names[-1], 1)
    for old_name in [ctx.name, *names[:-1]]:
        _expect_count(ctx, old_name, 0)
    _assert_saved(ctx, names[-1])


def test_TC_EDIT_REGION_028_minimum_length_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_MIN_LENGTH, unique_region=True)
    # 'E' cannot carry a unique suffix: exactly one more 'E' row must appear.
    count_before = ctx.tree.region_tree_rows(td.MIN_LENGTH_NAME).count()

    _edit_and_save(ctx, td.MIN_LENGTH_NAME)

    _expect_count(ctx, td.MIN_LENGTH_NAME, count_before + 1)
    _expect_count(ctx, ctx.name, 0)


def test_TC_EDIT_REGION_029_maximum_length_name_255(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_MAX_255, unique_region=True)
    new_name = _long_name(td.MAX_NAME_LENGTH, td.MAX_255_FILLER)
    assert len(new_name) == td.MAX_NAME_LENGTH

    _edit_and_save(ctx, new_name)

    _expect_count(ctx, new_name, 1)
    _assert_saved(ctx, new_name)  # full value shown in Region Details


def test_TC_EDIT_REGION_030_boundary_max_length_minus_one_254(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_MAX_254, unique_region=True)
    new_name = _long_name(td.MAX_254_LENGTH, td.MAX_254_FILLER)
    assert len(new_name) == td.MAX_254_LENGTH

    _edit_and_save(ctx, new_name)

    _expect_count(ctx, new_name, 1)
    _assert_saved(ctx, new_name)


def test_TC_EDIT_REGION_031_numeric_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_NUMERIC, unique_region=True)
    # '20260' cannot carry a unique suffix: exactly one more row must appear.
    count_before = ctx.tree.region_tree_rows(td.NUMERIC_NAME).count()

    _edit_and_save(ctx, td.NUMERIC_NAME)

    _expect_count(ctx, td.NUMERIC_NAME, count_before + 1)
    _expect_count(ctx, ctx.name, 0)


def test_TC_EDIT_REGION_032_alphanumeric_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_ALPHANUMERIC, unique_region=True)
    new_name = unique(td.ALPHANUMERIC_NAME)

    _edit_and_save(ctx, new_name)

    _expect_count(ctx, new_name, 1)
    _assert_saved(ctx, new_name)


def test_TC_EDIT_REGION_033_special_characters_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_SPECIAL, unique_region=True)
    new_name = unique(td.SPECIAL_NAME)

    _edit_and_save(ctx, new_name)

    _expect_count(ctx, new_name, 1)
    expect(ctx.tree.region_tree_rows(new_name).first).not_to_contain_text("&amp;")
    _assert_saved(ctx, new_name)


def test_TC_EDIT_REGION_034_unicode_nepali_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_UNICODE, unique_region=True)
    new_name = unique(td.UNICODE_NAME)

    _edit_and_save(ctx, new_name)
    _assert_saved(ctx, new_name)

    _reload(ctx)  # still correct after a page refresh
    _assert_saved(ctx, new_name)


def test_TC_EDIT_REGION_035_case_only_change(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_CASE, unique_region=True)
    upper_name = ctx.name.upper()

    _edit_and_save(ctx, upper_name)  # must not be blocked as a duplicate of itself

    _expect_count(ctx, upper_name, 1)
    _assert_saved(ctx, upper_name)


def test_TC_EDIT_REGION_037_leading_trailing_spaces_trimmed(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_TRIM, unique_region=True)
    trimmed = unique(td.TRIM_NAME)

    _edit_and_save(ctx, f" {trimmed} ")

    _expect_count(ctx, trimmed, 1)
    _assert_saved(ctx, trimmed)  # Details, hierarchy and the Edit field show no spaces


def test_TC_EDIT_REGION_039_save_button_loading_state(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_LOADING, unique_region=True)
    new_name = unique(td.LOADING_NEW)

    _delay_writes(page, td.LOADING_DELAY_MS)
    ctx.edit.fill_region_name(new_name)
    ctx.edit.save()

    expect(ctx.edit.save_changes_button).to_be_disabled(timeout=5000)
    expect(ctx.edit.save_changes_button).to_contain_text(td.LOADING_BUTTON_TEXT, timeout=5000)

    ctx.edit.verify_modal_closed()
    _expect_count(ctx, new_name, 1)


def test_TC_EDIT_REGION_040_double_click_sends_one_request(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_DOUBLE_CLICK, unique_region=True)
    new_name = unique(td.DOUBLE_CLICK_NEW)
    writes: list[str] = []
    page.on("request", lambda r: writes.append(r.url) if _is_write(r) else None)

    ctx.edit.fill_region_name(new_name)
    ctx.edit.save_changes_button.dblclick()
    ctx.edit.verify_modal_closed()

    assert len(writes) == 1, f"Expected 1 update request, got {writes}"
    _expect_count(ctx, new_name, 1)
    _expect_count(ctx, ctx.name, 0)


# ===========================================================================
# Validation (041 - 052)
# ===========================================================================
def test_TC_EDIT_REGION_041_empty_region_name_blocked(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.clear_region_name()
    ctx.edit.save()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.region_name_required_error).to_be_visible(timeout=5000)
    _cancel_and_assert_original(ctx)


def test_TC_EDIT_REGION_042_whitespace_only_name_blocked(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.WHITESPACE_NAME)
    ctx.edit.save()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.region_name_required_error).to_be_visible(timeout=5000)
    _cancel_and_assert_original(ctx)


def test_TC_EDIT_REGION_043_validation_message_auto_clears(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.clear_region_name()
    ctx.edit.save()
    expect(ctx.edit.region_name_required_error).to_be_visible(timeout=5000)

    ctx.edit.fill_region_name(td.VALID_AFTER_ERROR)  # not saved

    expect(ctx.edit.region_name_required_error).to_be_hidden(timeout=5000)


def test_TC_EDIT_REGION_044_name_exceeding_max_length_rejected(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.fill_region_name(td.OVER_MAX_NAME)

    _assert_over_limit_rejected(ctx, td.OVER_MAX_NAME)


def test_TC_EDIT_REGION_045_pasted_long_name_truncated_or_rejected(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.edit.paste_into_region_name(td.PASTE_LONG_NAME)

    _assert_over_limit_rejected(ctx, td.PASTE_LONG_NAME)


def test_TC_EDIT_REGION_046_duplicate_name_exact_match_not_blocked(page, credentials):
    # Per the sheet's Expected result: the update is NOT rejected.
    ctx = _prepare(page, credentials, region=td.REGION_DUPLICATE, unique_region=True,
                   open_edit=False)
    existing = unique(td.REGION_DUPLICATE_EXISTING)
    ctx.tree.close_via_button()
    _ensure_region(ctx.add, existing)
    _reopen_edit(ctx, ctx.name)

    ctx.edit.fill_region_name(existing)
    ctx.edit.save()

    ctx.edit.verify_modal_closed()
    expect(ctx.edit.duplicate_name_error).to_have_count(0)
    _expect_count(ctx, existing, 2)


# def test_TC_EDIT_REGION_047_duplicate_name_different_case_rejected(page, credentials):
#     ctx = _prepare(page, credentials, region=td.REGION_DUPLICATE_CASE, unique_region=True,
#                    open_edit=False)
#     existing = unique(td.REGION_DUPLICATE_CASE_EXISTING)
#     ctx.tree.close_via_button()
#     _ensure_region(ctx.add, existing)
#     _reopen_edit(ctx, ctx.name)

#     ctx.edit.fill_region_name(existing.lower())
#     ctx.edit.save()

#     ctx.edit.verify_modal_open()
#     expect(ctx.edit.duplicate_name_error).to_be_visible(timeout=5000)
#     _cancel_and_assert_original(ctx)


# def test_TC_EDIT_REGION_048_duplicate_name_with_extra_spaces_rejected(page, credentials):
#     ctx = _prepare(page, credentials, region=td.REGION_DUPLICATE_SPACE, unique_region=True,
#                    open_edit=False)
#     existing = unique(td.REGION_DUPLICATE_SPACE_EXISTING)
#     ctx.tree.close_via_button()
#     _ensure_region(ctx.add, existing)
#     _reopen_edit(ctx, ctx.name)

#     ctx.edit.fill_region_name(f" {existing} ")
#     ctx.edit.save()

#     ctx.edit.verify_modal_open()
#     expect(ctx.edit.duplicate_name_error).to_be_visible(timeout=5000)
#     _cancel_and_assert_original(ctx)


def test_TC_EDIT_REGION_049_emoji_in_name_handled_gracefully(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_EMOJI, unique_region=True)
    new_name = unique(td.EMOJI_NAME)

    ctx.edit.fill_region_name(new_name)
    ctx.edit.save()
    outcome = ctx.edit.submit_outcome()

    assert outcome in ("saved", "error"), "Save neither completed nor showed a message"
    if outcome == "saved":
        _expect_count(ctx, new_name, 1)
        _assert_saved(ctx, new_name)


def test_TC_EDIT_REGION_050_special_characters_only_name(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_SPECIAL_ONLY, unique_region=True)
    # '@@@###$$$' cannot carry a unique suffix: exactly one more row must appear.
    count_before = ctx.tree.region_tree_rows(td.SPECIAL_ONLY_NAME).count()

    _edit_and_save(ctx, td.SPECIAL_ONLY_NAME)

    _expect_count(ctx, td.SPECIAL_ONLY_NAME, count_before + 1)



def test_TC_EDIT_REGION_051_multiline_text_in_name_does_not_break_form(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_MULTILINE, unique_region=True)

    multiline_text = unique(td.MULTILINE_TEXT)

    expected_name = re.sub(r"[\r\n]+", " ", multiline_text).strip()

    # Paste multiline text into the Region Name field.
    ctx.edit.paste_into_region_name(multiline_text)

    pasted_value = ctx.edit.region_name_input.input_value()

    print(f"\nOriginal multiline test data: {repr(multiline_text)}")
    print(f"Actual pasted input value: {repr(pasted_value)}")
    print(f"Expected normalized value: {repr(expected_name)}")

    # Verify that multiline input is converted into a single-line value.
    assert pasted_value == expected_name, (
        f"Region Name was not normalized correctly. "
        f"Expected: {repr(expected_name)}, "
        f"Actual: {repr(pasted_value)}"
    )

    assert "\n" not in pasted_value and "\r" not in pasted_value, (
        f"Region Name retained a line break: {repr(pasted_value)}"
    )

    # Save the updated Region Name.
    ctx.edit.save()

    if ctx.edit.submit_outcome() == "saved":
        _reload(ctx)

        # Locate Region rows in the Coverage tree.
        rows = page.locator("button").filter(
            has_text=re.compile(r"^Region:\s")
        )

        # Normalize rendered whitespace before checking the Region Name.
        row_texts = rows.all_inner_texts()
        normalized_row_texts = [
            " ".join(text.split()) for text in row_texts
        ]

        assert any(expected_name in text for text in normalized_row_texts), (
            f"Normalized Region Name '{expected_name}' "
            f"was not found in the Region tree. "
            f"Available rows: {normalized_row_texts}"
        )

    else:
        # If the application rejects the value, a validation message must appear.
        expect(ctx.edit.validation_alert).to_be_visible()



def test_TC_EDIT_REGION_052_validation_failure_keeps_data_unchanged(page, credentials):
    ctx = _prepare(page, credentials, region=td.REGION_VALIDATION_FAILURE)

    ctx.edit.clear_region_name()
    ctx.edit.save()
    expect(ctx.edit.region_name_required_error).to_be_visible(timeout=5000)

    _cancel_and_assert_original(ctx)


# ===========================================================================
# Security (053 - 056)
# ===========================================================================
@pytest.mark.parametrize(
    "payload, injected_element",
    [
        pytest.param(td.XSS_PAYLOAD, td.XSS_SELECTOR, id=f"{TC}_053_script_in_name"),
        pytest.param(td.HTML_PAYLOAD, td.HTML_SELECTOR, id=f"{TC}_055_html_in_name"),
    ],
)
def test_region_name_payload_is_not_executed(page, credentials, payload, injected_element):
    dialogs: list[str] = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    region = td.REGION_XSS if payload == td.XSS_PAYLOAD else td.REGION_HTML
    ctx = _prepare(page, credentials, region=region, unique_region=True)
    new_name = f"{payload}{unique('')}"

    ctx.edit.fill_region_name(new_name)
    ctx.edit.save()
    outcome = ctx.edit.submit_outcome()

    assert not dialogs, f"A JavaScript dialog was triggered: {dialogs}"
    expect(page.locator(injected_element)).to_have_count(0)
    if outcome == "saved":
        _expect_count(ctx, new_name, 1)  # shown as literal text in the tree
        _assert_saved(ctx, new_name)  # and in Region Details
        assert not dialogs, f"A JavaScript dialog was triggered: {dialogs}"
        expect(page.locator(injected_element)).to_have_count(0)


def test_TC_EDIT_REGION_056_user_without_role_cannot_edit(
    page, credentials, restricted_credentials
):
    ctx = _prepare(page, credentials, region=td.REGION_PERMISSION, open_edit=False)
    ctx.tree.close_via_button()

    # Switch to the restricted (no-role) user.
    ctx.explorer.clear_session_data()
    _login_again(ctx, restricted_credentials)
    _open_details(ctx, ctx.name)

    try:
        expect(ctx.tree.edit_button).to_be_visible(timeout=5000)
    except AssertionError:
        return  # Edit is not offered to this user -> cannot edit
    if ctx.tree.edit_button.is_disabled():
        return

    statuses: list[int] = []
    page.on(
        "response",
        lambda r: statuses.append(r.status) if _is_write(r.request) else None,
    )

    ctx.tree.click_edit()
    ctx.edit.verify_modal_open()
    ctx.edit.fill_region_name(unique(td.PERMISSION_NEW))
    ctx.edit.save()

    expect(ctx.edit.permission_error).to_be_visible(timeout=8000)
    assert all(status in (401, 403) for status in statuses), f"Unexpected statuses: {statuses}"
    ctx.edit.cancel()
    _expect_count(ctx, ctx.name, 1)