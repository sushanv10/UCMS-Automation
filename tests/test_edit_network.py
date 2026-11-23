"""
Catalog - Edit Network automation tests.

"""
import re
from dataclasses import dataclass, field

import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from modals.add_network_modal import AddNetworkModal
from modals.add_region_modal import AddRegionModal
from modals.edit_network_modal import EditNetworkModal
from modals.network_details_modal import NetworkDetailsModal
from pages.login_page import LoginPage
from pages.nav_bar import NavBar
from pages.network_explorer_page import NetworkExplorerPage
from test_data import edit_network_test_data as td
from utils.helpers import unique


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
@dataclass
class NetSpec:
    """A network to create during setup."""
    prefix: str
    details: str = ""
    active: bool = True
    region: str = td.REGION_NAME


@dataclass
class Ctx:
    """Everything a test needs after setup."""
    page: Page
    explorer: NetworkExplorerPage
    tree: NetworkDetailsModal
    edit: EditNetworkModal
    region: str
    name: str                      # unique name of the primary network
    region_id: str = ""
    network_id: str = ""
    others: list[str] = field(default_factory=list)   # unique names of extra networks


def _login_and_open_coverage(page: Page, credentials: tuple[str, str]):
    """Log in and open the Coverage panel."""
    login_page = LoginPage(page)
    explorer = NetworkExplorerPage(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()

    return explorer, NetworkDetailsModal(page), EditNetworkModal(page)


def _ensure_region(page: Page, tree: NetworkDetailsModal, region_name: str):
    """Create the region through Add Region ONLY if it is not in the tree yet."""
    expect(
        page.locator("button").filter(has_text=re.compile(r"^Region:\s")).first
    ).to_be_visible(timeout=15000)

    if tree.region_rows(region_name).count() == 0:
        add_region = AddRegionModal(page)
        add_region.open()
        add_region.fill_region_name(region_name)
        add_region.submit()
        add_region.verify_modal_closed()
        expect(tree.region_rows(region_name).first).to_be_visible(timeout=15000)


def _ensure_network(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    region_name: str,
    network_name: str,
    *,
    details: str = "",
    active: bool = True,
) -> None:
    """
    Create the network under region_name ONLY if it is not already present.

    Used for the shared DEFAULT_EDIT_NAME ("Edit_Network_Test") so re-runs
    reuse the same row instead of creating a new unique network every time.
    """
    _ensure_region(page, tree, region_name)
    region_id = tree.get_region_id(region_name)
    tree.expand_region(region_name)
    if tree.network_rows(region_id, network_name).count() > 0:
        return

    _create_network(
        page,
        tree,
        explorer,
        NetSpec(network_name, details=details, active=active, region=region_name),
        network_name,
        refresh=True,
    )


def _reload_coverage(ctx: Ctx):
    """
    Reload the page, reopen Coverage and expand the original region.
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

    # expand_region is idempotent in the corrected NetworkDetailsModal.
    ctx.tree.expand_region(ctx.region)

    print("\n===== COVERAGE RELOAD DEBUG =====")
    print("Region Name:", ctx.region)
    print("Region ID:", refreshed_region_id)
    print("Region Row:", region_row.inner_text())




def _create_network(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    spec: NetSpec,
    name: str,
    refresh: bool,
):
    """Create a network (4-vertex polygon) via the region's '+' control."""
    add_network = AddNetworkModal(page)

    tree.open_add_network(spec.region)
    add_network.verify_modal_open()
    add_network.fill_network_name(name)
    if spec.details:
        add_network.fill_details(spec.details)
    add_network.set_active(spec.active)
    add_network.draw_coverage_polygon(td.POLYGON_POINTS)
    add_network.submit()
    add_network.verify_modal_closed()

    if refresh:  # the tree only shows new networks after a reload
        page.reload(wait_until="domcontentloaded")
        explorer.verify_page_loaded()
        explorer.open_coverage_panel()
        explorer.verify_coverage_panel_open()
        expect(tree.region_rows(spec.region).first).to_be_visible(timeout=15000)
        tree.expand_region(spec.region)


def _prepare(
    page: Page,
    credentials: tuple[str, str],
    prefix: str,
    details: str = "",
    active: bool = True,
    open_edit: bool = True,
    others: tuple[NetSpec, ...] = (),
) -> Ctx:
    """
    Login -> ensure region -> create the network (+ optional extra networks)
    -> open Network Details -> (optionally) click Edit.

    Special case: when `prefix` is DEFAULT_EDIT_NAME / DEFAULT_EDIT_NAME
    ("Edit_Network_Test"), the network is created ONLY if it does not already
    exist (shared fixed name for non-mutating UI cases). Every other prefix is
    still wrapped with unique() so functional cases stay isolated across runs.
    """
    explorer, tree, edit = _login_and_open_coverage(page, credentials)

    primary = NetSpec(prefix, details, active)
    specs = [primary, *others]

    # Fixed shared network vs unique-per-run networks
    reuse_fixed = prefix in (td.DEFAULT_EDIT_NAME)
    names: list[str] = []
    for index, spec in enumerate(specs):
        if index == 0 and reuse_fixed:
            name = td.DEFAULT_EDIT_NAME
            _ensure_network(
                page,
                tree,
                explorer,
                spec.region,
                name,
                details=spec.details,
                active=spec.active,
            )
        else:
            name = unique(spec.prefix)
            _ensure_region(page, tree, spec.region)
            _create_network(
                page,
                tree,
                explorer,
                spec,
                name,
                refresh=index == len(specs) - 1,
            )
        names.append(name)

    # When only the fixed network was ensured (no unique creates), still expand.
    tree.expand_region(primary.region)

    network_id = tree.open_for_network(primary.region, names[0])
    ctx = Ctx(
        page=page,
        explorer=explorer,
        tree=tree,
        edit=edit,
        region=primary.region,
        name=names[0],
        region_id=tree.opened_region_id,
        network_id=network_id,
        others=names[1:],
    )

    if open_edit:
        tree.click_edit()
        edit.verify_modal_open()
    return ctx


# ---------------------------------------------------------------------------
# Action / assertion helpers
# ---------------------------------------------------------------------------
def _close_details(ctx: Ctx):
    """Close Network Details if it is still open behind the edit modal."""
    if ctx.tree.modal_heading.is_visible():
        ctx.tree.close_via_button()
        ctx.tree.verify_modal_closed()


def _open_details(ctx: Ctx, name: str):
    """
    Open Network Details for `name`. The Coverage tree is not refreshed after an
    edit, so if the row is missing, reload once (re-expanding the region) and retry.
    """
    _close_details(ctx)
    try:
        return ctx.tree.open_for_network(ctx.region, name)
    except Exception as first_error:
        _reload_coverage(ctx)
        try:
            return ctx.tree.open_for_network(ctx.region, name)
        except Exception as retry_error:
            raise AssertionError(
                f"Could not open Network Details for {name!r} under "
                f"{ctx.region!r} after refreshing Coverage. "
                f"First error: {first_error}; retry error: {retry_error}"
            ) from retry_error


def _reopen_edit(ctx: Ctx, name: str):
    _open_details(ctx, name)
    ctx.tree.click_edit()
    ctx.edit.verify_modal_open()


def _edit_and_save(
    ctx: Ctx,
    name: str | None = None,
    details: str | None = None,
    active: bool | None = None,
):
    """Change the given fields, click Update Network and wait for the modal to close."""
    if name is not None:
        ctx.edit.fill_network_name(name)
    if details is not None:
        ctx.edit.fill_details(details)
    if active is not None:
        ctx.edit.set_active(active)
    ctx.edit.update()
    ctx.edit.verify_modal_closed()


def _row_visible(ctx: Ctx, name: str, timeout: int = 3000) -> bool:
    """True if the network row is visible in the tree within `timeout` ms."""
    row = ctx.tree.network_rows(ctx.region_id, name).first
    try:
        expect(row).to_be_visible(timeout=timeout)
        return True
    except AssertionError:
        return False



def _expect_in_tree(ctx: Ctx, name: str):
    """
    Verify that a network is visible in Coverage.

    Wait briefly for the current tree to update. If the row is still missing,
    reload the page, reopen Coverage, expand the region and retry.
    """
    row = ctx.tree.network_rows(ctx.region_id, name).first
    try:
        expect(row).to_be_visible(timeout=3000)
        return
    except AssertionError:
        pass

    print("\\nNetwork not found in the current Coverage tree; reloading...")
    print("Expected Network:", name)
    print("Expected Region ID:", ctx.region_id)

    _reload_coverage(ctx)

    row = ctx.tree.network_rows(ctx.region_id, name).first
    print("\\n===== NETWORK TREE DEBUG =====")
    print("Expected Network:", name)
    print("Matching Network Rows:", row.count())
    if row.count():
        print("Network Row Text:", row.inner_text())

    expect(row).to_be_visible(timeout=15000)


def _expect_not_in_tree(ctx: Ctx, name: str):
    """Reload before asserting absence so the check uses server-backed tree data."""
    _reload_coverage(ctx)
    expect(ctx.tree.network_rows(ctx.region_id, name)).to_have_count(0, timeout=15000)


def _expect_one_in_tree(ctx: Ctx, name: str):
    """Row exists exactly once (reload-aware)."""
    _expect_in_tree(ctx, name)
    expect(ctx.tree.network_rows(ctx.region_id, name)).to_have_count(1)


def _assert_edit_values(
    ctx: Ctx,
    name: str,
    details: str = "",
    active: bool | None = True,
    vertices: int | None = None,
):
    """Reopen Edit Network for `name`, verify the saved values, then cancel."""
    _reopen_edit(ctx, name)
    edit = ctx.edit
    edit.verify_network_name_value(name)
    edit.verify_details_value(details)
    if active is not None:
        expect(edit.active_checkbox).to_be_checked(checked=active)
    if vertices:
        edit.verify_vertex_count(vertices)
    edit.cancel()
    edit.verify_modal_closed()


def _assert_details_modal(ctx: Ctx, name: str, status: str = td.STATUS_ACTIVE):
    _open_details(ctx, name)
    ctx.tree.verify_network_details(ctx.region, name, status)


def _padded_name(base: str, length: int) -> str:
    """Name of exactly `length` characters that still ends with a unique suffix."""
    suffix = unique("")
    return base[: length - len(suffix)] + suffix


def _assert_over_limit_rejected(ctx: Ctx, value: str):
    """A name longer than 255 chars is blocked in the field or rejected on submit."""
    edit = ctx.edit
    edit.fill_network_name(value)
    if len(edit.network_name_input.input_value()) <= td.MAX_NAME_LENGTH:
        return  # field blocks typing beyond the limit
    edit.update()
    edit.verify_modal_open()
    expect(edit.name_too_long_error).to_be_visible()
    edit.cancel()
    edit.verify_modal_closed()
    _expect_in_tree(ctx, ctx.name)


def _try_save(ctx: Ctx, new_name: str) -> bool:
    """Fill the name and submit. Returns True if the modal closed (saved)."""
    ctx.edit.fill_network_name(new_name)
    ctx.edit.update()
    try:
        ctx.edit.verify_modal_closed()
        return True
    except AssertionError:
        return False


def _login_again(ctx: Ctx, credentials: tuple[str, str]):
    """Log in again after the session was cleared / signed out."""
    login_page = LoginPage(ctx.page)
    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(*credentials)
    login_page.verify_login_successful()
    ctx.explorer.verify_page_loaded()
    ctx.explorer.open_coverage_panel()
    ctx.explorer.verify_coverage_panel_open()
    expect(ctx.tree.region_rows(ctx.region).first).to_be_visible(timeout=15000)
    refreshed_region_id = ctx.tree.get_region_id(ctx.region)
    assert refreshed_region_id == ctx.region_id, (
        f"Region ID changed after login. Expected: {ctx.region_id}, "
        f"Actual: {refreshed_region_id}"
    )
    ctx.tree.expand_region(ctx.region)


def _expect_session_rejected(page: Page, edit: EditNetworkModal):
    """Update is blocked: 'Unauthenticated.' toast or redirect to Login."""
    try:
        expect(edit.unauthenticated_error_toast).to_be_visible(timeout=8000)
    except AssertionError:
        expect(page).to_have_url(re.compile(r".*/login"), timeout=10000)


def _network_row_texts(page: Page) -> list[str]:
    """Text of every network row currently rendered in the Coverage tree."""
    rows = page.locator("button").filter(
        has_text=re.compile(r"^(?:Network:\s+)?G\d+-\S+\s+-\s+")
    )
    return [text.strip() for text in rows.all_inner_texts()]


def _second_session(browser, credentials: tuple[str, str]):
    """Open a second browser context logged in as the same user."""
    context = browser.new_context(viewport=Config.VIEWPORT)
    page = context.new_page()
    explorer, tree, edit = _login_and_open_coverage(page, credentials)
    explorer.verify_page_loaded()
    explorer.verify_coverage_panel_open()
    return context, page, tree, edit


# ===========================================================================
# UI (001 - 025)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_001_edit_modal_opens_from_network_details(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME, open_edit=False)

    ctx.tree.verify_modal_open()
    expect(ctx.tree.edit_button).to_be_visible()
    expect(ctx.tree.close_button).to_be_visible()

    ctx.tree.click_edit()

    edit = ctx.edit
    edit.verify_modal_open()
    edit.verify_network_name_value(ctx.name)
    expect(edit.network_name_input).to_be_editable()
    expect(edit.details_input).to_be_editable()
    expect(edit.map_container).to_be_visible()
    expect(edit.active_checkbox).to_be_enabled()
    expect(edit.cancel_button).to_be_visible()
    expect(edit.update_button).to_be_visible()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_002_modal_title_displays_correctly(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    expect(edit.modal_heading).to_have_text(td.MODAL_TITLE)
    expect(edit.close_button).to_be_visible()

    weight = edit.modal_heading.evaluate("el => getComputedStyle(el).fontWeight")
    assert weight == "bold" or int(weight) >= 600, f"Header is not bold (weight={weight})"

    heading_box = edit.modal_heading.bounding_box()
    close_box = edit.close_button.bounding_box()
    assert heading_box["x"] < close_box["x"], "Header should be left of the X icon"


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_003_all_form_elements_displayed(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    ctx.edit.verify_elements_visible()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_004_form_is_prepopulated(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.NAME_PREFILL, details=td.DETAILS_PREFILL, open_edit=False
    )

    ctx.tree.click_edit()
    edit = ctx.edit
    edit.verify_modal_open()

    edit.verify_network_name_value(ctx.name)
    edit.verify_details_value(td.DETAILS_PREFILL)
    expect(edit.active_checkbox).to_be_checked()
    expect(edit.polygon_shapes.first).to_be_visible()
    edit.verify_vertex_count(td.POLYGON_VERTEX_COUNT)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_005_network_name_is_editable(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    expect(edit.network_name_input).to_be_editable()
    edit.type_into_network_name(td.TYPED_INPUT)
    assert edit.network_name_input.input_value().endswith(td.TYPED_INPUT)

    for _ in td.TYPED_INPUT:
        edit.network_name_input.press("Backspace")
    edit.verify_network_name_value(ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_006_details_empty_when_saved_without_details(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    # Genuinely empty: no 'null' / 'undefined' / whitespace-only content.
    ctx.edit.verify_details_value("")

# @pytest.mark.edit_network
# def test_TC_EDIT_NETWORK_007_edit_for_different_networks(
#     page: Page, credentials: tuple[str, str]
# ):
#     ctx = _prepare(page, credentials, td.NAME_OTHER)



@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_008_edit_opens_correct_data_for_different_networks(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.DEFAULT_EDIT_NAME,
        others=(NetSpec(td.NAME_OTHER, details=td.DETAILS_OTHER),),
    )
    edit = ctx.edit
    other_name = ctx.others[0]

    edit.verify_network_name_value(ctx.name)
    edit.verify_details_value("")
    edit.cancel()
    edit.verify_modal_closed()

    _reopen_edit(ctx, other_name)

    edit.verify_network_name_value(other_name)
    edit.verify_details_value(td.DETAILS_OTHER)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_009_required_asterisk_on_network_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    expect(ctx.edit.network_name_label).to_contain_text("*")
    expect(ctx.edit.details_label).not_to_contain_text("*")


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_010_button_labels_and_styling(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    expect(edit.cancel_button).to_have_text("Cancel")
    expect(edit.update_button).to_have_text("Update Network")

    update_bg = edit.update_button.evaluate("el => getComputedStyle(el).backgroundColor")
    cancel_bg = edit.cancel_button.evaluate("el => getComputedStyle(el).backgroundColor")
    assert update_bg != "rgba(0, 0, 0, 0)", "Update Network should be a filled primary button"
    assert update_bg != cancel_bg, "Primary and secondary buttons look identical"


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_011_default_focus_on_network_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    expect(ctx.edit.network_name_input).to_be_focused()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_012_placeholder_behavior(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    edit.clear_network_name()
    expect(edit.network_name_input).to_have_attribute(
        "placeholder", td.NETWORK_NAME_PLACEHOLDER
    )
    edit.verify_network_name_value("")

    edit.type_into_network_name(td.PLACEHOLDER_TYPED_CHAR)
    edit.verify_network_name_value(td.PLACEHOLDER_TYPED_CHAR)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_013_active_checkbox_reflects_saved_status(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.NAME_ACTIVE_SAVED,
        active=True,
        others=(NetSpec(td.NAME_INACTIVE_SAVED, active=False),),
    )

    expect(ctx.edit.active_checkbox).to_be_checked()
    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()

    _reopen_edit(ctx, ctx.others[0])
    expect(ctx.edit.active_checkbox).not_to_be_checked()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_014_active_checkbox_toggles(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    expect(edit.active_checkbox).to_be_checked()
    edit.active_checkbox.click()
    expect(edit.active_checkbox).not_to_be_checked()
    edit.active_checkbox.click()
    expect(edit.active_checkbox).to_be_checked()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_015_close_via_x_discards_changes(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    edit.fill_network_name(td.CLOSE_ICON_NAME)
    edit.fill_details(td.CLOSE_ICON_DETAILS)
    edit.set_active(False)
    edit.close_via_x()
    edit.verify_modal_closed()

    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, td.CLOSE_ICON_NAME)
    _assert_details_modal(ctx, ctx.name)
    _assert_edit_values(ctx, ctx.name, details="", active=True)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_016_escape_closes_without_saving(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    ctx.edit.fill_network_name(td.ESCAPE_NAME)
    page.keyboard.press("Escape")
    ctx.edit.verify_modal_closed()

    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, td.ESCAPE_NAME)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_017_backdrop_click_never_saves(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    ctx.edit.fill_network_name(td.BACKDROP_NAME)
    page.mouse.click(10, 10)
    page.wait_for_timeout(500)

    # The modal may close or stay open by design - the change must never be saved.
    if ctx.edit.modal_heading.is_visible():
        ctx.edit.cancel()
        ctx.edit.verify_modal_closed()

    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, td.BACKDROP_NAME)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_018_cancel_discards_all_unsaved_edits(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    edit.fill_network_name(td.CANCEL_NAME)
    edit.fill_details(td.CANCEL_DETAILS)
    edit.add_polygon_vertex()          # 4 -> 5 vertices
    edit.set_active(False)
    edit.cancel()
    edit.verify_modal_closed()

    _expect_not_in_tree(ctx, td.CANCEL_NAME)
    _assert_edit_values(
        ctx, ctx.name, details="", active=True, vertices=td.POLYGON_VERTEX_COUNT
    )


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_019_close_without_changes_has_no_side_effects(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    ctx.edit.cancel()

    ctx.edit.verify_modal_closed()
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_020_reopen_after_cancel_shows_saved_values(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    ctx.edit.fill_network_name(td.DISCARDED_NAME)
    ctx.edit.fill_details(td.DISCARDED_DETAILS)
    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()

    _assert_edit_values(ctx, ctx.name, details="")


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_021_keyboard_tab_order(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)

    order = ctx.edit.focus_order()
    first_seen = [label for i, label in enumerate(order) if label not in order[:i]]

    for label in ("name", "details", "active", "cancel", "update"):
        assert label in first_seen, f"{label} never received focus. Order: {first_seen}"

    position = {label: first_seen.index(label) for label in first_seen}
    assert (
        position["name"]
        < position["details"]
        < position["active"]
        < position["cancel"]
        < position["update"]
    ), f"Unexpected tab order: {first_seen}"
    # Focus must stay inside the modal while tabbing.
    expect(ctx.edit.modal_heading).to_be_visible()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_022_enter_key_submits_form(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.ENTER_ORIGINAL)
    new_name = unique(td.ENTER_NEW)

    ctx.edit.fill_network_name(new_name)
    ctx.edit.press_enter_on_name()

    try:
        ctx.edit.verify_modal_closed()
    except AssertionError:
        ctx.edit.cancel()
        pytest.skip("Enter does not submit the form (by design) - note in Remarks.")

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_023_edit_button_activated_by_keyboard(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME, open_edit=False)
    edit_button = ctx.tree.edit_button

    ctx.tree.modal_heading.click()
    reached = False
    for _ in range(15):
        page.keyboard.press("Tab")
        if edit_button.evaluate("el => el === document.activeElement"):
            reached = True
            break
    assert reached, "Edit button was not reached with the Tab key"

    expect(edit_button).to_be_focused()
    page.keyboard.press("Enter")

    ctx.edit.verify_modal_open()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_024_layout_at_different_zoom_levels(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    for width, height in td.ZOOM_VIEWPORTS:
        page.set_viewport_size({"width": width, "height": height})
        edit.verify_modal_open()

        for control in (edit.network_name_input, edit.cancel_button, edit.update_button):
            control.scroll_into_view_if_needed()
            expect(control).to_be_visible()
            expect(control).to_be_in_viewport()

        box = edit.network_name_input.bounding_box()
        assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1, (
            f"Network Name field is cut off at {width}x{height}"
        )


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_025_details_textarea_resizes(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DEFAULT_EDIT_NAME)
    edit = ctx.edit

    edit.details_input.scroll_into_view_if_needed()
    before = edit.details_input.bounding_box()
    handle_x = before["x"] + before["width"] - 4
    handle_y = before["y"] + before["height"] - 4

    page.mouse.move(handle_x, handle_y)
    page.mouse.down()
    page.mouse.move(handle_x, handle_y + 60, steps=5)
    page.mouse.up()

    after = edit.details_input.bounding_box()
    assert after["height"] > before["height"], "Details textarea did not resize"

    for control in (edit.network_name_input, edit.cancel_button, edit.update_button):
        control.scroll_into_view_if_needed()
        expect(control).to_be_visible()


# ===========================================================================
# Functional (026 - 063)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_026_update_network_name_only(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.NAME_ONLY_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.NAME_ONLY_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)
    _assert_edit_values(
        ctx, new_name, details=td.DETAILS_ORIGINAL, active=True,
        vertices=td.POLYGON_VERTEX_COUNT,
    )


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_027_update_details_only(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.DETAILS_ONLY_ORIGINAL, details=td.DETAILS_ORIGINAL
    )

    _edit_and_save(ctx, details=td.DETAILS_ONLY_NEW)

    _expect_in_tree(ctx, ctx.name)
    _assert_edit_values(
        ctx, ctx.name, details=td.DETAILS_ONLY_NEW, active=True,
        vertices=td.POLYGON_VERTEX_COUNT,
    )


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_028_update_active_status_only(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.ACTIVE_ONLY_ORIGINAL, details=td.DETAILS_ORIGINAL
    )

    _edit_and_save(ctx, active=False)

    _open_details(ctx, ctx.name)
    expect(ctx.tree.status_badge(td.STATUS_INACTIVE)).to_be_visible()   # known issue
    _assert_edit_values(ctx, ctx.name, details=td.DETAILS_ORIGINAL, active=None)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_029_update_multiple_fields_together(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MULTI_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.MULTI_NEW)

    _edit_and_save(ctx, name=new_name, details=td.MULTI_DETAILS_NEW, active=False)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)
    _assert_edit_values(ctx, new_name, details=td.MULTI_DETAILS_NEW, active=False)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_030_edit_with_valid_name_succeeds(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.VALID_SAVE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.VALID_SAVE_NEW)

    _edit_and_save(ctx, name=new_name, details=td.VALID_SAVE_DETAILS)

    _expect_in_tree(ctx, new_name)
    _assert_details_modal(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_031_success_notification_displayed(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.NOTIFICATION_ORIGINAL, details=td.DETAILS_ORIGINAL)

    ctx.edit.fill_network_name(unique(td.NOTIFICATION_NEW))
    ctx.edit.update()

    expect(ctx.edit.success_toast).to_be_visible(timeout=5000)
    expect(ctx.edit.success_toast).to_be_hidden(timeout=15000)   # auto-dismisses


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_032_modal_closes_after_save(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MODAL_CLOSE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.MODAL_CLOSE_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_033_save_without_changes(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.NO_CHANGE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    edit = ctx.edit

    if edit.update_button.is_enabled():
        edit.update()
        edit.verify_modal_closed()
        expect(edit.duplicate_name_error).to_have_count(0)
    else:
        edit.verify_update_disabled()   # disabled until something changes
        edit.cancel()

    _expect_one_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_034_revert_to_original_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.REVERT_ORIGINAL,
        details=td.DETAILS_ORIGINAL
    )

    temp_name = unique(td.REVERT_TEMP)

    # Step 1: Rename the network and capture the API response.
    with page.expect_response(
        lambda response: (
            re.search(td.UPDATE_NETWORK_API_ROUTE_PATTERN, response.url)
            and response.request.method != "GET"
        ),
        timeout=15000
    ) as response_info:
        _edit_and_save(ctx, name=temp_name)

    response = response_info.value

    print(f"\nUpdate API Status: {response.status}")
    print(f"Update API URL: {response.url}")
    print(f"Update API Response: {response.text()}")

    assert response.ok, (
        f"Network update failed. HTTP Status: {response.status}"
    )

    # Step 2: Reload and verify the temporary name.
    _reload_coverage(ctx)

    print("\nNetwork rows after reload:")
    print(_network_row_texts(page))

    _expect_in_tree(ctx, temp_name)

    # Step 3: Reopen Edit Network using the temporary name.
    _reopen_edit(ctx, temp_name)

    # Step 4: Revert to the original name.
    _edit_and_save(ctx, name=ctx.name)

    # Step 5: Verify the final state.
    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, temp_name)

    _open_details(ctx, ctx.name)

    assert ctx.tree.opened_network_id == ctx.network_id, (
        "Network ID changed after reverting the network name"
    )


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_035_multiple_consecutive_edits(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.CONSECUTIVE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    names = [unique(name) for name in td.CONSECUTIVE_NAMES]

    current = ctx.name
    for new_name in names:
        if current != ctx.name:
            _reopen_edit(ctx, current)
        _edit_and_save(ctx, name=new_name)
        _expect_in_tree(ctx, new_name)
        current = new_name

    _expect_in_tree(ctx, names[-1])
    for old_name in [ctx.name, *names[:-1]]:
        _expect_not_in_tree(ctx, old_name)
    _assert_details_modal(ctx, names[-1])


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_036_reopen_edit_after_save_shows_saved_values(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.REOPEN_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.REOPEN_NEW)

    _edit_and_save(ctx, name=new_name, details=td.REOPEN_DETAILS_NEW, active=False)

    _assert_edit_values(ctx, new_name, details=td.REOPEN_DETAILS_NEW, active=False)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_037_minimum_length_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MIN_LENGTH_ORIGINAL, details=td.DETAILS_ORIGINAL)

    _edit_and_save(ctx, name=td.MIN_LENGTH_NEW)

    _expect_in_tree(ctx, td.MIN_LENGTH_NEW)
    _assert_details_modal(ctx, td.MIN_LENGTH_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_038_maximum_length_name_255(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MAX_255_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = _padded_name(td.MAX_255_FILLER * td.MAX_NAME_LENGTH, td.MAX_NAME_LENGTH)
    assert len(new_name) == td.MAX_NAME_LENGTH

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    _assert_details_modal(ctx, new_name)   # full value shown in Network Details


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_039_boundary_max_length_minus_one_254(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MAX_254_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = _padded_name(td.MAX_254_FILLER * td.MAX_254_LENGTH, td.MAX_254_LENGTH)
    assert len(new_name) == td.MAX_254_LENGTH

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_040_numeric_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.NUMERIC_ORIGINAL, details=td.DETAILS_ORIGINAL)

    _edit_and_save(ctx, name=td.NUMERIC_NEW)

    _expect_in_tree(ctx, td.NUMERIC_NEW)
    _assert_details_modal(ctx, td.NUMERIC_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_041_alphanumeric_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.ALPHANUMERIC_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.ALPHANUMERIC_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    _assert_details_modal(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_042_special_characters_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.SPECIAL_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.SPECIAL_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    expect(ctx.tree.network_rows(ctx.region_id, new_name).first).not_to_contain_text("&amp;")
    _assert_details_modal(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_043_unicode_nepali_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.UNICODE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.UNICODE_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    _assert_details_modal(ctx, new_name)

    _reload_coverage(ctx)
    _expect_in_tree(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_044_case_only_change(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.CASE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    upper_name = ctx.name.upper()

    _edit_and_save(ctx, name=upper_name)   # must not be blocked as duplicate of itself

    _expect_in_tree(ctx, upper_name)
    _assert_details_modal(ctx, upper_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_045_leading_trailing_spaces_trimmed(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.TRIM_ORIGINAL, details=td.DETAILS_ORIGINAL)
    trimmed = unique(td.TRIM_BASE)

    _edit_and_save(ctx, name=f" {trimmed} ")

    _expect_in_tree(ctx, trimmed)
    _assert_details_modal(ctx, trimmed)
    _assert_edit_values(ctx, trimmed, details=td.DETAILS_ORIGINAL)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_046_details_multiline_preserved(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MULTILINE_DETAILS_ORIGINAL)

    _edit_and_save(ctx, details=td.MULTILINE_DETAILS_NEW)

    _assert_edit_values(ctx, ctx.name, details=td.MULTILINE_DETAILS_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_047_details_special_and_unicode_characters(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.SPECIAL_DETAILS_ORIGINAL)

    _edit_and_save(ctx, details=td.SPECIAL_DETAILS_NEW)

    _assert_edit_values(ctx, ctx.name, details=td.SPECIAL_DETAILS_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_048_clear_existing_details(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.CLEAR_DETAILS_ORIGINAL, details=td.CLEAR_DETAILS_TEXT
    )

    _edit_and_save(ctx, details="")

    _assert_edit_values(ctx, ctx.name, details="")


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_049_update_button_loading_state(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.LOADING_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.LOADING_NEW)

    def _delay_update_only(route):
        if route.request.method != "GET":
            page.wait_for_timeout(td.LOADING_DELAY_MS)
        route.continue_()

    page.route(re.compile(td.UPDATE_NETWORK_API_ROUTE_PATTERN), _delay_update_only)

    ctx.edit.fill_network_name(new_name)
    ctx.edit.update()

    expect(ctx.edit.update_button).to_be_disabled(timeout=5000)
    expect(ctx.edit.update_button).to_contain_text(td.LOADING_BUTTON_TEXT, timeout=5000)

    ctx.edit.verify_modal_closed()
    _expect_in_tree(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_050_double_click_update_sends_one_request(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DOUBLE_CLICK_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.DOUBLE_CLICK_NEW)

    update_requests: list[str] = []
    page.on(
        "request",
        lambda request: update_requests.append(request.url)
        if request.method != "GET"
        and re.search(td.UPDATE_NETWORK_API_ROUTE_PATTERN, request.url)
        else None,
    )

    ctx.edit.fill_network_name(new_name)
    ctx.edit.update_button.dblclick()
    ctx.edit.verify_modal_closed()

    assert len(update_requests) == 1, f"Expected 1 update request, got {update_requests}"
    _expect_one_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)


# ===========================================================================
# Validation (050 - 079)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_051_empty_network_name_blocked(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.EMPTY_NAME_ORIGINAL, details=td.DETAILS_ORIGINAL)

    ctx.edit.clear_network_name()
    ctx.edit.update()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.name_required_error).to_be_visible(timeout=5000)
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_052_whitespace_only_name_blocked(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.WHITESPACE_NAME_ORIGINAL, details=td.DETAILS_ORIGINAL
    )

    ctx.edit.fill_network_name(td.WHITESPACE_NAME)
    ctx.edit.update()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.name_required_error).to_be_visible(timeout=5000)
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_053_validation_message_auto_clears(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.VALIDATION_CLEAR_ORIGINAL, details=td.DETAILS_ORIGINAL
    )

    ctx.edit.clear_network_name()
    ctx.edit.update()
    expect(ctx.edit.name_required_error).to_be_visible(timeout=5000)

    ctx.edit.fill_network_name(unique(td.VALIDATION_CLEAR_NEW))

    expect(ctx.edit.name_required_error).to_be_hidden(timeout=5000)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_054_name_exceeding_max_length_rejected(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.EXCEEDED_ORIGINAL, details=td.DETAILS_ORIGINAL)

    _assert_over_limit_rejected(ctx, td.OVER_MAX_NAME_K)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_055_pasted_long_name_truncated_or_rejected(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.PASTE_LONG_ORIGINAL, details=td.DETAILS_ORIGINAL)

    _assert_over_limit_rejected(ctx, td.PASTE_LONG_NAME)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_056_details_exceeding_max_length_rejected(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.LONG_DETAILS_ORIGINAL, details=td.DETAILS_ORIGINAL)
    edit = ctx.edit

    edit.fill_details(td.OVER_MAX_DETAILS)
    if len(edit.details_input.input_value()) < len(td.OVER_MAX_DETAILS):
        return  # field blocks typing beyond the limit

    edit.update()
    edit.verify_modal_open()
    expect(edit.details_too_long_error).to_be_visible(timeout=5000)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_057_duplicate_name_exact_match_blocked(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.DUP_EXACT_ORIGINAL,
        details=td.DETAILS_ORIGINAL,
        others=(NetSpec(td.DUP_EXACT_EXISTING),),
    )

    ctx.edit.fill_network_name(ctx.others[0])
    ctx.edit.update()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.duplicate_name_error).to_be_visible(timeout=5000)
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_058_duplicate_name_different_case_blocked(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.DUP_CASE_ORIGINAL,
        details=td.DETAILS_ORIGINAL,
        others=(NetSpec(td.DUP_CASE_EXISTING),),
    )

    ctx.edit.fill_network_name(ctx.others[0].lower())
    ctx.edit.update()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.duplicate_name_error).to_be_visible(timeout=5000)
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_059_duplicate_name_with_extra_spaces_blocked(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.DUP_SPACE_ORIGINAL,
        details=td.DETAILS_ORIGINAL,
        others=(NetSpec(td.DUP_SPACE_EXISTING),),
    )

    ctx.edit.fill_network_name(f" {ctx.others[0]} ")
    ctx.edit.update()

    ctx.edit.verify_modal_open()
    expect(ctx.edit.duplicate_name_error).to_be_visible(timeout=5000)
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_060_same_name_in_different_region_allowed(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.CROSS_REGION_ORIGINAL,
        details=td.DETAILS_ORIGINAL,
        others=(NetSpec(td.CROSS_REGION_EXISTING, region=td.OTHER_REGION_NAME),),
    )
    shared_name = ctx.others[0]

    _edit_and_save(ctx, name=shared_name)

    _expect_in_tree(ctx, shared_name)
    _expect_not_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_060_emoji_in_name_handled_gracefully(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.EMOJI_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.EMOJI_NEW)

    if _try_save(ctx, new_name):
        _expect_in_tree(ctx, new_name)
        _assert_details_modal(ctx, new_name)
    else:
        expect(ctx.edit.error_notification).to_be_visible()   # clear validation message


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_075_special_characters_only_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.SPECIAL_ONLY_ORIGINAL, details=td.DETAILS_ORIGINAL)

    _edit_and_save(ctx, name=td.SPECIAL_ONLY_NEW)

    _expect_in_tree(ctx, td.SPECIAL_ONLY_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_076_multiline_text_in_name_does_not_break_form(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.MULTILINE_NAME_ORIGINAL, details=td.DETAILS_ORIGINAL)
    edit = ctx.edit

    edit.fill_network_name(unique(td.MULTILINE_NAME_NEW))
    assert "\n" not in edit.network_name_input.input_value(), "Line break kept in the name"

    edit.update()
    try:
        edit.verify_modal_closed()
    except AssertionError:
        expect(edit.error_notification).to_be_visible()   # rejected with a message
        return

    _reload_coverage(ctx)   # tree is stale after save - read the real rows
    assert all("\n" not in text for text in _network_row_texts(page))


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_079_validation_failure_keeps_data_unchanged(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.VALIDATION_FAILURE_ORIGINAL, details=td.DETAILS_ORIGINAL
    )

    ctx.edit.clear_network_name()
    ctx.edit.update()
    expect(ctx.edit.name_required_error).to_be_visible(timeout=5000)

    ctx.edit.cancel()
    ctx.edit.verify_modal_closed()

    _expect_in_tree(ctx, ctx.name)
    _assert_edit_values(
        ctx, ctx.name, details=td.DETAILS_ORIGINAL, active=True,
        vertices=td.POLYGON_VERTEX_COUNT,
    )


# ===========================================================================
# Security (080 - 083)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_080_script_injection_in_name(
    page: Page, credentials: tuple[str, str]
):
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))

    ctx = _prepare(page, credentials, td.XSS_NAME_ORIGINAL, details=td.DETAILS_ORIGINAL)
    payload = f"{td.XSS_NAME_PAYLOAD}{unique('')}"

    if _try_save(ctx, payload):
        _expect_in_tree(ctx, payload)          # shown literally as plain text
        _assert_details_modal(ctx, payload)

    assert not dialogs, f"JavaScript dialog triggered - payload executed: {dialogs}"
    expect(page.locator("script", has_text="alert('test')")).to_have_count(0)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_081_html_script_injection_in_details(
    page: Page, credentials: tuple[str, str]
):
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))

    ctx = _prepare(page, credentials, td.XSS_DETAILS_ORIGINAL)

    _edit_and_save(ctx, details=td.XSS_DETAILS_PAYLOAD)

    _assert_edit_values(ctx, ctx.name, details=td.XSS_DETAILS_PAYLOAD)   # plain text
    _assert_details_modal(ctx, ctx.name)

    assert not dialogs, f"JavaScript dialog triggered - payload executed: {dialogs}"
    expect(page.locator("img[src='x']")).to_have_count(0)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_082_html_tags_in_name_rendered_as_text(
    page: Page, credentials: tuple[str, str]
):
    dialogs: list[str] = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))

    ctx = _prepare(page, credentials, td.HTML_NAME_ORIGINAL, details=td.DETAILS_ORIGINAL)
    payload = f"{td.HTML_NAME_PAYLOAD}{unique('')}"

    _edit_and_save(ctx, name=payload)

    _expect_in_tree(ctx, payload)
    _assert_details_modal(ctx, payload)

    assert not dialogs, f"JavaScript dialog triggered - payload executed: {dialogs}"
    expect(page.locator("b", has_text="Bold")).to_have_count(0)
    expect(page.locator("img[src='x']")).to_have_count(0)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_083_user_without_role_cannot_edit(
    page: Page,
    credentials: tuple[str, str],
    restricted_credentials: tuple[str, str],
):
    # Setup as admin, then switch to the restricted (no-role) user.
    ctx = _prepare(page, credentials, td.PERMISSION_ORIGINAL, open_edit=False)
    ctx.explorer.clear_session_data()
    _login_again(ctx, restricted_credentials)
    _open_details(ctx, ctx.name)

    try:
        expect(ctx.tree.edit_button).to_be_visible(timeout=5000)
    except AssertionError:
        return  # Edit is not offered to this user -> cannot edit
    if ctx.tree.edit_button.is_disabled():
        return

    ctx.tree.click_edit()
    ctx.edit.fill_network_name(unique(td.PERMISSION_NEW))
    ctx.edit.update()

    expect(ctx.edit.error_notification).to_be_visible(timeout=8000)
    ctx.edit.cancel()
    _expect_in_tree(ctx, ctx.name)


# ===========================================================================
# Error handling (085 - 093)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_085_update_without_internet(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.OFFLINE_ORIGINAL, details=td.DETAILS_ORIGINAL)
    ctx.edit.fill_network_name(td.OFFLINE_NEW)

    page.context.set_offline(True)
    try:
        ctx.edit.update()
        expect(ctx.edit.server_unreachable_error_toast).to_be_visible(timeout=10000)
        ctx.edit.verify_modal_open()
        ctx.edit.verify_network_name_value(td.OFFLINE_NEW)
    finally:
        page.context.set_offline(False)

    _expect_not_in_tree(ctx, td.OFFLINE_NEW)
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_086_server_error_500(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.SERVER_ERROR_ORIGINAL, details=td.DETAILS_ORIGINAL)

    def _fail_update_only(route):
        if route.request.method == "GET":
            route.continue_()
        else:
            route.fulfill(status=500, body="Internal Server Error")

    page.route(re.compile(td.UPDATE_NETWORK_API_ROUTE_PATTERN), _fail_update_only)

    ctx.edit.fill_network_name(td.SERVER_ERROR_NEW)
    ctx.edit.update()

    expect(ctx.edit.error_notification).to_be_visible(timeout=10000)
    ctx.edit.verify_modal_open()
    ctx.edit.verify_network_name_value(td.SERVER_ERROR_NEW)
    ctx.edit.verify_update_enabled()
    expect(page.get_by_text(td.RAW_SERVER_ERROR_PATTERN)).to_have_count(0)
    _expect_not_in_tree(ctx, td.SERVER_ERROR_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_087_slow_network_timeout(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.TIMEOUT_ORIGINAL, details=td.DETAILS_ORIGINAL)

    def _timeout_update_only(route):
        if route.request.method == "GET":
            route.continue_()
            return
        page.wait_for_timeout(td.TIMEOUT_DELAY_MS)
        route.abort("timedout")

    page.route(re.compile(td.UPDATE_NETWORK_API_ROUTE_PATTERN), _timeout_update_only)

    ctx.edit.fill_network_name(td.TIMEOUT_NEW)
    ctx.edit.update()

    expect(ctx.edit.update_button).to_contain_text(td.LOADING_BUTTON_TEXT, timeout=2000)
    expect(ctx.edit.error_notification).to_be_visible(timeout=15000)
    ctx.edit.verify_update_enabled()
    ctx.edit.verify_modal_open()
    _expect_not_in_tree(ctx, td.TIMEOUT_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_088_backend_validation_message_displayed(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.BACKEND_VALIDATION_ORIGINAL, details=td.DETAILS_ORIGINAL
    )

    def _reject_update_only(route):
        if route.request.method == "GET":
            route.continue_()
            return
        route.fulfill(
            status=422,
            content_type="application/json",
            body=(
                '{"message":"%s","errors":{"label":["%s"]}}'
                % (td.NETWORK_NAME_TOO_LONG, td.NETWORK_NAME_TOO_LONG)
            ),
        )

    page.route(re.compile(td.UPDATE_NETWORK_API_ROUTE_PATTERN), _reject_update_only)

    ctx.edit.fill_network_name(td.BACKEND_VALIDATION_NAME)
    ctx.edit.update()

    expect(ctx.edit.name_too_long_error).to_be_visible(timeout=5000)
    ctx.edit.verify_modal_open()
    ctx.edit.cancel()
    _expect_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_089_update_after_session_data_cleared(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.SESSION_CLEARED_ORIGINAL, details=td.DETAILS_ORIGINAL)

    ctx.edit.fill_network_name(td.SESSION_CLEARED_NEW)
    ctx.explorer.clear_session_data()
    ctx.edit.update()

    _expect_session_rejected(page, ctx.edit)

    _login_again(ctx, credentials)
    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, td.SESSION_CLEARED_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_090_update_with_expired_session(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.EXPIRED_SESSION_ORIGINAL, details=td.DETAILS_ORIGINAL)

    ctx.edit.fill_network_name(td.EXPIRED_SESSION_NEW)

    # Invalidate the token: keep the cookies but replace their values.
    cookies = page.context.cookies()
    page.context.clear_cookies()
    page.context.add_cookies([{**cookie, "value": "expired"} for cookie in cookies])

    ctx.edit.update()

    _expect_session_rejected(page, ctx.edit)

    page.context.clear_cookies()
    _login_again(ctx, credentials)
    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, td.EXPIRED_SESSION_NEW)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_091_page_refresh_discards_unsaved_changes(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.REFRESH_ORIGINAL, details=td.DETAILS_ORIGINAL)

    ctx.edit.fill_network_name(td.REFRESH_NEW)
    _reload_coverage(ctx)

    _expect_in_tree(ctx, ctx.name)
    _expect_not_in_tree(ctx, td.REFRESH_NEW)


@pytest.mark.edit_network
@pytest.mark.skip(
    reason="TODO: needs a second session that DELETES the network (no delete "
    "flow/endpoint available to automate yet); expected message 'Network not found.'"
)
def test_TC_EDIT_NETWORK_092_network_deleted_or_modified_while_editing(
    page: Page, credentials: tuple[str, str]
):
    pass


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_093_concurrent_edit_by_two_users(
    page: Page, browser, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.CONCURRENT_ORIGINAL, details=td.DETAILS_ORIGINAL)
    name_a = unique(td.CONCURRENT_NAME_A)
    name_b = unique(td.CONCURRENT_NAME_B)

    context_b, page_b, tree_b, edit_b = _second_session(browser, credentials)
    try:
        # User B opens Edit Network for the same network.
        tree_b.open_for_network(ctx.region, ctx.name)
        tree_b.click_edit()
        edit_b.verify_modal_open()

        # User A saves first, then User B saves.
        _edit_and_save(ctx, name=name_a)
        edit_b.fill_network_name(name_b)
        edit_b.update()
        page_b.wait_for_timeout(2000)

        # Refresh both sessions and compare the final state.
        final_states = []
        for session_page, session_tree in ((page, ctx.tree), (page_b, tree_b)):
            session_page.reload(wait_until="domcontentloaded")
            if session_page is page:
                ctx.explorer.verify_page_loaded()
                ctx.explorer.open_coverage_panel()
                ctx.explorer.verify_coverage_panel_open()
            else:
                explorer_b = NetworkExplorerPage(session_page)
                explorer_b.verify_page_loaded()
                explorer_b.open_coverage_panel()
                explorer_b.verify_coverage_panel_open()

            expect(session_tree.region_rows(ctx.region).first).to_be_visible(timeout=15000)
            region_id = session_tree.get_region_id(ctx.region)
            assert region_id == ctx.region_id, (
                f"Region ID changed in concurrent session. "
                f"Expected {ctx.region_id}, got {region_id}"
            )
            session_tree.expand_region(ctx.region)
            rows_a = session_tree.network_rows(region_id, name_a)
            rows_b = session_tree.network_rows(region_id, name_b)
            expect(rows_a.or_(rows_b).first).to_be_visible(timeout=15000)
            final_states.append((rows_a.count(), rows_b.count()))

        assert final_states[0] == final_states[1], f"Sessions disagree: {final_states}"
        assert sum(final_states[0]) == 1, f"Data corruption / duplicate rows: {final_states}"
    finally:
        context_b.close()


# ===========================================================================
# Hierarchy verification (094 - 104)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_094_hierarchy_reflects_update_immediately(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page, credentials, td.HIERARCHY_UPDATE_ORIGINAL, details=td.DETAILS_ORIGINAL
    )
    new_name = unique(td.HIERARCHY_UPDATE_NEW)

    _edit_and_save(ctx, name=new_name, details=td.HIERARCHY_UPDATE_DETAILS)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)
    _assert_details_modal(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_095_hierarchy_persists_after_refresh(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.REFRESH_PERSIST_ORIGINAL)
    new_name = unique(td.REFRESH_PERSIST_NEW)

    _edit_and_save(ctx, name=new_name)
    _reload_coverage(ctx)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_096_network_id_and_parent_region_unchanged(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.ID_UNCHANGED_ORIGINAL)
    new_name = unique(td.ID_UNCHANGED_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    assert ctx.tree.get_network_id(ctx.region_id, new_name) == ctx.network_id
    _expect_one_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_097_old_name_removed_from_hierarchy(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.OLD_REMOVED_ORIGINAL)
    new_name = unique(td.OLD_REMOVED_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)
    expect(page.get_by_text(ctx.name)).to_have_count(0)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_098_other_networks_unaffected(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(
        page,
        credentials,
        td.ISOLATION_ORIGINAL,
        others=(NetSpec(td.ISOLATION_OTHER, details=td.ISOLATION_OTHER_DETAILS),),
    )
    new_name = unique(td.ISOLATION_NEW)
    rows_before = set(_network_row_texts(page))

    _edit_and_save(ctx, name=new_name)
    _expect_in_tree(ctx, new_name)   # reloads (and re-expands the region) if the tree is stale
    rows_after = set(_network_row_texts(page))

    assert len(rows_before - rows_after) == 1, "More than one row disappeared"
    assert len(rows_after - rows_before) == 1, "More than one row appeared"
    assert any(new_name in row for row in rows_after - rows_before)
    _expect_in_tree(ctx, ctx.others[0])


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_099_long_name_displays_properly(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.LONG_DISPLAY_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = _padded_name(td.LONG_DISPLAY_BASE, td.LONG_DISPLAY_LENGTH)
    assert len(new_name) == td.LONG_DISPLAY_LENGTH

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    assert not page.evaluate(
        "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
    ), "Long name caused horizontal overflow"
    _open_details(ctx, new_name)
    expect(ctx.tree.label_value(new_name)).to_be_visible()   # complete name in details


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_100_special_characters_rendered_as_text(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.SPECIAL_DISPLAY_ORIGINAL, details=td.DETAILS_ORIGINAL)
    new_name = unique(td.SPECIAL_DISPLAY_NEW)

    _edit_and_save(ctx, name=new_name)

    _expect_in_tree(ctx, new_name)
    expect(ctx.tree.network_rows(ctx.region_id, new_name).first).not_to_contain_text("&amp;")


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_101_updated_name_visible_to_other_users(
    page: Page, browser, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.OTHER_USER_ORIGINAL)
    new_name = unique(td.OTHER_USER_NEW)
    _edit_and_save(ctx, name=new_name)

    context_b, page_b, tree_b, _ = _second_session(browser, credentials)
    try:
        expect(tree_b.region_rows(ctx.region).first).to_be_visible(timeout=15000)
        region_id = tree_b.get_region_id(ctx.region)
        assert region_id == ctx.region_id, (
            f"Region ID differs between sessions: {ctx.region_id} != {region_id}"
        )
        tree_b.expand_region(ctx.region)
        expect(tree_b.network_rows(region_id, new_name).first).to_be_visible(timeout=15000)
        expect(tree_b.network_rows(region_id, ctx.name)).to_have_count(0)
    finally:
        context_b.close()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_102_updated_name_persists_after_logout_login(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.LOGOUT_LOGIN_ORIGINAL)
    new_name = unique(td.LOGOUT_LOGIN_NEW)
    _edit_and_save(ctx, name=new_name)
    _close_details(ctx)

    nav_bar = NavBar(page)
    nav_bar.open_account_menu()
    nav_bar.click_sign_out()
    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)

    _login_again(ctx, credentials)

    _expect_in_tree(ctx, new_name)
    _expect_not_in_tree(ctx, ctx.name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_103_add_network_duplicate_check_uses_updated_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.ADD_DUPLICATE_ORIGINAL)
    new_name = unique(td.ADD_DUPLICATE_NEW)
    _edit_and_save(ctx, name=new_name)
    _close_details(ctx)

    add_network = AddNetworkModal(page)
    ctx.tree.open_add_network(ctx.region)
    add_network.verify_modal_open()
    add_network.fill_network_name(new_name)
    add_network.draw_coverage_polygon(td.POLYGON_POINTS)
    add_network.submit()

    # Known issue: duplicate validation currently fails in Add Network (ADD_NETWORK_046).
    add_network.verify_modal_open()
    expect(page.get_by_text(td.DUPLICATE_ERROR_PATTERN).first).to_be_visible(timeout=5000)
    add_network.cancel()

    _expect_one_in_tree(ctx, new_name)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_104_old_name_can_be_reused_after_rename(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.OLD_REUSE_ORIGINAL)
    old_name = ctx.name
    new_name = unique(td.OLD_REUSE_NEW)
    _edit_and_save(ctx, name=new_name)
    _close_details(ctx)

    add_network = AddNetworkModal(page)
    ctx.tree.open_add_network(ctx.region)
    add_network.verify_modal_open()
    add_network.fill_network_name(old_name)
    add_network.draw_coverage_polygon(td.POLYGON_POINTS)
    add_network.submit()
    add_network.verify_modal_closed()

    _reload_coverage(ctx)
    _expect_in_tree(ctx, old_name)
    _expect_in_tree(ctx, new_name)
    assert (
        ctx.tree.get_network_id(ctx.region_id, old_name)
        != ctx.tree.get_network_id(ctx.region_id, new_name)
    ), "Both networks must have different IDs"


# ===========================================================================
# Network Details verification (105 - 109)
# ===========================================================================
@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_105_network_details_shows_updated_name(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DETAILS_NAME_ORIGINAL)
    new_name = unique(td.DETAILS_NAME_NEW)

    _edit_and_save(ctx, name=new_name)
    _assert_details_modal(ctx, new_name)

    expect(ctx.tree.label_value(ctx.name)).to_have_count(0)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_106_network_id_unchanged_in_details(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DETAILS_ID_ORIGINAL)
    new_name = unique(td.DETAILS_ID_NEW)

    _edit_and_save(ctx, name=new_name)
    _open_details(ctx, new_name)

    expect(ctx.tree.id_value(ctx.network_id)).to_be_visible()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_107_path_updated_in_details(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DETAILS_PATH_ORIGINAL)
    new_name = unique(td.DETAILS_PATH_NEW)

    _edit_and_save(ctx, name=new_name)
    _open_details(ctx, new_name)

    expect(
        ctx.tree.path_text(ctx.region_id, ctx.region, ctx.network_id, new_name)
    ).to_be_visible()
    expect(
        ctx.tree.path_text(ctx.region_id, ctx.region, ctx.network_id, ctx.name)
    ).to_have_count(0)


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_108_details_text_shown_in_network_details(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.DETAILS_TEXT_ORIGINAL)

    _edit_and_save(ctx, details=td.DETAILS_TEXT_NEW)
    _open_details(ctx, ctx.name)

    # Known issue (Status FAIL in sheet): Details text is not rendered in Network Details.
    expect(page.get_by_text(td.DETAILS_TEXT_NEW, exact=True)).to_be_visible()


@pytest.mark.edit_network
def test_TC_EDIT_NETWORK_109_status_badge_matches_saved_active_state(
    page: Page, credentials: tuple[str, str]
):
    ctx = _prepare(page, credentials, td.STATUS_BADGE_ORIGINAL, details=td.DETAILS_ORIGINAL)

    _edit_and_save(ctx, active=False)
    _open_details(ctx, ctx.name)
    expect(ctx.tree.status_badge(td.STATUS_INACTIVE)).to_be_visible()   # known issue

    ctx.tree.click_edit()
    ctx.edit.verify_modal_open()
    _edit_and_save(ctx, active=True)
    _open_details(ctx, ctx.name)
    expect(ctx.tree.status_badge(td.STATUS_ACTIVE)).to_be_visible()