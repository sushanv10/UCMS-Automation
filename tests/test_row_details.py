"""
Row Details automation (TC_ROWDETAILS_001 .. 041) - follows the test case sheet.

* Region "Region-Row_Details_Test", network "Network-Row_Details_Test" and
  primary row "Row_Details_Test" are created ONLY if missing.
* Scenario rows / networks / regions use the fixed sheet names and are also
  ensure-only (created only if missing).
* TC_025, TC_026 and TC_035 need a delete flow / a second session and are skipped.
* TC_012 asserts the real expected result (Inactive badge). It fails while the
  product shows Active for an inactive row (sheet status: FAILS).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, expect

from modals.add_network_modal import AddNetworkModal
from modals.add_region_modal import AddRegionModal
from modals.add_row_modal import AddRowModal
from modals.network_details_modal import NetworkDetailsModal
from modals.row_details_modal import RowDetailsModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import row_details_test_data as td
from utils.helpers import unique  # noqa: F401  (kept for other suites / compatibility)

pytestmark = pytest.mark.row_details


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    page: Page
    explorer: NetworkExplorerPage
    tree: NetworkDetailsModal
    details: RowDetailsModal
    region: str
    network: str
    row: str
    region_id: str = ""
    network_id: str = ""
    row_id: str = ""


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------
def _login_and_open_coverage(page: Page, credentials: tuple[str, str]):
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
    expect(
        page.locator("button").filter(has_text=re.compile(r"^Region:\s")).first
    ).to_be_visible(timeout=15000)
    page.wait_for_load_state("networkidle")  # let the tree finish loading
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
) -> None:
    add_network = AddNetworkModal(page)
    tree.open_add_network(region_name)
    add_network.verify_modal_open()
    add_network.fill_network_name(network_name)
    add_network.set_active(active)
    add_network.draw_coverage_polygon(td.NETWORK_POLYGON_POINTS)
    add_network.submit()
    add_network.verify_modal_closed()

    page.reload(wait_until="domcontentloaded")
    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()
    expect(tree.region_rows(region_name).first).to_be_visible(timeout=15000)
    tree.expand_region(region_name)  # reload collapses the tree, so re-expand
    region_id = tree.get_region_id(region_name)
    expect(tree.network_rows(region_id, network_name).first).to_be_visible(
        timeout=15000
    )


def _ensure_network(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    region_name: str,
    network_name: str,
    *,
    active: bool = True,
) -> None:
    _ensure_region(page, tree, region_name)
    region_id = tree.get_region_id(region_name)
    tree.expand_region(region_name)
    if tree.network_rows(region_id, network_name).count() == 0:
        _create_network(
            page, tree, explorer, region_name, network_name, active=active
        )


def _create_row(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    region_name: str,
    network_name: str,
    row_name: str,
    *,
    active: bool = True,
    polygon_points: list[tuple[float, float]] | None = None,
    typed_name: str | None = None,
    details: str | None = None,
    remarks: str | None = None,
) -> None:
    """
    typed_name: text typed in Row Name when it differs from the saved name
                (e.g. leading/trailing spaces that the system trims).
    details / remarks: optional text for the Details and Remarks fields.
    """
    add_row = AddRowModal(page)
    network_id = tree.open_add_row(region_name, network_name)
    add_row.verify_modal_open()
    add_row.fill_row_name(typed_name if typed_name is not None else row_name)
    if details is not None:
        page.get_by_label(re.compile(r"^Details")).fill(details)
    if remarks is not None:
        page.get_by_label(re.compile(r"^Remarks")).fill(remarks)
    add_row.set_active(active)
    if polygon_points:
        add_row.draw_coverage_polygon(polygon_points)
    add_row.submit()
    add_row.verify_modal_closed()

    page.reload(wait_until="domcontentloaded")
    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()
    expect(tree.region_rows(region_name).first).to_be_visible(timeout=15000)
    region_id = tree.get_region_id(region_name)
    tree.expand_region(region_name)
    tree.expand_network(region_id, network_name)
    expect(tree.row_rows(network_id, row_name).first).to_be_visible(timeout=15000)


def _ensure_row(
    page: Page,
    tree: NetworkDetailsModal,
    explorer: NetworkExplorerPage,
    region_name: str,
    network_name: str,
    row_name: str,
    *,
    active: bool = True,
    polygon_points: list[tuple[float, float]] | None = None,
    typed_name: str | None = None,
    details: str | None = None,
    remarks: str | None = None,
) -> None:
    """Create the row under the network ONLY if it is not already present."""
    _ensure_network(page, tree, explorer, region_name, network_name)
    region_id = tree.get_region_id(region_name)
    tree.expand_region(region_name)  # expand BEFORE reading the network ID
    network_id = tree.get_network_id(region_id, network_name)
    tree.expand_network(region_id, network_name)
    if tree.row_rows(network_id, row_name).count() == 0:
        _create_row(
            page,
            tree,
            explorer,
            region_name,
            network_name,
            row_name,
            active=active,
            polygon_points=polygon_points,
            typed_name=typed_name,
            details=details,
            remarks=remarks,
        )


def _ensure_primary(page: Page, tree: NetworkDetailsModal, explorer: NetworkExplorerPage):
    """Region + network + primary row (no polygon) from the sheet."""
    _ensure_row(
        page,
        tree,
        explorer,
        td.REGION_NAME,
        td.NETWORK_NAME,
        td.PRIMARY_ROW_NAME,
        active=True,
        polygon_points=None,
    )


def _prepare(
    page: Page,
    credentials: tuple[str, str],
    *,
    open_details: bool = True,
    row_name: str = td.PRIMARY_ROW_NAME,
    network_name: str = td.NETWORK_NAME,
    region_name: str = td.REGION_NAME,
    ensure_primary: bool = True,
    ensure_row: bool = True,
    row_active: bool = True,
    polygon_points: list[tuple[float, float]] | None = None,
    typed_row_name: str | None = None,
    row_details: str | None = None,
    row_remarks: str | None = None,
) -> Ctx:
    explorer, tree = _login_and_open_coverage(page, credentials)
    details = RowDetailsModal(page)

    if ensure_primary:
        _ensure_primary(page, tree, explorer)

    if ensure_row and row_name != td.PRIMARY_ROW_NAME:
        _ensure_row(
            page,
            tree,
            explorer,
            region_name,
            network_name,
            row_name,
            active=row_active,
            polygon_points=polygon_points,
            typed_name=typed_row_name,
            details=row_details,
            remarks=row_remarks,
        )

    region_id = tree.get_region_id(region_name)
    network_id = tree.get_network_id(region_id, network_name)
    row_id = ""

    if open_details:
        row_id = tree.open_for_row(region_name, network_name, row_name)
        details.verify_modal_open()
        details.opened_region_id = tree.opened_region_id
        details.opened_network_id = tree.opened_network_id
        details.opened_row_id = tree.opened_row_id
    else:
        tree.expand_region(region_name)
        tree.expand_network(region_id, network_name)
        if tree.row_rows(network_id, row_name).count() > 0:
            row_id = tree.get_row_id(network_id, row_name)

    return Ctx(
        page=page,
        explorer=explorer,
        tree=tree,
        details=details,
        region=region_name,
        network=network_name,
        row=row_name,
        region_id=region_id,
        network_id=network_id,
        row_id=row_id or (tree.opened_row_id or ""),
    )


def _assert_row_still_listed(ctx: Ctx):
    """The row is still in the Coverage tree with the same ID and name (no data altered)."""
    row_btn = ctx.tree.row_rows(ctx.network_id, ctx.row).first
    expect(row_btn).to_be_visible()
    expect(row_btn).to_contain_text(ctx.row_id)
    expect(row_btn).to_contain_text(ctx.row)


def _polygon_width(d: RowDetailsModal) -> float:
    return d.polygon_box()["width"]


# ===========================================================================
# TC_001 – TC_010  Modal open, close, path, ID, Label, Network
# ===========================================================================
def test_TC_ROWDETAILS_001_modal_opens_from_row_label(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    d.verify_modal_open()
    d.verify_overlay_dims_page()          # opens over a dimmed page
    d.verify_fields_visible()             # Path, ID, Label, Network, Status, map, Edit, Close
    d.verify_no_polygon()                 # "No coverage polygon defined." below the map


def test_TC_ROWDETAILS_002_modal_title(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    expect(d.modal_heading).to_have_text(td.MODAL_TITLE)  # exactly "Row Details"
    expect(d.close_icon).to_be_visible()

    weight = d.modal_heading.evaluate("el => getComputedStyle(el).fontWeight")
    assert weight == "bold" or int(weight) >= 600, f"Heading is not bold ({weight})"

    modal = d.modal_container.first.bounding_box()
    heading = d.modal_heading.bounding_box()
    close = d.close_icon.bounding_box()
    assert modal and heading and close
    middle = modal["x"] + modal["width"] / 2
    top_band = modal["y"] + modal["height"] * 0.25
    assert heading["x"] < middle and heading["y"] < top_band, "Title is not at the top-left"
    assert close["x"] > middle and close["y"] < top_band, "X icon is not at the top-right"


def test_TC_ROWDETAILS_003_close_via_x(page, credentials):
    ctx = _prepare(page, credentials)
    ctx.details.close_via_x()
    ctx.details.verify_modal_closed()
    ctx.explorer.verify_coverage_panel_open()
    _assert_row_still_listed(ctx)


def test_TC_ROWDETAILS_004_escape_closes(page, credentials):
    ctx = _prepare(page, credentials)
    page.keyboard.press("Escape")
    ctx.details.verify_modal_closed()
    ctx.explorer.verify_coverage_panel_open()
    _assert_row_still_listed(ctx)


def test_TC_ROWDETAILS_005_close_button(page, credentials):
    ctx = _prepare(page, credentials)
    ctx.details.close_via_button()
    ctx.details.verify_modal_closed()
    ctx.explorer.verify_coverage_panel_open()
    _assert_row_still_listed(ctx)


def test_TC_ROWDETAILS_006_path_breadcrumb(page, credentials):
    ctx = _prepare(page, credentials)
    expect(
        ctx.details.path_text(
            ctx.region_id,
            ctx.region,
            ctx.network_id,
            ctx.network,
            ctx.row_id,
            ctx.row,
        )
    ).to_be_visible()
    assert ctx.network_id.startswith(f"{ctx.region_id}-")
    assert ctx.row_id.startswith(f"{ctx.network_id}-R")


def test_TC_ROWDETAILS_007_path_matches_clicked_row(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    _ensure_row(page, ctx.tree, ctx.explorer, ctx.region, ctx.network, td.ROW_PATH_1)
    _ensure_row(page, ctx.tree, ctx.explorer, ctx.region, ctx.network, td.ROW_PATH_2)

    row_id_1 = ctx.tree.get_row_id(ctx.network_id, td.ROW_PATH_1)
    row_id_2 = ctx.tree.open_for_row(ctx.region, ctx.network, td.ROW_PATH_2)
    d = ctx.details
    d.verify_modal_open()
    d.verify_row_details(
        ctx.region_id,
        ctx.region,
        ctx.network_id,
        ctx.network,
        row_id_2,
        td.ROW_PATH_2,
        status=td.STATUS_ACTIVE,
    )
    # nothing of the sibling row 1 appears in the modal
    expect(d.label_value(td.ROW_PATH_1)).to_have_count(0)
    expect(d.modal_container).not_to_contain_text(td.ROW_PATH_1)
    expect(d.modal_container).not_to_contain_text(row_id_1)


def test_TC_ROWDETAILS_008_id_field(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    id_el = d.id_value(ctx.row_id)
    expect(id_el).to_be_visible()
    # ID equals the tree row ID and has the format "<Network ID>-R##"
    assert id_el.first.text_content().strip() == ctx.row_id
    assert re.fullmatch(rf"{re.escape(ctx.network_id)}-R\d+", ctx.row_id), (
        f"Row ID {ctx.row_id!r} is not '<Network ID>-R##'"
    )
    # ... and equals the row ID at the end of the Path line
    expect(
        d.path_text(
            ctx.region_id, ctx.region, ctx.network_id, ctx.network, ctx.row_id, ctx.row
        )
    ).to_be_visible()


def test_TC_ROWDETAILS_009_label_field(page, credentials):
    ctx = _prepare(page, credentials)
    label = ctx.details.label_value(td.PRIMARY_ROW_NAME)
    expect(label).to_be_visible()
    # exact text: no truncation, no leading / trailing whitespace
    assert label.first.text_content() == td.PRIMARY_ROW_NAME


def test_TC_ROWDETAILS_010_network_field(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    net = d.network_value(ctx.network_id)
    expect(net).to_be_visible()
    # the ID only, not the network name
    assert net.first.text_content().strip() == ctx.network_id
    expect(d.network_value(ctx.network)).to_have_count(0)
    # same as the network part of the row ID and of the Path line
    assert ctx.row_id.startswith(f"{ctx.network_id}-R")
    expect(d.path_label).to_contain_text(f"{ctx.network_id} - {ctx.network}")


# ===========================================================================
# TC_011 – TC_012  Status badge
# ===========================================================================
def test_TC_ROWDETAILS_011_status_active(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_ACTIVE,
        ensure_row=True,
        row_active=True,
    )
    expect(ctx.details.status_badge(td.STATUS_ACTIVE)).to_be_visible()


def test_TC_ROWDETAILS_012_status_inactive(page, credentials):
    # Row "Row_Details_Inactive_Test" is created with Active UNCHECKED.
    # Expected: badge reads "Inactive". (Known product bug: shows "Active" -> test fails.)
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_INACTIVE,
        ensure_row=True,
        row_active=False,
    )
    d = ctx.details
    expect(d.label_value(td.ROW_INACTIVE)).to_be_visible()
    expect(d.status_badge(td.STATUS_INACTIVE)).to_be_visible(timeout=5000)
    expect(d.status_badge(td.STATUS_ACTIVE)).to_have_count(0)


# ===========================================================================
# TC_013 – TC_018  Coverage area map
# ===========================================================================
def test_TC_ROWDETAILS_013_polygon_rendered(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_POLYGON,
        ensure_row=True,
        polygon_points=td.ROW_POLYGON_POINTS,
    )
    d = ctx.details
    expect(d.polygon_shapes.first).to_be_visible(timeout=10000)
    assert d.polygon_vertex_count() == td.ROW_POLYGON_VERTEX_COUNT, (
        f"Expected a triangle, found {d.polygon_vertex_count()} corners"
    )
    d.verify_polygon_inside_map()
    expect(d.no_polygon_message).to_have_count(0)


def test_TC_ROWDETAILS_014_vertex_caption_3(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_POLYGON,
        ensure_row=True,
        polygon_points=td.ROW_POLYGON_POINTS,
    )
    ctx.details.verify_caption(3)


def test_TC_ROWDETAILS_015_vertex_caption_50(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_FIFTY,
        ensure_row=True,
        polygon_points=td.FIFTY_POLYGON_POINTS,
    )
    d = ctx.details
    print("captions:", page.get_by_text(re.compile(td.POLYGON_INFO_PATTERN, re.I)).all_inner_texts())
    print("no-polygon msg:", d.no_polygon_message.count(), "| shapes:", d.polygon_shapes.count())
    d.verify_caption(td.FIFTY_VERTEX_COUNT)
    expect(d.polygon_shapes.first).to_be_visible(timeout=10000)
    d.verify_polygon_inside_map()


def test_TC_ROWDETAILS_016_map_is_read_only(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_POLYGON,
        ensure_row=True,
        polygon_points=td.ROW_POLYGON_POINTS,
    )
    d = ctx.details
    d.verify_caption(3)
    d_before = d.polygon_path_d()
    count_before = d.polygon_shapes.count()
    box = d.polygon_box()
    map_box = d.map_container.bounding_box()
    assert map_box

    # 1. click once on an empty spot ~20 px above the polygon
    x_above = box["x"] + box["width"] / 2
    y_above = max(map_box["y"] + 3, box["y"] - 20)
    page.mouse.click(x_above, y_above)
    page.wait_for_timeout(300)

    # 2. drag the top-left corner 50 px to the right
    cx, cy = box["x"] + 1, box["y"] + 1
    page.mouse.move(cx, cy)
    page.mouse.down()
    page.mouse.move(cx + 50, cy, steps=10)
    page.mouse.up()
    page.wait_for_timeout(300)

    # 3. right-click the same corner
    page.mouse.click(cx, cy, button="right")
    page.wait_for_timeout(300)

    # 4. nothing changed
    d.verify_modal_open()
    assert d.polygon_shapes.count() == count_before, "A shape was added or removed"
    assert d.polygon_path_d() == d_before, "The polygon geometry changed"
    assert d.polygon_vertex_count() == 3
    d.verify_caption(3)


def test_TC_ROWDETAILS_017_zoom_controls(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_POLYGON,
        ensure_row=True,
        polygon_points=td.ROW_POLYGON_POINTS,
    )
    d = ctx.details
    w0 = _polygon_width(d)
    already_max = "leaflet-disabled" in (d.zoom_in_button.get_attribute("class") or "")

    # 1. zoom in x3 with the "+" button
    for _ in range(3):
        d.zoom_in_button.click()
        page.wait_for_timeout(500)
    w_in = _polygon_width(d)
    assert w_in > w0 or already_max, "Zoom in button did not zoom the map in"

    # 2. zoom out x3 with the "-" button
    for _ in range(3):
        d.zoom_out_button.click()
        page.wait_for_timeout(500)
    w_out = _polygon_width(d)
    assert w_out < w_in, "Zoom out button did not zoom the map out"

    # 3. mouse wheel up x3 over the map
    box = d.map_container.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    for _ in range(3):
        page.mouse.wheel(0, -120)
        page.wait_for_timeout(500)
    w_wheel_in = _polygon_width(d)
    assert w_wheel_in > w_out, "Mouse wheel up did not zoom the map in"

    # 4. mouse wheel down x3
    for _ in range(3):
        page.mouse.wheel(0, 120)
        page.wait_for_timeout(500)
    w_wheel_out = _polygon_width(d)
    assert w_wheel_out < w_wheel_in, "Mouse wheel down did not zoom the map out"

    # 5. polygon shape and caption unchanged
    assert d.polygon_vertex_count() == 3
    d.verify_caption(3)


def test_TC_ROWDETAILS_018_map_attribution(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    expect(d.attribution).to_be_visible()
    text = d.attribution.inner_text()
    assert re.search(td.ATTRIBUTION_PATTERN, text), (
        f"Unexpected attribution text: {text!r}"
    )
    leaflet_href = d.attribution.locator("a", has_text="Leaflet").first.get_attribute("href")
    osm_href = d.attribution.locator("a", has_text="OpenStreetMap").first.get_attribute("href")
    assert td.LEAFLET_HREF in (leaflet_href or ""), f"Leaflet link: {leaflet_href!r}"
    assert td.OSM_HREF in (osm_href or ""), f"OpenStreetMap link: {osm_href!r}"


# ===========================================================================
# TC_019 – TC_021  Edit hand-off, safe rendering, trimming
# ===========================================================================
def test_TC_ROWDETAILS_019_edit_opens_prefilled_form(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    d.click_edit()
    d.verify_edit_modal_open()
    expect(d.edit_row_name_input).to_have_value(td.PRIMARY_ROW_NAME)
    expect(d.edit_details_input).to_have_value("")
    expect(d.edit_remarks_input).to_have_value("")
    expect(d.edit_active_checkbox).to_be_checked()
    # fields are editable
    expect(d.edit_row_name_input).to_be_editable()
    expect(d.edit_details_input).to_be_editable()
    expect(d.edit_remarks_input).to_be_editable()
    expect(d.edit_active_checkbox).to_be_enabled()


def test_TC_ROWDETAILS_020_script_payload_rendered_as_text(page, credentials):
    dialogs: list[str] = []

    def _on_dialog(dialog):
        dialogs.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", _on_dialog)

    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_SCRIPT,
        ensure_row=True,
    )
    d = ctx.details
    page.wait_for_timeout(500)

    # Path and Label show the payload as visible plain text
    expect(
        d.path_text(
            ctx.region_id, ctx.region, ctx.network_id, ctx.network, ctx.row_id, td.ROW_SCRIPT
        )
    ).to_be_visible()
    label = d.label_value_in_modal(td.ROW_SCRIPT)
    expect(label).to_be_visible()
    assert label.first.text_content() == td.ROW_SCRIPT

    # nothing was executed
    assert not dialogs, f"An alert dialog appeared: {dialogs}"
    injected = page.evaluate(
        "() => [...document.scripts].some(s => s.textContent.includes('alert(1)'))"
    )
    assert not injected, "A <script> element containing alert(1) exists in the page"

    # layout intact
    d.verify_fields_visible()


def test_TC_ROWDETAILS_021_name_trimmed(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_TRIMMED,
        ensure_row=True,
        typed_row_name=td.ROW_TRIMMED_TYPED,   # typed with 1 leading + 1 trailing space
    )
    d = ctx.details
    path_raw = d.path_label.first.text_content()
    assert path_raw.endswith(f"{ctx.row_id} - {td.ROW_TRIMMED}"), (
        f"Path does not end with the trimmed name: {path_raw!r}"
    )
    label = d.label_value_in_modal(td.ROW_TRIMMED)
    expect(label).to_be_visible()
    assert label.first.text_content() == td.ROW_TRIMMED, (
        f"Label has extra whitespace: {label.first.text_content()!r}"
    )


# ===========================================================================
# TC_022 – TC_023  Long names
# ===========================================================================
def test_TC_ROWDETAILS_022_long_row_name_does_not_break_layout(page, credentials):
    # Row name = "M" x 255, Active, no polygon (created only if missing)
    assert len(td.LONG_ROW_NAME) == td.LONG_ROW_NAME_LENGTH == 255
    ctx = _prepare(
        page,
        credentials,
        row_name=td.LONG_ROW_NAME,
        ensure_row=True,
        polygon_points=None,
    )
    d = ctx.details
    d.verify_modal_open()

    # 5. Path line and Label value must stay inside the modal edges
    label_loc = d.label_value_in_modal(td.LONG_ROW_NAME)
    d.assert_inside_modal(d.path_label, "Path line")
    d.assert_inside_modal(label_loc, "Label value")

    # Long text must not overlap / hide the fields below it
    label_rect = d.visible_text_rect(label_loc)
    for lbl, name in ((d.network_label, "Network"), (d.status_label, "Status")):
        top = lbl.first.bounding_box()["y"]
        assert label_rect["bottom"] <= top + 1, (
            f"Long Label value overlaps the {name} field"
        )

    # 6. Everything else is still visible and usable
    d.verify_fields_visible()
    d.assert_inside_modal(d.id_value(ctx.row_id), "ID value")
    expect(d.id_value(ctx.row_id)).to_be_visible()
    expect(d.network_value(ctx.network_id)).to_be_visible()
    expect(d.status_badge(td.STATUS_ACTIVE)).to_be_visible()
    expect(d.map_container).to_be_visible()
    expect(d.edit_button).to_be_enabled()
    expect(d.close_button).to_be_enabled()
    expect(d.close_icon).to_be_visible()


def test_TC_ROWDETAILS_023_long_region_name_in_path(page, credentials):
    assert len(td.LONG_REGION_NAME) == td.LONG_REGION_NAME_LENGTH == 255
    ctx = _prepare(
        page,
        credentials,
        region_name=td.LONG_REGION_NAME,
        network_name=td.NETWORK_LONG_REGION,
        row_name=td.ROW_LONG_REGION,
        ensure_primary=False,
        ensure_row=True,
        polygon_points=None,
    )
    d = ctx.details
    d.verify_modal_open()

    # Path contains all 255 "R" characters, then the network and row
    path_raw = d.path_label.first.text_content()
    assert td.LONG_REGION_NAME in path_raw, "Path does not contain all 255 'R' characters"
    assert path_raw.endswith(
        f" / {ctx.network_id} - {td.NETWORK_LONG_REGION}"
        f" / {ctx.row_id} - {td.ROW_LONG_REGION}"
    ), f"Unexpected end of Path: {path_raw[-120:]!r}"
    expect(
        d.path_text(
            ctx.region_id,
            td.LONG_REGION_NAME,
            ctx.network_id,
            td.NETWORK_LONG_REGION,
            ctx.row_id,
            td.ROW_LONG_REGION,
        )
    ).to_be_visible()

    # Nothing extends outside the modal
    d.assert_inside_modal(d.path_label, "Path line")
    d.verify_fields_visible()


# ===========================================================================
# TC_025 / TC_026 skipped (second session + delete)
# ===========================================================================
@pytest.mark.skip(reason="Needs a second session and a delete flow, not automated (TC_025)")
def test_TC_ROWDETAILS_025_parent_network_deleted(page, credentials):
    pass


@pytest.mark.skip(reason="Needs a second session and a delete flow, not automated (TC_026)")
def test_TC_ROWDETAILS_026_row_deleted_by_other_session(page, credentials):
    pass


# ===========================================================================
# TC_027 – TC_029  Keyboard, checkbox, Active coverage
# ===========================================================================
def test_TC_ROWDETAILS_027_keyboard_accessible(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details

    # 1. focus inside the modal
    d.modal_heading.click()

    # 2. Tab up to 10 times and record the order of X / Edit / Close
    order: list[str] = []
    for _ in range(10):
        page.keyboard.press("Tab")
        control = d.focused_control()
        if control and (not order or order[-1] != control):
            order.append(control)
            assert d.focus_ring_visible(), f"No visible focus indicator on '{control}'"
        if control == "close":
            break

    assert order == ["x", "edit", "close"], (
        f"Focus order should be X, Edit, Close but was {order}"
    )

    # 3. Enter on Close closes the modal
    page.keyboard.press("Enter")
    d.verify_modal_closed()


def test_TC_ROWDETAILS_028_checkbox_does_not_open_details(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    d = ctx.details
    row_btn = ctx.tree.row_rows(ctx.network_id, ctx.row).first
    expect(row_btn).to_be_visible()

    checkbox = d.row_checkbox(ctx.row_id, ctx.row)
    expect(checkbox).not_to_be_checked()          # 5. unchecked at the start
    checkbox.check()                              # 6. click the checkbox itself
    expect(checkbox).to_be_checked()

    # 7. row is added to the Active coverage panel and Row Details stays closed
    expect(d.active_coverage_title).to_be_visible()
    expect(d.active_coverage_one_row).to_be_visible()
    expect(
        d.active_coverage_entry(
            ctx.region_id, ctx.region, ctx.network_id, ctx.network, ctx.row_id, ctx.row
        ).first
    ).to_be_visible()
    expect(d.modal_heading).to_have_count(0)


def test_TC_ROWDETAILS_029_active_coverage_reflects_checked_row(page, credentials):
    ctx = _prepare(page, credentials, open_details=False)
    d = ctx.details
    row_btn = ctx.tree.row_rows(ctx.network_id, ctx.row).first
    expect(row_btn).to_be_visible()

    # 5. check the row checkbox
    checkbox = d.row_checkbox(ctx.row_id, ctx.row)
    checkbox.check()
    expect(checkbox).to_be_checked()

    # 6. click the label and wait for the modal
    ctx.tree.open_for_row(ctx.region, ctx.network, ctx.row)
    d.verify_modal_open()

    # 7. Active coverage shows 1 row, the same row as in the modal
    expect(d.active_coverage_one_row).to_be_visible()
    expect(
        d.active_coverage_entry(
            ctx.region_id, ctx.region, ctx.network_id, ctx.network, ctx.row_id, ctx.row
        ).first
    ).to_be_visible()
    expect(
        d.path_text(
            ctx.region_id, ctx.region, ctx.network_id, ctx.network, ctx.row_id, ctx.row
        )
    ).to_be_visible()


# ===========================================================================
# TC_030 – TC_034  Details/Remarks, backdrop, session, viewport
# ===========================================================================
def test_TC_ROWDETAILS_030_details_remarks_not_lost(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_TEXT,
        ensure_row=True,
        row_details=td.ROW_TEXT_DETAILS,
        row_remarks=td.ROW_TEXT_REMARKS,
    )
    d = ctx.details
    # 1. Row Details does not show Details and Remarks
    expect(d.modal_container).not_to_contain_text(td.ROW_TEXT_DETAILS)
    expect(d.modal_container).not_to_contain_text(td.ROW_TEXT_REMARKS)

    # 2-3. Edit form shows them complete and unchanged
    d.click_edit()
    d.verify_edit_modal_open()
    expect(d.edit_details_input).to_have_value(td.ROW_TEXT_DETAILS)
    expect(d.edit_remarks_input).to_have_value(td.ROW_TEXT_REMARKS)


def test_TC_ROWDETAILS_031_backdrop_click_closes_single_modal(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    heading = page.get_by_role("heading", name=td.MODAL_TITLE)
    expect(heading).to_have_count(1)             # only one modal open

    # 1. click the dimmed background (5 px from the top-left corner)
    page.mouse.click(5, 5)

    # 3. never two Row Details modals at the same time
    for _ in range(5):
        assert heading.count() <= 1, "More than one Row Details modal is shown"
        page.wait_for_timeout(100)

    # 2. the modal closes
    d.verify_modal_closed()


def test_TC_ROWDETAILS_032_session_cleared_while_open(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details

    # 1-2. clear cookies and session storage
    ctx.explorer.clear_session_data()

    # 3. click Edit (the form may open client-side; the API call then reports the session problem)
    d.click_edit()

    def _login_or_message() -> bool:
        on_login = bool(re.search(r"/login", page.url or ""))
        return on_login or page.get_by_text(td.SESSION_MESSAGE).count() > 0

    # 4. wait up to ~8 s for a redirect to Login or a session message ...
    for _ in range(16):
        if _login_or_message():
            break
        page.wait_for_timeout(500)
    else:
        # ... otherwise reload (F5) as the test case says; the app must then send us to Login
        page.reload(wait_until="domcontentloaded")
        expect(page).to_have_url(re.compile(r"/login"), timeout=15000)


def test_TC_ROWDETAILS_033_map_survives_resize(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_POLYGON,
        ensure_row=True,
        polygon_points=td.ROW_POLYGON_POINTS,
    )
    d = ctx.details
    for width, height in ((1920, 1080), (800, 600)):
        page.set_viewport_size({"width": width, "height": height})
        page.wait_for_timeout(700)
        d.verify_modal_open()
        d.assert_modal_inside_viewport()
        expect(d.map_container).to_be_visible()
        expect(d.polygon_shapes.first).to_be_visible()
        d.verify_polygon_inside_map()
        d.verify_caption(3)


def test_TC_ROWDETAILS_034_narrow_viewport_usable(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    page.set_viewport_size({"width": 575, "height": 812})
    page.wait_for_timeout(700)

    d.verify_fields_visible()
    expect(d.edit_button).to_be_enabled()
    expect(d.close_button).to_be_enabled()
    d.assert_modal_inside_viewport()

    fields = [
        ("Path", d.path_label),
        ("ID label", d.id_label),
        ("Label label", d.label_label),
        ("Network label", d.network_label),
        ("Status label", d.status_label),
        ("Coverage area label", d.coverage_area_label),
        ("Map", d.map_container),
        ("Edit button", d.edit_button),
        ("Close button", d.close_button),
    ]
    for name, loc in fields:
        d.assert_inside_viewport(loc, name)
    d.assert_no_overlap(fields)               # stacked, nothing overlapping


# ===========================================================================
# TC_035 skipped (delete)
# ===========================================================================
@pytest.mark.skip(reason="Delete flow not automated (TC_035)")
def test_TC_ROWDETAILS_035_only_row_delete_shows_no_row(page, credentials):
    pass


# ===========================================================================
# TC_036 – TC_041  Precision, labels, focus trap, inactive parent, no polygon, SQL
# ===========================================================================
def test_TC_ROWDETAILS_036_polygon_precision_caption(page, credentials):
    # The visual comparison with the main map is manual (see sheet remarks);
    # here: 4 corners drawn, inside the map, caption exactly 4 vertices.
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_PRECISION,
        ensure_row=True,
        polygon_points=td.PRECISION_POLYGON_POINTS,
    )
    d = ctx.details
    expect(d.polygon_shapes.first).to_be_visible(timeout=10000)
    assert d.polygon_vertex_count() == td.PRECISION_VERTEX_COUNT
    d.verify_polygon_inside_map()
    d.verify_caption(td.PRECISION_VERTEX_COUNT)


def test_TC_ROWDETAILS_037_labels_distinct_from_values(page, credentials):
    ctx = _prepare(page, credentials)
    d = ctx.details
    pairs = [
        ("ID", d.id_label, d.id_value(ctx.row_id), True),
        ("Label", d.label_label, d.label_value_in_modal(td.PRIMARY_ROW_NAME), True),
        ("Network", d.network_label, d.network_value(ctx.network_id), True),
        # Status value is a small pill: it must differ from its label, but is not
        # required to be larger than it.
        ("Status", d.status_label, d.status_badge(td.STATUS_ACTIVE), False),
    ]
    for name, label_loc, value_loc, strict in pairs:
        expect(label_loc).to_be_visible()
        expect(value_loc).to_be_visible()
        label = d.text_style(label_loc)
        value = d.text_style(value_loc)
        smaller = label["fontSize"] < value["fontSize"]
        lighter = label["luminance"] > value["luminance"]
        if strict:
            assert smaller, f"{name}: label font ({label['fontSize']}px) is not smaller than value ({value['fontSize']}px)"
            assert lighter, f"{name}: label colour is not lighter than the value colour"
        else:
            assert smaller or lighter, f"{name}: label looks the same as its value"



def test_TC_ROWDETAILS_039_active_row_under_inactive_network(page, credentials):
    ctx = _prepare(page, credentials, open_details=False, ensure_primary=True)
    _ensure_network(
        page,
        ctx.tree,
        ctx.explorer,
        ctx.region,
        td.NETWORK_INACTIVE_PARENT,
        active=True,
    )
    _ensure_row(
        page,
        ctx.tree,
        ctx.explorer,
        ctx.region,
        td.NETWORK_INACTIVE_PARENT,
        td.ROW_INACTIVE_PARENT,
        active=True,
    )

    # 1. Network Details -> Edit -> uncheck Active -> save -> wait until the form closes
    ctx.tree.open_for_network(ctx.region, td.NETWORK_INACTIVE_PARENT)
    ctx.tree.click_edit()
    page.get_by_role("checkbox", name="Active", exact=True).uncheck()
    page.locator('button[type="submit"]').last.click()
    expect(
        page.get_by_role("heading", name=re.compile(r"Edit Network", re.I))
    ).to_be_hidden(timeout=15000)

    # make sure a Network Details dialog left open does not cover the tree
    network_details = page.get_by_role("heading", name=re.compile(r"Network Details", re.I))
    if network_details.count() and network_details.first.is_visible():
        page.keyboard.press("Escape")
        expect(network_details).to_be_hidden(timeout=10000)

    # 2-3. click the row label under the (now inactive) network
    ctx.tree.expand_region(ctx.region)
    network_id = ctx.tree.get_network_id(ctx.region_id, td.NETWORK_INACTIVE_PARENT)
    row_id = ctx.tree.open_for_row(
        ctx.region, td.NETWORK_INACTIVE_PARENT, td.ROW_INACTIVE_PARENT
    )

    # 4. Network and Status values
    d = ctx.details
    d.verify_modal_open()
    expect(d.label_value_in_modal(td.ROW_INACTIVE_PARENT)).to_be_visible()
    expect(d.network_value(network_id)).to_be_visible()
    expect(d.status_badge(td.STATUS_ACTIVE)).to_be_visible()   # the row's own flag
    expect(d.id_value(row_id)).to_be_visible()


def test_TC_ROWDETAILS_040_no_coverage_polygon_message(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_NO_POLYGON,
        ensure_row=True,
        polygon_points=None,
    )
    d = ctx.details
    expect(d.map_container).to_be_visible()
    d.verify_no_polygon_drawn()       # map without any polygon
    d.verify_no_polygon()             # message shown, "Polygon defined with ... vertices." not shown


def test_TC_ROWDETAILS_041_sql_payload_rendered_as_text(page, credentials):
    ctx = _prepare(
        page,
        credentials,
        row_name=td.ROW_SQL,
        ensure_row=True,
        polygon_points=None,
    )
    d = ctx.details
    # Path and Label show the payload as plain text, quotes visible
    expect(
        d.path_text(
            ctx.region_id, ctx.region, ctx.network_id, ctx.network, ctx.row_id, td.ROW_SQL
        )
    ).to_be_visible()
    label = d.label_value_in_modal(td.ROW_SQL)
    expect(label).to_be_visible()
    assert label.first.text_content() == td.ROW_SQL
    expect(d.id_value(ctx.row_id)).to_be_visible()

    # no error message / dialog
    assert page.locator("dialog, [role='alertdialog']").count() == 0
    expect(
        page.get_by_text(re.compile(r"something went wrong|unexpected error|failed to", re.I))
    ).to_have_count(0)

    # 8. close the modal; the rest of the tree is intact
    d.close_via_button()
    d.verify_modal_closed()
    expect(ctx.tree.row_rows(ctx.network_id, td.ROW_SQL).first).to_be_visible()
    expect(ctx.tree.row_rows(ctx.network_id, td.PRIMARY_ROW_NAME).first).to_be_visible()