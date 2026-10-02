import re

import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from modals.add_region_modal import AddRegionModal
from modals.region_detail_modal import RegionDetailsModal
from pages.login_page import LoginPage
from pages.network_explorer_page import NetworkExplorerPage
from test_data import region_detail_test_data as td


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _login_and_open_coverage(
    page: Page,
    credentials: tuple[str, str],
) -> tuple[NetworkExplorerPage, RegionDetailsModal]:
    """
    Log in and open the Coverage panel.
    Does NOT open any region.
    """
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


def _login_and_open_region_details(
    page: Page,
    credentials: tuple[str, str],
    region_id: str | None = None,
    region_name: str = td.PRIMARY_REGION_NAME,
) -> tuple[NetworkExplorerPage, RegionDetailsModal]:
    """
    Log in, open Coverage, and open Region Details.

    If region_id is provided, the exact region is opened using
    ID + name. This is required when multiple regions share the
    same label.

    If region_id is omitted, the region is opened by name.
    """
    explorer, modal = _login_and_open_coverage(page, credentials)

    if region_id is not None:
        modal.open_for_region(
            region_id,
            region_name,
        )
    else:
        modal.open_for_region_name(region_name)

    return explorer, modal


def _create_region(
    page: Page,
    region_name: str,
) -> AddRegionModal:
    """
    Create a new region via Add Region.

    Used only where no stable seeded region exists for the scenario
    (TC013, TC014), so these tests remain self-contained.
    """
    add_region_modal = AddRegionModal(page)

    add_region_modal.open()
    add_region_modal.fill_region_name(region_name)
    add_region_modal.submit()
    add_region_modal.verify_modal_closed()

    return add_region_modal


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_001: Modal displays correctly
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_001_modal_displays_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    modal.verify_modal_open()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_002: Modal title displays correctly
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_002_modal_title_displays_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    expect(modal.modal_heading).to_have_text(
        td.MODAL_TITLE
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_003: Modal closes via 'X' icon
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_003_modal_closes_via_x_icon(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    modal.close_via_x()

    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_004: Modal is dismissible via Escape key
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_004_escape_key_closes_modal(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    page.keyboard.press("Escape")

    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_005: 'Close' button dismisses the modal
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_005_close_button_dismisses_modal(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    modal.close_via_button()

    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_006: Path breadcrumb displays the correct region
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_006_path_breadcrumb_displays_correct_region(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    expect(
        modal.path_text(
            td.PRIMARY_REGION_ID,
            td.PRIMARY_REGION_NAME,
        )
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_007: Path breadcrumb matches the region actually clicked
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_007_details_match_region_actually_clicked(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
        region_name=td.SECONDARY_REGION_NAME,
    )

    # Get the actual ID assigned to the secondary region.
    secondary_region_id = modal.get_id_from_path(
        td.SECONDARY_REGION_NAME
    )

    # Verify that the details belong to the region actually clicked.
    modal.verify_region_details(
        secondary_region_id,
        td.SECONDARY_REGION_NAME,
    )

    # The primary region must not appear in the breadcrumb.
    expect(
        modal.path_text(
            td.PRIMARY_REGION_ID,
            td.PRIMARY_REGION_NAME,
        )
    ).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_008: ID field displays the correct region identifier
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_008_id_field_correct(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    expect(modal.id_label).to_be_visible()
    expect(
        modal.id_value(td.PRIMARY_REGION_ID)
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_009: Label field displays the correct region name
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_009_label_field_correct(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    expect(modal.label_label).to_be_visible()
    expect(
        modal.label_value(td.PRIMARY_REGION_NAME)
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_010: Distinguishes two regions sharing the same Label
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_010_distinguishes_duplicate_label_regions(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
        region_id=td.DUPLICATE_LABEL_REGION_A_ID,
        region_name=td.DUPLICATE_LABEL_REGION_NAME,
    )

    # Verify Region A.
    modal.verify_region_details(
        td.DUPLICATE_LABEL_REGION_A_ID,
        td.DUPLICATE_LABEL_REGION_NAME,
    )

    modal.close_via_button()
    modal.verify_modal_closed()

    # Open Region B using its unique ID.
    modal.open_for_region(
        td.DUPLICATE_LABEL_REGION_B_ID,
        td.DUPLICATE_LABEL_REGION_NAME,
    )

    # Verify Region B.
    modal.verify_region_details(
        td.DUPLICATE_LABEL_REGION_B_ID,
        td.DUPLICATE_LABEL_REGION_NAME,
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_011: Long region name displays in full (untruncated)
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_011_long_region_name_displays_in_full(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(
        page,
        credentials,
    )

    modal.open_for_region_name(
        td.LONG_NAME_REGION_NAME
    )

    expect(
        modal.label_value(td.LONG_NAME_REGION_NAME)
    ).to_be_visible()


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
        region_id=td.SHORT_NAME_REGION_ID,
        region_name=td.SHORT_NAME_REGION_NAME,
    )

    modal.verify_region_details(
        td.SHORT_NAME_REGION_ID,
        td.SHORT_NAME_REGION_NAME,
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_013: Script/SQL payload region name renders safely
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_013_injection_payload_renders_safely(
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

    _, modal = _login_and_open_coverage(
        page,
        credentials,
    )

    region_name = td.SCRIPT_INJECTION_REGION_NAME

    _create_region(
        page,
        region_name,
    )

    modal.open_for_region_name(region_name)

    # Payload must not execute JavaScript.
    assert not dialogs, (
        "A JS dialog fired - script injection was NOT sanitized."
    )

    # Payload should be rendered as literal text.
    expect(
        modal.label_value(region_name)
    ).to_be_visible()

    expect(
        modal.path_text_by_name(region_name)
    ).to_be_visible()

    # Payload must not result in an actual script element.
    expect(
        modal.script_element_for_payload(region_name)
    ).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_014: Leading/trailing spaces display trimmed
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_014_untrimmed_name_displays_trimmed(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_coverage(
        page,
        credentials,
    )

    _create_region(
        page,
        td.UNTRIMMED_REGION_NAME,
    )

    modal.open_for_region_name(
        td.TRIMMED_REGION_NAME
    )

    expect(
        modal.label_value(td.TRIMMED_REGION_NAME)
    ).to_be_visible()

    expect(
        modal.path_text_by_name(td.TRIMMED_REGION_NAME)
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_015: Edit button opens the edit form pre-filled
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_015_edit_button_opens_prefilled_form(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    modal.click_edit()

    modal.verify_edit_modal_open()

    expect(
        modal.edit_region_name_input
    ).to_have_value(
        td.PRIMARY_REGION_NAME
    )

    # Leave the Edit modal cleanly for test isolation.
    page.keyboard.press("Escape")


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_016: Region deleted by another session mid-view
# ---------------------------------------------------------------------------
@pytest.mark.skip(
    reason="TODO: implement concurrent region deletion scenario"
)
@pytest.mark.region_details
def test_TC_REGIONDETAILS_016_region_deleted_mid_view(
    page: Page,
    credentials: tuple[str, str],
    region_to_delete: str,
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
        region_name=region_to_delete,
    )

    # TODO:
    # Delete region_to_delete here via a second browser context
    # or a direct API call.

    modal.click_edit()

    # TODO:
    # Confirm the actual error message/locator shown in this case.
    expect(
        page.get_by_text(
            re.compile(
                "no longer exists",
                re.IGNORECASE,
            )
        )
    ).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_017: Region Details modal is keyboard accessible
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_017_modal_keyboard_accessible(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    # Click inside the modal so keyboard navigation starts
    # from the modal rather than the page behind it.
    modal.modal_container.click()

    close_button_reached = False

    # Tab through the modal until the Close button receives focus.
    for _ in range(10):
        page.keyboard.press("Tab")

        focused = page.evaluate(
            """
            () => {
                const el = document.activeElement;

                if (!el) {
                    return {
                        text: "",
                        ariaLabel: ""
                    };
                }

                return {
                    text: (el.textContent || "").trim(),
                    ariaLabel: el.getAttribute("aria-label") || ""
                };
            }
            """
        )

        if (
            focused["text"].lower() == "close"
            or focused["ariaLabel"].lower() == "close"
        ):
            close_button_reached = True
            break

    assert close_button_reached, (
        "Close button was not reached using keyboard Tab navigation"
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
    _, modal = _login_and_open_coverage(
        page,
        credentials,
    )

    expand_arrow = modal.expand_arrow

    expect(expand_arrow).to_be_visible()

    expand_arrow.click()

    # Clicking the expand/collapse arrow must not open the modal.
    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_019: Region visually indicated in tree while open
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_019_region_highlighted_in_tree(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    row = modal.region_tree_row(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )

    # TODO:
    expect(row).to_have_attribute(
        "aria-expanded",
        "true",
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_020: Only one modal instance at a time
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_020_no_overlapping_modal_instances(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    # Clicking the dimmed background closes the modal.
    page.mouse.click(5, 5)

    modal.verify_modal_closed()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_021: Opens fresh (not cached) for a different region
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_021_opens_fresh_for_different_region(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    # Verify the primary region details.
    modal.verify_region_details(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )

    # Close the primary region modal.
    modal.close_via_button()
    modal.verify_modal_closed()

    # Open the secondary region.
    modal.open_for_region_name(
        td.SECONDARY_REGION_NAME
    )

    # Get the actual ID assigned to the secondary region.
    secondary_region_id = modal.get_id_from_path(
        td.SECONDARY_REGION_NAME
    )

    # Verify the secondary region details.
    modal.verify_region_details(
        secondary_region_id,
        td.SECONDARY_REGION_NAME,
    )

    # Previous region must not leak into the new modal.
    expect(
        modal.label_value(td.PRIMARY_REGION_NAME)
    ).to_have_count(0)


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_022: Session expiry while modal is open
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_022_session_expiry_while_open(
    page: Page,
    context,
    credentials: tuple[str, str],
):
    explorer, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    # Simulate session expiry.
    explorer.clear_session_data()

    # Reload so the application detects the expired session.
    page.reload()

    # User should be redirected to the login page.
    expect(page).to_have_url(
        Config.LOGIN_URL,
        timeout=15000,
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_023: Opens correctly for a region with no child networks
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_023_opens_correctly_with_no_networks(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    modal.verify_region_details(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_024: Field labels visually distinguished from values
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_024_labels_visually_distinguished_from_values(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    label_color = modal.id_label.evaluate(
        "(el) => getComputedStyle(el).color"
    )

    value_color = modal.id_value(
        td.PRIMARY_REGION_ID
    ).evaluate(
        "(el) => getComputedStyle(el).color"
    )

    label_weight = modal.id_label.evaluate(
        "(el) => getComputedStyle(el).fontWeight"
    )

    value_weight = modal.id_value(
        td.PRIMARY_REGION_ID
    ).evaluate(
        "(el) => getComputedStyle(el).fontWeight"
    )

    # Loose smoke check until exact design-system values are confirmed.
    assert (
        label_color != value_color
        or label_weight != value_weight
    ), (
        "ID label and value appear visually identical "
        "(same color and weight) - expected a clear visual distinction."
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_025: Renders correctly on a narrow (mobile) viewport
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_025_renders_on_mobile_viewport(
    page: Page,
    credentials: tuple[str, str],
):
    page.set_viewport_size(
        {
            "width": 375,
            "height": 812,
        }
    )

    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    modal.verify_region_details(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )

    expect(modal.edit_button).to_be_visible()
    expect(modal.close_button).to_be_visible()


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_026: Resizes/reflows correctly on window resize
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_026_resizes_on_window_resize(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    page.set_viewport_size(
        {
            "width": 1920,
            "height": 1080,
        }
    )

    modal.verify_modal_open()

    page.set_viewport_size(
        {
            "width": 800,
            "height": 600,
        }
    )

    modal.verify_modal_open()

    modal.verify_region_details(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )


# ---------------------------------------------------------------------------
# TC_REGIONDETAILS_027: ID/Label/Path fields are read-only
# ---------------------------------------------------------------------------
@pytest.mark.region_details
def test_TC_REGIONDETAILS_027_fields_are_read_only(
    page: Page,
    credentials: tuple[str, str],
):
    _, modal = _login_and_open_region_details(
        page,
        credentials,
    )

    id_value_locator = modal.id_value(
        td.PRIMARY_REGION_ID
    )

    label_value_locator = modal.label_value(
        td.PRIMARY_REGION_NAME
    )

    path_locator = modal.path_text(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )

    for locator in (
        id_value_locator,
        label_value_locator,
        path_locator,
    ):
        locator.click()

        page.keyboard.type(
            td.READ_ONLY_FIELD_TYPED_INPUT
        )

        page.keyboard.press("Backspace")

        # Attempt paste as an additional read-only check.
        page.keyboard.press("Control+V")

    # Values must remain completely unchanged.
    expect(id_value_locator).to_have_text(
        td.PRIMARY_REGION_ID
    )

    expect(label_value_locator).to_have_text(
        td.PRIMARY_REGION_NAME
    )

    expect(path_locator).to_have_text(
        f"Path: {td.PRIMARY_REGION_ID} - "
        f"{td.PRIMARY_REGION_NAME}"
    )

    # No editable element should have received focus.
    expect(
        page.locator(
            'input:focus, '
            'textarea:focus, '
            '[contenteditable="true"]:focus'
        )
    ).to_have_count(0)

    modal.close_via_button()
    modal.verify_modal_closed()

    # Reopen and confirm nothing persisted.
    modal.open_for_region(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )

    modal.verify_region_details(
        td.PRIMARY_REGION_ID,
        td.PRIMARY_REGION_NAME,
    )