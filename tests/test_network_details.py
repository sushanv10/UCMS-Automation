"""
Network Details automation (TC_NETWORK_DETAILS_001 .. 027).

* Primary region "Region - Network_Details_Test" and network
  "Network_Details_Test" are created ONLY if missing (_ensure_region /
  _ensure_network), so re-runs never collide.
* Scenario-specific networks (Active, Inactive, Fresh, No polygon, etc.)
  use unique() so each run is isolated.
* All test data lives in test_data/network_details_test_data.py and matches
  the sheet Test Data column.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from modals.add_network_modal import AddNetworkModal
from modals.add_region_modal import AddRegionModal
from modals.network_details_modal import NetworkDetailsModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import network_details_test_data as td
from utils.helpers import unique

pytestmark = pytest.mark.network_details


# ---------------------------------------------------------------------------
# Shared context
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    """Shared objects available to each Network Details test."""
    page: Page
    explorer: NetworkExplorerPage
    tree: NetworkDetailsModal
    region: str
    network: str
    region_id: str = ""
    network_id: str = ""


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
def _login_and_open_coverage(
    page: Page,
    credentials: tuple[str, str],
) -> tuple[NetworkExplorerPage, NetworkDetailsModal]:
    """Log in and open the Coverage panel. Does NOT open any network."""
    login_page = LoginPage(page)
    explorer = NetworkExplorerPage(page)
    tree = NetworkDetailsModal(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()

    return explorer, tree


def _ensure_region(page: Page, tree: NetworkDetailsModal, name: str) -> None:
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


def _create_network(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    region_name: str,
    network_name: str,
    *,
    active: bool = True,
    with_polygon: bool = True,
) -> None:
    """Create a network under region_name via the region row's '+' control."""
    add_network = AddNetworkModal(page)

    tree.open_add_network(region_name)
    add_network.verify_modal_open()
    add_network.fill_network_name(network_name)
    add_network.set_active(active)
    if with_polygon:
        add_network.draw_coverage_polygon(td.POLYGON_POINTS)
    add_network.submit()
    add_network.verify_modal_closed()

    # Coverage tree only shows new networks after a reload.
    page.reload(wait_until="domcontentloaded")
    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()
    expect(tree.region_rows(region_name).first).to_be_visible(timeout=15000)


def _ensure_network(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    region_name: str,
    network_name: str,
    *,
    active: bool = True,
    with_polygon: bool = True,
) -> None:
    """
    Create the network under region_name ONLY if it is not already present.
    Region must already exist (call _ensure_region first).
    """
    region_id = tree.get_region_id(region_name)
    tree.expand_region(region_name)
    if tree.network_rows(region_id, network_name).count() == 0:
        _create_network(
            page,
            tree,
            explorer,
            region_name,
            network_name,
            active=active,
            with_polygon=with_polygon,
        )


def _ensure_primary(page: Page, tree: NetworkDetailsModal, explorer: NetworkExplorerPage) -> None:
    """Ensure primary region + network from the sheet exist."""
    _ensure_region(page, tree, td.PRIMARY_REGION_NAME)
    _ensure_network(
        page,
        tree,
        explorer,
        td.PRIMARY_REGION_NAME,
        td.PRIMARY_NETWORK_NAME,
        active=True,
        with_polygon=True,
    )


def _prepare(
    page: Page,
    credentials: tuple[str, str],
    *,
    open_details: bool = True,
    region: str = td.PRIMARY_REGION_NAME,
    network: str = td.PRIMARY_NETWORK_NAME,
    ensure_primary: bool = True,
) -> Ctx:
    """
    Login → open Coverage → ensure primary region/network (optional) →
    optionally open Network Details for `network`.
    """
    explorer, tree = _login_and_open_coverage(page, credentials)

    if ensure_primary:
        _ensure_primary(page, tree, explorer)

    region_id = ""
    network_id = ""
    if open_details:
        network_id = tree.open_for_network(region, network)
        region_id = tree.opened_region_id or tree.get_region_id(region)
    else:
        if tree.region_rows(region).count() > 0:
            region_id = tree.get_region_id(region)

    return Ctx(
        page=page,
        explorer=explorer,
        tree=tree,
        region=region,
        network=network,
        region_id=region_id,
        network_id=network_id,
    )


def _long_name(filler: str) -> str:
    """Unique name padded to exactly td.LONG_NAME_LENGTH characters."""
    suffix = unique("")
    body = filler * max(0, td.LONG_NAME_LENGTH - len(suffix))
    return (body + suffix)[: td.LONG_NAME_LENGTH]


# ---------------------------------------------------------------------------
# TC_001 – Modal displays correctly
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_001_modal_displays_correctly(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.tree.verify_modal_open()
    ctx.tree.verify_network_details(ctx.region, ctx.network)
    expect(ctx.tree.polygon_info).to_be_visible()


# ---------------------------------------------------------------------------
# TC_002 – Modal title
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_002_modal_title_displays_correctly(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.tree.modal_heading).to_have_text(td.MODAL_TITLE)
    expect(ctx.tree.close_icon).to_be_visible()


# ---------------------------------------------------------------------------
# TC_003 – Path breadcrumb format
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_003_path_breadcrumb_format(page, credentials):
    ctx = _prepare(page, credentials)

    expect(
        ctx.tree.path_text(
            ctx.tree.opened_region_id,
            ctx.region,
            ctx.tree.opened_network_id,
            ctx.network,
        )
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_004 – ID field accuracy and read-only
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_004_id_field_accuracy(page, credentials):
    ctx = _prepare(page, credentials)

    network_id = ctx.tree.opened_network_id
    id_value = ctx.tree.id_value(network_id)

    expect(ctx.tree.id_label).to_be_visible()
    expect(id_value).to_be_visible()

    ctx.tree.try_typing_into(id_value, td.ID_EDIT_TYPED)
    expect(id_value).to_have_text(network_id)
    ctx.tree.verify_no_editable_focus()


# ---------------------------------------------------------------------------
# TC_005 – Label field accuracy and read-only
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_005_label_field_accuracy(page, credentials):
    ctx = _prepare(page, credentials)

    label_value = ctx.tree.label_value(ctx.network)
    expect(ctx.tree.label_label).to_be_visible()
    expect(label_value).to_be_visible()

    ctx.tree.try_typing_into(label_value, td.LABEL_EDIT_TYPED)
    expect(label_value).to_have_text(ctx.network)
    ctx.tree.verify_no_editable_focus()


# ---------------------------------------------------------------------------
# TC_006 – Region field accuracy
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_006_region_field_accuracy(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.tree.region_label).to_be_visible()
    expect(ctx.tree.region_value(ctx.tree.opened_region_id)).to_be_visible()
    assert ctx.tree.opened_network_id.startswith(f"{ctx.tree.opened_region_id}-")


# ---------------------------------------------------------------------------
# TC_007 – Status badge Active
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_007_status_badge_active(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    name = unique(td.NAME_ACTIVE)
    _create_network(
        page, ctx.tree, ctx.explorer, ctx.region, name, active=True
    )
    ctx.tree.open_for_network(ctx.region, name)

    expect(ctx.tree.status_label).to_be_visible()
    expect(ctx.tree.status_badge(td.STATUS_ACTIVE)).to_be_visible()


# ---------------------------------------------------------------------------
# TC_008 – Status badge Inactive (known defect: may still show Active)
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_008_status_badge_inactive(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    name = unique(td.NAME_INACTIVE)
    _create_network(
        page, ctx.tree, ctx.explorer, ctx.region, name, active=False
    )
    ctx.tree.open_for_network(ctx.region, name)

    try:
        expect(ctx.tree.status_badge(td.STATUS_INACTIVE)).to_be_visible(timeout=5000)
    except AssertionError:
        pytest.xfail(
            "Known defect (sheet TC_008): network saved with Active unchecked "
            "still shows Active in Network Details."
        )


# ---------------------------------------------------------------------------
# TC_009 – Close via Close button
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_009_close_via_close_button(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.tree.close_via_button()
    ctx.tree.verify_modal_closed()
    expect(ctx.tree.region_rows(ctx.region).first).to_be_visible()
    expect(ctx.tree.network_rows(ctx.tree.opened_region_id, ctx.network).first).to_be_visible()


# ---------------------------------------------------------------------------
# TC_010 – Close via X icon
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_010_close_via_x_icon(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.tree.close_via_x()
    ctx.tree.verify_modal_closed()
    expect(ctx.tree.region_rows(ctx.region).first).to_be_visible()


# ---------------------------------------------------------------------------
# TC_011 – Edit button opens editable form
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_011_edit_button_opens_editable_form(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.tree.click_edit()
    ctx.tree.verify_edit_modal_open()
    # Pre-filled Network Name
    expect(ctx.tree.edit_network_name_input).to_have_value(ctx.network)


# ---------------------------------------------------------------------------
# TC_012 – Reopening details for a different network shows fresh data
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_012_fresh_data_for_second_network(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    fresh_name = unique(td.NAME_FRESH)
    _create_network(page, ctx.tree, ctx.explorer, ctx.region, fresh_name)

    # Open primary first
    id1 = ctx.tree.open_for_network(ctx.region, td.PRIMARY_NETWORK_NAME)
    expect(ctx.tree.label_value(td.PRIMARY_NETWORK_NAME)).to_be_visible()
    ctx.tree.close_via_button()
    ctx.tree.verify_modal_closed()

    # Open second network
    id2 = ctx.tree.open_for_network(ctx.region, fresh_name)
    expect(ctx.tree.label_value(fresh_name)).to_be_visible()
    expect(ctx.tree.id_value(id2)).to_be_visible()
    expect(ctx.tree.label_value(td.PRIMARY_NETWORK_NAME)).to_have_count(0)
    assert id1 != id2


# ---------------------------------------------------------------------------
# TC_013 – Details persist after page refresh
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_013_details_persist_after_refresh(page, credentials):
    ctx = _prepare(page, credentials)

    noted_id = ctx.tree.opened_network_id
    noted_region = ctx.tree.opened_region_id
    ctx.tree.close_via_button()
    ctx.tree.verify_modal_closed()

    ctx.page.reload(wait_until="domcontentloaded")
    ctx.explorer.verify_page_loaded()
    ctx.explorer.open_coverage_panel()
    ctx.explorer.verify_coverage_panel_open()

    ctx.tree.open_for_network(ctx.region, ctx.network)
    expect(ctx.tree.id_value(noted_id)).to_be_visible()
    expect(ctx.tree.label_value(ctx.network)).to_be_visible()
    expect(ctx.tree.region_value(noted_region)).to_be_visible()
    expect(ctx.tree.status_badge(td.STATUS_ACTIVE)).to_be_visible()


# ---------------------------------------------------------------------------
# TC_014 – Fields are read-only in view mode
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_014_fields_read_only_in_view_mode(page, credentials):
    ctx = _prepare(page, credentials)

    fields = (
        ctx.tree.id_value(ctx.tree.opened_network_id),
        ctx.tree.label_value(ctx.network),
        ctx.tree.region_value(ctx.tree.opened_region_id),
        ctx.tree.status_badge(td.STATUS_ACTIVE),
    )
    for field in fields:
        ctx.tree.try_typing_into(field, td.READ_ONLY_TYPED_INPUT)

    ctx.tree.verify_no_editable_focus()
    ctx.tree.verify_network_details(ctx.region, ctx.network)
    expect(ctx.tree.edit_button).to_be_visible()


# ---------------------------------------------------------------------------
# TC_015 – Error when details fail to load
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_015_error_when_details_fail_to_load(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    ctx.tree.expand_region(ctx.region)

    try:
        page.context.set_offline(True)
        ctx.tree.open_for_network(
            ctx.region, ctx.network, wait_for_modal=False
        )
        expect(
            page.get_by_text(re.compile(td.LOAD_ERROR_PATTERN, re.IGNORECASE))
        ).to_be_visible(timeout=15000)
    finally:
        page.context.set_offline(False)


# ---------------------------------------------------------------------------
# TC_016 – Session expiry while modal is open
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_016_session_expiry_while_open(page, credentials):
    ctx = _prepare(page, credentials)

    ctx.explorer.clear_session_data()
    page.reload()
    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)


# ---------------------------------------------------------------------------
# TC_017 – Network deleted in another session (needs second browser)
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="TODO: needs a second browser session that deletes a network")
def test_TC_NETWORK_DETAILS_017_network_deleted_in_another_session(page, credentials):
    pass


# ---------------------------------------------------------------------------
# TC_018 – Long names do not break layout
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_018_long_names_do_not_break_layout(page, credentials):
    ctx = _prepare(page, credentials, open_details=False, ensure_primary=False)

    long_region = _long_name(td.LONG_REGION_FILLER)
    long_network = _long_name(td.LONG_NETWORK_FILLER)
    assert len(long_region) == td.LONG_NAME_LENGTH
    assert len(long_network) == td.LONG_NAME_LENGTH

    _ensure_region(page, ctx.tree, long_region)
    _create_network(page, ctx.tree, ctx.explorer, long_region, long_network)
    ctx.tree.open_for_network(long_region, long_network)

    path = ctx.tree.path_text(
        ctx.tree.opened_region_id,
        long_region,
        ctx.tree.opened_network_id,
        long_network,
    )
    label = ctx.tree.label_value(long_network)
    ctx.tree.verify_long_path_fits(path, label)
    expect(ctx.tree.close_icon).to_be_visible()
    expect(ctx.tree.edit_button).to_be_visible()
    expect(ctx.tree.close_button).to_be_visible()


# ---------------------------------------------------------------------------
# TC_019 – No coverage polygon message
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_019_no_coverage_polygon_message(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    name = unique(td.NAME_NO_POLYGON)
    _create_network(
        page, ctx.tree, ctx.explorer, ctx.region, name, with_polygon=False
    )
    ctx.tree.open_for_network(ctx.region, name)

    expect(ctx.tree.no_polygon_message).to_be_visible()
    expect(ctx.tree.polygon_shapes).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_020 – Parent region renamed
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="TODO: needs Edit Region flow fully wired for rename")
def test_TC_NETWORK_DETAILS_020_parent_region_renamed(page, credentials):
    pass


# ---------------------------------------------------------------------------
# TC_021 – Coverage polygon display
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_021_coverage_polygon_displayed(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    name = unique(td.NAME_POLYGON)
    _create_network(
        page, ctx.tree, ctx.explorer, ctx.region, name, with_polygon=True
    )
    ctx.tree.open_for_network(ctx.region, name)

    expect(ctx.tree.polygon_info).to_be_visible()
    expect(ctx.tree.polygon_shapes.first).to_be_visible()
    expect(ctx.tree.no_polygon_message).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_022 – Map controls in view mode
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_022_map_controls_in_view_mode(page, credentials):
    ctx = _prepare(page, credentials)

    shapes_before = ctx.tree.polygon_shapes.count()
    info_before = ctx.tree.polygon_info.text_content()
    start_zoom = ctx.tree.current_zoom()

    ctx.tree.zoom_in(times=2)
    ctx.tree.verify_zoom_level(start_zoom + 2)

    ctx.tree.zoom_out(times=2)
    ctx.tree.verify_zoom_level(start_zoom)

    ctx.tree.click_map_center()
    assert ctx.tree.polygon_shapes.count() == shapes_before
    expect(ctx.tree.polygon_info).to_have_text(info_before)


# ---------------------------------------------------------------------------
# TC_023 – Modal buttons displayed
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_023_modal_buttons_displayed(page, credentials):
    ctx = _prepare(page, credentials)

    expect(ctx.tree.edit_button).to_be_visible()
    expect(ctx.tree.edit_button).to_be_enabled()
    expect(ctx.tree.close_button).to_be_visible()
    expect(ctx.tree.close_button).to_be_enabled()


# ---------------------------------------------------------------------------
# TC_024 – Unicode network name
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_024_unicode_network_name(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    name = unique(td.NAME_UNICODE)
    _create_network(page, ctx.tree, ctx.explorer, ctx.region, name)
    ctx.tree.open_for_network(ctx.region, name)

    expect(ctx.tree.label_value(name)).to_be_visible()
    ctx.tree.verify_network_details(ctx.region, name)


# ---------------------------------------------------------------------------
# TC_025 – HTML/script characters displayed as plain text
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_025_html_network_name_is_plain_text(page, credentials):
    dialogs: list[str] = []
    page.on(
        "dialog",
        lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()),
    )

    ctx = _prepare(page, credentials, open_details=False)
    name = unique(td.NAME_HTML_XSS)
    _create_network(page, ctx.tree, ctx.explorer, ctx.region, name)
    ctx.tree.open_for_network(ctx.region, name)

    expect(ctx.tree.label_value(name)).to_be_visible()
    expect(page.locator("b", has_text="XSS Test")).to_have_count(0)
    assert not dialogs, "A JS dialog fired – HTML was NOT sanitized."


# ---------------------------------------------------------------------------
# TC_026 – Open details repeatedly
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_026_open_and_close_repeatedly(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)

    for _ in range(td.REPEAT_COUNT):
        ctx.tree.open_for_network(ctx.region, ctx.network)
        expect(ctx.tree.modal_heading).to_have_count(1)
        expect(ctx.tree.label_value(ctx.network)).to_be_visible()
        ctx.tree.close_via_button()
        ctx.tree.verify_modal_closed()

    ctx.tree.open_for_network(ctx.region, ctx.network)
    expect(ctx.tree.modal_heading).to_have_count(1)
    expect(ctx.tree.id_value(ctx.tree.opened_network_id)).to_be_visible()
    expect(ctx.tree.label_value(ctx.network)).to_be_visible()


# ---------------------------------------------------------------------------
# TC_027 – Close via Escape key
# ---------------------------------------------------------------------------
def test_TC_NETWORK_DETAILS_027_close_via_escape_key(page, credentials):
    ctx = _prepare(page, credentials)

    page.keyboard.press("Escape")
    ctx.tree.verify_modal_closed()
    expect(
        ctx.tree.network_rows(ctx.tree.opened_region_id, ctx.network).first
    ).to_be_visible()
