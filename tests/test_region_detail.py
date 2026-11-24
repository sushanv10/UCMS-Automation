import re

import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from modals.add_region_modal import AddRegionModal
from modals.region_detail_modal import RegionDetailsModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import region_detail_test_data as td
from utils.helpers import unique


# ---------------------------------------------------------------------------
# Shared helpers
#
# NOTE: No region ID is hardcoded anywhere in this module. Regions are found
# by NAME; the auto-generated ID is read from the Coverage tree at runtime.
#
# Two ways a test gets its region:
#   * _ensure_region(...)  - shared, fixed-name regions. Created only if the
#                            tree does not already contain them.
#   * _create_region(...)  - used with a unique(<base>) name, so every run
#                            gets a brand-new region and re-runs never clash.
# ---------------------------------------------------------------------------
def _login_and_open_coverage(
    page: Page,
    credentials: tuple[str, str],
) -> tuple[NetworkExplorerPage, RegionDetailsModal]:
    """Log in and open the Coverage panel. Does NOT open any region."""
    login_page = LoginPage(page)
    explorer = NetworkExplorerPage(page)
    modal = RegionDetailsModal(page)

    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    explorer.verify_page_loaded()
    explorer.open_coverage_panel()
    explorer.verify_coverage_panel_open()

    return explorer, modal


def _wait_for_tree(modal: RegionDetailsModal) -> None:
    expect(modal.any_region_row().first).to_be_visible(timeout=15000)


def _create_region(
    page: Page,
    modal: RegionDetailsModal,
    entered_name: str,
    displayed_name: str | None = None,
) -> None:
    """
    Create a region via Add Region and wait until it appears in the tree.
    `displayed_name` is the name the tree shows when it differs from what was
    typed (e.g. trimmed whitespace).
    """
    _wait_for_tree(modal)

    add_region = AddRegionModal(page)
    add_region.open()
    add_region.fill_region_name(entered_name)
    add_region.submit()
    add_region.verify_modal_closed()

    expect(
        modal.region_tree_rows(displayed_name or entered_name).first
    ).to_be_visible(timeout=15000)


def _ensure_region(page: Page, modal: RegionDetailsModal, region_name: str) -> None:
    """Create the region through Add Region ONLY if it is not in the tree yet."""
    _wait_for_tree(modal)

    if modal.region_tree_rows(region_name).count() == 0:
        _create_region(page, modal, region_name)


def _ensure_long_name_region(page: Page, modal: RegionDetailsModal) -> None:
    """The 255-char name is shown truncated, so existence is checked by prefix."""
    _wait_for_tree(modal)

    if modal.region_tree_rows_by_prefix(td.LONG_NAME_TREE_PREFIX).count() == 0:
        add_region = AddRegionModal(page)
        add_region.open()
        add_region.fill_region_name(td.LONG_NAME_REGION_NAME)
        add_region.submit()
        add_region.verify_modal_closed()
        expect(
            modal.region_tree_rows_by_prefix(td.LONG_NAME_TREE_PREFIX).first
        ).to_be_visible(timeout=15000)


def _login_and_open_region_details(
    page: Page,
    credentials: tuple[str, str],
    region_name: str = td.PRIMARY_REGION_NAME,
) -> tuple[NetworkExplorerPage, RegionDetailsModal]:
    """
    Log in, open Coverage, make sure the region exists (create only if
    missing) and open Region Details for it. The runtime ID is available
    afterwards as `modal.opened_region_id`.
    """
    explorer, modal = _login_and_open_coverage(page, credentials)

    _ensure_region(page, modal, region_name)
    modal.open_for_region_name(region_name)

    return explorer, modal


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_001: Modal opens correctly when a region label is clicked
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_001_modal_displays_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    modal.verify_modal_open()
    modal.verify_modal_centred()

    # Path, ID, Label.
    modal.verify_opened_region_details(td.PRIMARY_REGION_NAME)

    # Coverage area map plus action buttons.
    expect(modal.coverage_area_heading).to_be_visible()
    expect(modal.map_container).to_be_visible()
    expect(modal.edit_button).to_be_visible()
    expect(modal.close_button).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_002: Modal title displays correctly
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_002_modal_title_displays_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    expect(modal.modal_heading).to_have_text(td.MODAL_TITLE)

    # Title is bold.
    font_weight = modal.modal_heading.evaluate(
        "(el) => getComputedStyle(el).fontWeight"
    )
    assert font_weight in ("bold", "bolder") or int(font_weight) >= 600, (
        f"Modal title is not bold (font-weight={font_weight})"
    )

    # Close "X" icon at the top-right of the modal.
    expect(modal.close_icon).to_be_visible()
    heading_box = modal.modal_heading.bounding_box()
    icon_box = modal.close_icon.bounding_box()
    assert icon_box["x"] > heading_box["x"], (
        "Close icon should be to the right of the title"
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_003: Modal closes via 'X' icon, no data altered
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_003_modal_closes_via_x_icon(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)
    region_id = modal.opened_region_id

    modal.close_via_x()

    modal.verify_modal_closed()
    modal.verify_tree_row_unchanged(td.PRIMARY_REGION_NAME, region_id)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_004: Modal is dismissible via Escape key
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_004_escape_key_closes_modal(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)
    region_id = modal.opened_region_id

    page.keyboard.press("Escape")

    modal.verify_modal_closed()
    modal.verify_tree_row_unchanged(td.PRIMARY_REGION_NAME, region_id)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_005: 'Close' button dismisses the modal, no data changed
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_005_close_button_dismisses_modal(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)
    region_id = modal.opened_region_id

    modal.close_via_button()

    modal.verify_modal_closed()
    modal.verify_tree_row_unchanged(td.PRIMARY_REGION_NAME, region_id)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_006: Path shows only the clicked region (no parent chain)
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_006_path_breadcrumb_displays_correct_region(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    path = modal.path_text(modal.opened_region_id, td.PRIMARY_REGION_NAME)
    expect(path).to_be_visible()

    # A region is the top level: no "/" separator / parent segments.
    expect(path).not_to_contain_text("/")


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_007: Details match the region actually clicked
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_007_details_match_region_actually_clicked(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    name_1 = td.PATH_TEST_REGION_1_NAME
    name_2 = td.PATH_TEST_REGION_2_NAME

    # Preconditions: both regions exist (created only if missing).
    _ensure_region(page, modal, name_1)
    _ensure_region(page, modal, name_2)

    # Read both runtime IDs BEFORE opening anything.
    id_1 = modal.get_region_id_from_tree(name_1)
    id_2 = modal.get_region_id_from_tree(name_2)

    # Click region 2 (not region 1).
    modal.open_for_region_name(name_2)

    # Path, ID and Label all belong to region 2.
    modal.verify_region_details(id_2, name_2)

    # Nothing of region 1 may appear.
    expect(modal.path_text(id_1, name_1)).to_have_count(0)
    expect(modal.id_value(id_1)).to_have_count(0)
    expect(modal.label_value(name_1)).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_008: ID field displays the correct region identifier
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_008_id_field_correct(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    region_id = modal.opened_region_id

    expect(modal.id_label).to_be_visible()
    expect(modal.id_value(region_id)).to_be_visible()

    # Auto-generated ID: letter "G" followed by a number.
    assert re.fullmatch(r"G\d+", region_id), (
        f"Region ID {region_id!r} does not look like 'G<number>'"
    )

    # Same ID as in the Path line.
    expect(modal.path_text(region_id, td.PRIMARY_REGION_NAME)).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_009: Label field displays the correct region name
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_009_label_field_correct(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    expect(modal.label_label).to_be_visible()

    # Exact match: no truncation, no leading/trailing whitespace.
    label = modal.label_value(td.PRIMARY_REGION_NAME)
    expect(label).to_be_visible()
    assert label.text_content() == td.PRIMARY_REGION_NAME


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_010: Two regions sharing a Label are told apart by ID
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_010_distinguishes_duplicate_label_regions(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    # Unique per run, but shared by BOTH regions (duplicates are allowed).
    name = unique(td.DUPLICATE_LABEL_REGION_BASE)
    _create_region(page, modal, name)
    _create_region(page, modal, name)

    rows = modal.region_tree_rows(name)
    expect(rows).to_have_count(2, timeout=15000)

    # Read both runtime IDs up front; they must differ.
    region_a_id = modal.get_region_id_from_tree(name, index=0)
    region_b_id = modal.get_region_id_from_tree(name, index=1)
    assert region_a_id != region_b_id, (
        "Two regions with the same label must have different IDs"
    )

    # First row.
    modal.open_for_region_name(name, index=0)
    modal.verify_region_details(region_a_id, name)

    modal.close_via_button()
    modal.verify_modal_closed()

    # Second row.
    modal.open_for_region_name(name, index=1)
    modal.verify_region_details(region_b_id, name)

    # Region A's data must not be shown in Region B's modal.
    expect(modal.path_text(region_a_id, name)).to_have_count(0)
    expect(modal.id_value(region_a_id)).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_011: Long region name must not overflow the modal
# (currently a known FAIL - the name overflows; max length may become 50)
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_011_long_region_name_does_not_overflow(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    _ensure_long_name_region(page, modal)

    # The tree row is truncated with "...", so locate it by prefix.
    modal.open_for_row(
        modal.region_tree_rows_by_prefix(td.LONG_NAME_TREE_PREFIX).first
    )

    path = modal.path_text_by_name(td.LONG_NAME_REGION_NAME)
    label = modal.label_value(td.LONG_NAME_REGION_NAME)
    expect(path).to_be_visible()
    expect(label).to_be_visible()

    # Text stays inside the modal and does not touch the page layout.
    modal.verify_content_within_modal(path, label)
    modal.verify_no_horizontal_scroll()

    # Text must not run into the X icon or the Edit / Close buttons.
    for text_loc in (path, label):
        text_box = text_loc.bounding_box()
        for other in (modal.close_icon, modal.edit_button, modal.close_button):
            other_box = other.bounding_box()
            overlaps = not (
                text_box["x"] + text_box["width"] <= other_box["x"]
                or other_box["x"] + other_box["width"] <= text_box["x"]
                or text_box["y"] + text_box["height"] <= other_box["y"]
                or other_box["y"] + other_box["height"] <= text_box["y"]
            )
            assert not overlaps, "Long name overlaps another modal element"


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_012: Single-character region name displays correctly
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_012_single_character_region_name(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
        region_name=td.SHORT_NAME_REGION_NAME,
    )

    # First "R" in the tree is used if several share the name.
    modal.verify_opened_region_details(td.SHORT_NAME_REGION_NAME)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_013: Script payload renders safely as plain text
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_013_script_payload_renders_safely(
    page: Page,
    credentials: tuple[str, str],
):
    dialogs: list[str] = []

    page.on(
        "dialog",
        lambda dialog: (
            dialogs.append(dialog.message),
            dialog.dismiss(),
        ),
    )

    _, modal = _login_and_open_coverage(page, credentials)

    # Unique per run so a re-run never collides with an old payload region.
    region_name = unique(td.SCRIPT_INJECTION_REGION_BASE)
    _create_region(page, modal, region_name)

    # Locate the row by its (unique) name and open it.
    modal.open_for_region_name(region_name)

    # Payload must not execute JavaScript.
    assert not dialogs, f"A JS dialog fired - script injection NOT sanitized: {dialogs}"

    # Payload is shown as literal text, angle brackets included.
    modal.verify_opened_region_details(region_name)
    expect(modal.path_text_by_name(region_name)).to_be_visible()

    # No <script> element carrying the payload exists in the DOM.
    expect(modal.script_element_for_payload(region_name)).to_have_count(0)

    # Layout intact.
    modal.verify_content_within_modal(modal.label_value(region_name))
    modal.verify_no_horizontal_scroll()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_014: Leading/trailing spaces display trimmed
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_014_untrimmed_name_displays_trimmed(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    trimmed_name = unique(td.TRIMMED_REGION_BASE)
    entered_name = f" {trimmed_name} "  # 1 leading + 1 trailing space

    _create_region(page, modal, entered_name, displayed_name=trimmed_name)

    modal.open_for_region_name(trimmed_name)

    # Exact-text locators fail if any leading/trailing whitespace is shown.
    modal.verify_opened_region_details(trimmed_name)
    expect(modal.path_text_by_name(trimmed_name)).to_be_visible()
    assert modal.label_value(trimmed_name).text_content() == trimmed_name


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_015: Edit button opens the edit form pre-filled
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_015_edit_button_opens_prefilled_form(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    modal.click_edit()

    modal.verify_edit_modal_open()
    expect(modal.edit_region_name_input).to_have_value(td.PRIMARY_REGION_NAME)
    expect(modal.edit_region_name_input).to_be_editable()

    # Leave the Edit form without changing anything.
    page.keyboard.press("Escape")


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_016: Region deleted by another session mid-view
# ---------------------------------------------------------------------------
@pytest.mark.skip(reason="TODO: implement concurrent region deletion scenario")
@pytest.mark.region_details
def test_TC_REGIONDETAILS_016_region_deleted_mid_view(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    # Unique so the region this test deletes is never reused by other tests.
    region_name = unique(td.DELETE_TEST_REGION_NAME)
    _create_region(page, modal, region_name)
    modal.open_for_region_name(region_name)

    # TODO: delete `region_name` from a second browser context (Session B)
    # or via the delete API (look it up by name, not by ID).

    modal.click_edit()

    # TODO: confirm the exact message ("Region not found" / "no longer exists").
    expect(
        page.get_by_text(re.compile("not found|no longer exists", re.IGNORECASE))
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_017: Modal is keyboard accessible
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_017_modal_keyboard_accessible(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    # Click the title so keyboard focus is inside the modal.
    modal.modal_heading.click()

    focus_order: list[str] = []
    close_button_reached = False

    for _ in range(10):
        page.keyboard.press("Tab")

        focused = page.evaluate(
            """
            () => {
                const el = document.activeElement;
                if (!el) { return { text: "", ariaLabel: "", title: "" }; }
                return {
                    text: (el.textContent || "").trim(),
                    ariaLabel: el.getAttribute("aria-label") || "",
                    title: el.getAttribute("title") || ""
                };
            }
            """
        )
        name = (focused["text"] or focused["ariaLabel"] or focused["title"]).lower()
        focus_order.append(name)

        if name == "close" and "edit" in focus_order:
            close_button_reached = True
            break

    assert close_button_reached, (
        f"Close button not reached via Tab after Edit. Focus order: {focus_order}"
    )

    # Activate the focused Close button.
    page.keyboard.press("Enter")

    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_018: Clicking the expand arrow does not open the modal
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_018_expand_arrow_does_not_open_modal(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    _ensure_region(page, modal, td.PRIMARY_REGION_NAME)

    arrow = modal.expand_arrow_for(td.PRIMARY_REGION_NAME)
    expect(arrow).to_be_visible()

    # First click expands, second click collapses; modal never opens.
    arrow.click()
    modal.verify_modal_closed()

    arrow.click()
    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_019: Selected region highlighted in tree while modal open
# (currently a known FAIL - the real "selected" indicator is unconfirmed)
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_019_region_highlighted_in_tree(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    row = modal.region_tree_rows(td.PRIMARY_REGION_NAME).first

    # TODO: replace with the real selected-state indicator once confirmed
    # with the developer (CSS class / background / aria-selected).
    expect(row).to_have_attribute("aria-expanded", "true")


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_020: One modal at a time; dimmed background closes it
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_020_no_overlapping_modal_instances(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    # Only a single modal instance is open.
    expect(modal.modal_heading).to_have_count(1)

    # Click the dimmed background (5 px from the top-left corner).
    page.mouse.click(5, 5)

    modal.verify_modal_closed()
    expect(modal.modal_heading).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_021: Opens fresh (not cached) for a different region
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_021_opens_fresh_for_different_region(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    _ensure_region(page, modal, td.PRIMARY_REGION_NAME)
    _ensure_region(page, modal, td.FRESH_REGION_NAME)

    # First region.
    id_1 = modal.open_for_region_name(td.PRIMARY_REGION_NAME)
    modal.verify_region_details(id_1, td.PRIMARY_REGION_NAME)

    modal.close_via_button()
    modal.verify_modal_closed()

    # Second region (ID read from the tree at runtime).
    id_2 = modal.open_for_region_name(td.FRESH_REGION_NAME)
    modal.verify_region_details(id_2, td.FRESH_REGION_NAME)

    # Nothing from the first region carried over.
    expect(modal.path_text(id_1, td.PRIMARY_REGION_NAME)).to_have_count(0)
    expect(modal.id_value(id_1)).to_have_count(0)
    expect(modal.label_value(td.PRIMARY_REGION_NAME)).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_022: Session expiry while modal is open
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_022_session_expiry_while_open(
    page: Page,
    context,
    credentials: tuple[str, str],
):
    explorer, modal = _login_and_open_region_details(page, credentials)

    # Simulate session expiry (cookies + session storage cleared).
    explorer.clear_session_data()

    page.reload()

    # User is redirected to the login page; modal/data are not shown.
    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)
    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_023: Opens correctly for a region with no child networks
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_023_opens_correctly_with_no_networks(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    _ensure_region(page, modal, td.NO_NETWORK_REGION_NAME)

    # Expand the row: "No network" is shown; collapse again.
    arrow = modal.expand_arrow_for(td.NO_NETWORK_REGION_NAME)
    arrow.click()
    expect(page.get_by_text("No network", exact=True).first).to_be_visible()
    arrow.click()

    modal.open_for_region_name(td.NO_NETWORK_REGION_NAME)

    modal.verify_opened_region_details(td.NO_NETWORK_REGION_NAME)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_024: Field labels visually distinguished from values
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_024_labels_visually_distinguished_from_values(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    id_value_locator = modal.id_value(modal.opened_region_id)
    label_value_locator = modal.label_value(td.PRIMARY_REGION_NAME)

    js = (
        "(el) => { const s = getComputedStyle(el);"
        " return { color: s.color, size: parseFloat(s.fontSize),"
        " weight: s.fontWeight }; }"
    )

    pairs = (
        ("ID", modal.id_label.evaluate(js), id_value_locator.evaluate(js)),
        ("Label", modal.label_label.evaluate(js), label_value_locator.evaluate(js)),
    )

    for field, label_style, value_style in pairs:
        # Label is smaller and a different (lighter grey) colour than its value.
        assert label_style["size"] <= value_style["size"], (
            f"{field}: label font should not be larger than its value "
            f"({label_style['size']} vs {value_style['size']})"
        )
        assert (
            label_style["color"] != value_style["color"]
            or label_style["weight"] != value_style["weight"]
            or label_style["size"] != value_style["size"]
        ), f"{field}: label and value look identical"


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_025: Renders correctly on a narrow (mobile) viewport
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_025_renders_on_mobile_viewport(
    page: Page,
    credentials: tuple[str, str],
):
    page.set_viewport_size(td.MOBILE_VIEWPORT)

    _, modal = _login_and_open_region_details(page, credentials)
    region_id = modal.opened_region_id

    modal.verify_opened_region_details(td.PRIMARY_REGION_NAME)

    expect(modal.edit_button).to_be_visible()
    expect(modal.close_button).to_be_visible()

    # Nothing is outside the screen.
    modal.verify_within_viewport(
        modal.path_text(region_id, td.PRIMARY_REGION_NAME),
        modal.id_value(region_id),
        modal.label_value(td.PRIMARY_REGION_NAME),
        modal.edit_button,
        modal.close_button,
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_026: Reflows correctly on window resize
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_026_resizes_on_window_resize(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)
    region_id = modal.opened_region_id

    for viewport in (td.DESKTOP_VIEWPORT, td.SMALL_DESKTOP_VIEWPORT):
        page.set_viewport_size(viewport)

        modal.verify_modal_open()
        modal.verify_opened_region_details(td.PRIMARY_REGION_NAME)
        expect(modal.edit_button).to_be_visible()
        expect(modal.close_button).to_be_visible()

        # Modal stays inside the window at both sizes.
        modal.verify_within_viewport(
            modal.modal_container,
            modal.path_text(region_id, td.PRIMARY_REGION_NAME),
            modal.edit_button,
            modal.close_button,
        )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_027: ID/Label/Path fields are read-only
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_027_fields_are_read_only(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(page, credentials)

    region_id = modal.opened_region_id

    # Text "abc123" is on the clipboard for the Ctrl+V attempts.
    page.evaluate(
        "(text) => navigator.clipboard.writeText(text)"
        ".catch(() => {})",
        td.READ_ONLY_FIELD_TYPED_INPUT,
    )

    id_value_locator = modal.id_value(region_id)
    label_value_locator = modal.label_value(td.PRIMARY_REGION_NAME)
    path_locator = modal.path_text(region_id, td.PRIMARY_REGION_NAME)

    for locator in (id_value_locator, label_value_locator, path_locator):
        locator.click()

        page.keyboard.type(td.READ_ONLY_FIELD_TYPED_INPUT)
        page.keyboard.press("Backspace")
        page.keyboard.press("Delete")
        page.keyboard.press("Control+V")

    # Values must remain unchanged.
    expect(id_value_locator).to_have_text(region_id)
    expect(label_value_locator).to_have_text(td.PRIMARY_REGION_NAME)
    expect(path_locator).to_have_text(
        f"Path: {region_id} - {td.PRIMARY_REGION_NAME}"
    )

    # No editable element should have received focus.
    expect(
        page.locator(
            "input:focus, textarea:focus, [contenteditable='true']:focus"
        )
    ).to_have_count(0)

    modal.close_via_button()
    modal.verify_modal_closed()

    # Tree row unchanged, and reopening shows the same values.
    modal.verify_tree_row_unchanged(td.PRIMARY_REGION_NAME, region_id)
    modal.open_for_region_name(td.PRIMARY_REGION_NAME)
    modal.verify_opened_region_details(td.PRIMARY_REGION_NAME)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_028: Coverage area for a region without a polygon
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_028_coverage_area_without_polygon(
    page: Page,
    credentials: tuple[str, str],
):
    # Created via Add Region without drawing a polygon (only if missing).
    _, modal = _login_and_open_region_details(page, credentials)

    expect(modal.coverage_area_heading).to_be_visible()

    # Map with zoom controls and the Leaflet / OpenStreetMap credit.
    expect(modal.map_container).to_be_visible()
    expect(modal.map_zoom_in).to_be_visible()
    expect(modal.map_zoom_out).to_be_visible()
    expect(modal.map_attribution).to_contain_text("Leaflet")
    expect(modal.map_attribution).to_contain_text("OpenStreetMap")

    # No polygon drawn; message shown below the map.
    expect(modal.map_container.locator("path.leaflet-interactive")).to_have_count(0)
    expect(modal.no_polygon_text).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_029: SQL payload region name renders safely
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_029_sql_payload_renders_safely(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(page, credentials)

    # Unique per run so re-runs never clash with an old payload region.
    region_name = unique(td.SQL_INJECTION_REGION_BASE)
    _create_region(page, modal, region_name)

    modal.open_for_region_name(region_name)

    # Shown as plain text with the quote characters visible.
    modal.verify_opened_region_details(region_name)
    expect(modal.path_text_by_name(region_name)).to_be_visible()

    # Close and confirm the tree still lists other regions (nothing broken).
    modal.close_via_button()
    modal.verify_modal_closed()

    assert modal.any_region_row().count() > 1, (
        "Coverage tree should still list its other regions"
    )
    expect(modal.region_tree_rows(region_name).first).to_be_visible()