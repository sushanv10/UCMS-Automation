"""
Automation suite for TC_NAVBAR_001 - TC_NAVBAR_060.

Locators live in pages/nav_bar.py. Locators confirmed via Playwright Codegen
against the real app are used as-is; anywhere the real locator wasn't
captured, a best-effort guess is used and flagged with a `# TODO` comment in
nav_bar.py - replace those before trusting the corresponding test.

Additional fixtures this suite assumes exist in conftest.py (beyond the
`page` and `credentials` fixtures already used elsewhere in the project):

    restricted_credentials  -> tuple[str, str]
        Login for a role with at least one module (e.g. Outages / Port
        Allocations) hidden, used by TC_017, TC_018, TC_059.

    long_name_credentials   -> tuple[str, str]
        Login for a user whose display name/email is unusually long, used by
        TC_041.

    restricted_module_url   -> str  (or add to Config)
        A URL for a module the `restricted_credentials` user cannot access,
        used by TC_018.

Config is also assumed to gain the following URL constants alongside the
existing LOGIN_URL / DASHBOARD_URL / NETWORK_EXPLORER_URL:
    CATALOG_URL, ACCESS_NETWORK_URL, PORT_TRACE_URL, PORT_ALLOCATIONS_URL,
    OUTAGES_URL, ADMINISTRATION_URL

Several test cases (TC_055 screen-reader announcements, TC_056 color
contrast) are not meaningfully verifiable with plain Playwright assertions
and are marked `pytest.mark.skip` with guidance on the right tool instead
(e.g. axe-core / Playwright's accessibility snapshot, or a contrast checker)
rather than being faked with a shallow assertion.
"""

import pytest
from playwright.sync_api import Page, expect

from config.config import Config
from pages.login_page import LoginPage
from pages.nav_bar import NavBar
from test_data.nav_bar_test_data import URL_ACCESS_DENIED


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------
def _login(page: Page, credentials: tuple[str, str]) -> tuple[LoginPage, NavBar]:
    """Log in and return ready-to-use LoginPage / NavBar page objects."""
    login_page = LoginPage(page)
    nav_bar = NavBar(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)
    login_page.verify_login_successful()

    return login_page, nav_bar


# ---------------------------------------------------------------------------
# SECTION A: Logo / Brand (TC_001 - TC_003)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_001_logo_and_app_name_display_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    login_page = LoginPage(page)
    nav_bar = NavBar(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)

    expect(page).to_have_url(Config.NETWORK_EXPLORER_URL)
    nav_bar.verify_logo_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_002_logo_navigates_to_network_explorer(
    page: Page,
    credentials: tuple[str, str],
):
    login_page, nav_bar = _login(page, credentials)

    # Navigate away first so the click is a meaningful assertion.
    page.goto(Config.DASHBOARD_URL, wait_until="domcontentloaded")
    expect(page).to_have_url(Config.DASHBOARD_URL, timeout=15000)

    nav_bar.verify_logo_visible()
    nav_bar.click_logo()

    nav_bar.verify_network_explorer_url()
    nav_bar.verify_network_explorer_active()


@pytest.mark.navbar
def test_TC_NAVBAR_003_logo_click_on_network_explorer(
    page: Page,
    credentials: tuple[str, str],
):
    login_page, nav_bar = _login(page, credentials)

    nav_bar.verify_network_explorer_url()
    nav_bar.verify_network_explorer_active()

    nav_bar.click_logo()

    nav_bar.verify_network_explorer_url()
    nav_bar.verify_network_explorer_active()
    nav_bar.verify_logo_visible()


# ---------------------------------------------------------------------------
# SECTION B: Primary nav links (TC_004 - TC_016)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_004_all_primary_nav_links_present_and_labeled(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.verify_direct_nav_links_visible()
    nav_bar.verify_more_menu_contains("Port Trace", "Catalog")


@pytest.mark.navbar
def test_TC_NAVBAR_005_clicking_dashboard_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Dashboard")

    nav_bar.verify_url(Config.DASHBOARD_URL)
    nav_bar.verify_nav_link_active("Dashboard")


@pytest.mark.navbar
def test_TC_NAVBAR_006_clicking_network_explorer_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    page.goto(Config.DASHBOARD_URL, wait_until="domcontentloaded")
    expect(page).to_have_url(Config.DASHBOARD_URL, timeout=15000)
    nav_bar.click_nav_link("Network Explorer")

    nav_bar.verify_network_explorer_url()
    nav_bar.verify_network_explorer_active()


@pytest.mark.navbar
def test_TC_NAVBAR_007_clicking_catalog_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    # Catalog lives inside the "More" overflow menu.
    nav_bar.click_nav_link("Catalog")

    nav_bar.verify_url(Config.CATALOG_URL)
    nav_bar.verify_nav_link_active("Catalog")


@pytest.mark.navbar
def test_TC_NAVBAR_008_clicking_access_network_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Access Network")

    nav_bar.verify_url(Config.ACCESS_NETWORK_URL)
    nav_bar.verify_nav_link_active("Access Network")


@pytest.mark.navbar
def test_TC_NAVBAR_009_clicking_port_trace_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    # Port Trace lives inside the "More" overflow menu.
    nav_bar.click_nav_link("Port Trace")

    nav_bar.verify_url(Config.PORT_TRACE_URL)
    nav_bar.verify_nav_link_active("Port Trace")


@pytest.mark.navbar
def test_TC_NAVBAR_010_clicking_port_allocations_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Port Allocations")

    nav_bar.verify_url(Config.PORT_ALLOCATIONS_URL)
    nav_bar.verify_nav_link_active("Port Allocations")


@pytest.mark.navbar
def test_TC_NAVBAR_011_clicking_outages_navigates_correctly(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Outages")

    nav_bar.verify_url(Config.OUTAGES_URL)
    nav_bar.verify_nav_link_active("Outages")


@pytest.mark.navbar
def test_TC_NAVBAR_012_active_page_is_visually_highlighted(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Network Explorer")

    nav_bar.verify_nav_link_active("Network Explorer")
    # Cross-check an inactive link does NOT carry the same attribute.
    expect(nav_bar.dashboard_nav).not_to_have_attribute("aria-current", "page")


@pytest.mark.navbar
def test_TC_NAVBAR_013_direct_url_navigation_highlights_correct_nav_item(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    page.goto(Config.CATALOG_URL, wait_until="domcontentloaded")

    nav_bar.verify_url(Config.CATALOG_URL)
    nav_bar.verify_nav_link_active("Catalog")


@pytest.mark.navbar
def test_TC_NAVBAR_014_clicking_active_nav_item_again_no_errors(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.verify_network_explorer_url()
    nav_bar.click_nav_link("Network Explorer")

    nav_bar.verify_network_explorer_url()
    nav_bar.verify_network_explorer_active()
  


@pytest.mark.navbar
def test_TC_NAVBAR_015_nav_bar_remains_sticky_while_scrolling(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    box_before = nav_bar.ucms_logo.bounding_box()
    page.mouse.wheel(0, 2000)
    page.wait_for_timeout(300)
    box_after = nav_bar.ucms_logo.bounding_box()

    expect(nav_bar.ucms_logo).to_be_visible()
    assert box_before is not None and box_after is not None
    assert box_before["y"] == box_after["y"], (
        "Nav bar (logo) position shifted vertically after scrolling; "
        "it should remain fixed/sticky at the top."
    )


@pytest.mark.navbar
def test_TC_NAVBAR_016_nav_bar_consistent_across_all_pages(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    for label in ("Dashboard", "Network Explorer", "Access Network",
                  "Port Allocations", "Outages", "Port Trace", "Catalog"):
        nav_bar.click_nav_link(label)
        nav_bar.verify_logo_visible()
        nav_bar.verify_direct_nav_links_visible()
        expect(nav_bar.open_command_palette_button).to_be_visible()
        expect(nav_bar.account_menu_button_default_user).to_be_visible()


# ---------------------------------------------------------------------------
# SECTION C: Role-based visibility (TC_017 - TC_018)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_017_restricted_role_hides_unauthorized_nav_links(
    page: Page,
    restricted_credentials: tuple[str, str],
):
    _, nav_bar = _login(page, restricted_credentials)

    nav_bar.verify_nav_link_hidden("Port Allocations")
    nav_bar.verify_nav_link_hidden("Outages")

   
    # Open the restricted user's account menu
    nav_bar.open_account_menu()
    nav_bar.verify_account_menu_open()
    nav_bar.verify_administration_hidden()


@pytest.mark.navbar
def test_TC_NAVBAR_018_direct_url_to_restricted_module_is_blocked(
    page: Page,
    restricted_credentials: tuple[str, str],  # TODO: add fixture in conftest.py
):
    _, nav_bar = _login(page, restricted_credentials)

    # TODO: replace with Config.PORT_ALLOCATIONS_URL (or the correct
    # restricted module URL for this test account).
    page.goto(Config.PORT_ALLOCATIONS_URL, wait_until="domcontentloaded")

    expect(page).to_have_url(Config.PORT_ALLOCATIONS_URL, timeout=15000)

    expect(
        page.get_by_text(
            URL_ACCESS_DENIED,
            exact=True,
    )).to_be_visible(timeout=15000)


# ---------------------------------------------------------------------------
# SECTION D: Global search entry points (TC_019 - TC_023)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_019_search_bar_placeholder_and_shortcut_hint(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    expect(nav_bar.open_command_palette_button).to_be_visible()
    expect(page.get_by_text("Ctrl+K", exact=True)).to_be_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_020_clicking_search_bar_opens_command_palette(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()

    nav_bar.verify_command_palette_open()


@pytest.mark.navbar
def test_TC_NAVBAR_021_ctrl_k_opens_command_palette_from_anywhere(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Access Network")
    
    nav_bar.open_command_palette_via_shortcut()

    nav_bar.verify_command_palette_open()


@pytest.mark.navbar
def test_TC_NAVBAR_022_ctrl_k_while_focus_in_another_text_field(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Catalog")
    # TODO: replace with a real text field locator from another page object,
    # e.g. the Catalog "Add Network" modal's Network Name input.
    some_text_field = page.get_by_placeholder("e.g., Lalitpur")  # TODO
    some_text_field.click()
    some_text_field.type("Partially typed text")

    nav_bar.open_command_palette_via_shortcut()

    nav_bar.verify_command_palette_open()
    # The other field's in-progress text should not be lost.
    expect(some_text_field).to_have_value("Partially typed text")


@pytest.mark.navbar
def test_TC_NAVBAR_023_esc_badge_hint_closes_command_palette(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.verify_command_palette_open()
    expect(nav_bar.esc_badge).to_be_visible()

    nav_bar.close_command_palette_via_escape()

    nav_bar.verify_command_palette_closed()


# ---------------------------------------------------------------------------
# SECTION E: Search modal contents & interaction (TC_024 - TC_037)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_024_default_search_state_lists_all_available_items(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()

    nav_bar.verify_default_result_list_contents()


@pytest.mark.navbar
def test_TC_NAVBAR_025_each_result_shows_icon_label_and_category_tag(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()

    expect(nav_bar.result_network_explorer).to_be_visible()
    expect(nav_bar.result_network_explorer).to_contain_text("Modules")
    expect(nav_bar.result_ui_kit).to_be_visible()
    expect(nav_bar.result_ui_kit).to_contain_text("Design system review")
    # TODO: confirm a locator for the icon element itself (e.g. an <svg> or
    # data-icon attribute) if per-icon verification is required.


@pytest.mark.navbar
def test_TC_NAVBAR_026_typing_query_filters_results_in_real_time(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("Port")

    expect(nav_bar.result_port_trace).to_be_visible()
    expect(nav_bar.result_port_allocations).to_be_visible()
    expect(nav_bar.result_dashboard).to_be_hidden()
    expect(nav_bar.result_catalog).to_be_hidden()


@pytest.mark.navbar
def test_TC_NAVBAR_027_search_is_case_insensitive(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("CATALOG")

    expect(nav_bar.result_catalog).to_be_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_028_no_matching_results_shows_empty_state(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("zzzxyz123")

    nav_bar.verify_search_no_results()


@pytest.mark.navbar
def test_TC_NAVBAR_029_search_input_sanitized_against_injection(
    page: Page,
    credentials: tuple[str, str],
):
    dialogs: list[str] = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))

    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("<script>alert(1)</script>")

    assert not dialogs, "A JS dialog fired - script injection was NOT sanitized."
    # Payload should be treated as literal search text with no matches.
    nav_bar.verify_search_no_results()


@pytest.mark.navbar
def test_TC_NAVBAR_030_arrow_keys_navigate_result_list(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.press_arrow_down(times=2)

    # TODO: confirm the actual attribute/class used to mark the highlighted
    # row (e.g. aria-selected="true", data-highlighted, or a CSS class).
    highlighted = page.locator('[aria-selected="true"]')  # TODO
    expect(highlighted).to_have_count(1)


@pytest.mark.navbar
def test_TC_NAVBAR_031_enter_key_opens_highlighted_result(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("Access Network")
    nav_bar.press_arrow_down(times=1)  # highlight the single filtered result

    nav_bar.press_enter()

    nav_bar.verify_url(Config.ACCESS_NETWORK_URL)
    nav_bar.verify_command_palette_closed()


@pytest.mark.navbar
def test_TC_NAVBAR_032_clicking_result_with_mouse_navigates_and_closes(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.click_module_result("Outages")

    nav_bar.verify_url(Config.OUTAGES_URL)
    nav_bar.verify_command_palette_closed()


@pytest.mark.navbar
def test_TC_NAVBAR_033_result_list_scrolls_when_overflowing(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.verify_default_result_list_contents()

    # Scrolling within the palette's results container should reveal the
    # later items without breaking the modal's own layout/size.
    # TODO: confirm the scroll-container locator - falling back to the
    # last known result as a scroll target.
    nav_bar.result_admin_activity_audit.scroll_into_view_if_needed()
    expect(nav_bar.result_admin_activity_audit).to_be_visible()
    expect(nav_bar.command_palette).to_be_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_034_results_correctly_categorize_modules_vs_other_types(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()

    expect(nav_bar.result_dashboard).to_contain_text("Modules")
    expect(nav_bar.result_ui_kit).to_be_visible()  # tagged "Design" per spec
    expect(nav_bar.result_catalog_regions).to_contain_text("Catalog")
    expect(nav_bar.result_olt_inventory).to_contain_text("Access Network")
    expect(nav_bar.result_admin_users).to_contain_text("Administration")


@pytest.mark.navbar
def test_TC_NAVBAR_035_clearing_search_restores_default_list(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("Port")
    expect(nav_bar.result_dashboard).to_be_hidden()

    nav_bar.clear_search()

    nav_bar.verify_default_result_list_contents()


@pytest.mark.navbar
def test_TC_NAVBAR_036_clicking_outside_search_modal_closes_it(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.verify_command_palette_open()

    nav_bar.close_command_palette_via_outside_click()

    nav_bar.verify_command_palette_closed()
    nav_bar.verify_network_explorer_url()


@pytest.mark.navbar
def test_TC_NAVBAR_037_search_modal_opens_fresh_each_time(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("Outages")
    nav_bar.close_command_palette_via_escape()

    nav_bar.open_command_palette_via_click()

    expect(nav_bar.search_input).to_have_value("")
    nav_bar.verify_default_result_list_contents()


# ---------------------------------------------------------------------------
# SECTION F: User account menu (TC_038 - TC_049)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_038_user_avatar_displays_correct_initials(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    expect(nav_bar.account_menu_button_default_user).to_be_visible()
    # TODO: confirm the initials text is exposed as its own text node vs.
    # only present within the accessible name used above.
    expect(nav_bar.account_menu_button_default_user).to_contain_text("SV")


@pytest.mark.navbar
def test_TC_NAVBAR_039_clicking_avatar_opens_profile_dropdown(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()

    nav_bar.verify_account_menu_open()
    expect(nav_bar.administration_menuitem).to_be_visible()
    expect(nav_bar.sign_out_menuitem).to_be_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_040_profile_dropdown_shows_correct_name_and_email(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()

    nav_bar.verify_account_menu_name_and_email(
        name="Sushan Vaidya",
        email="sushanv3@gmail.com",
    )


@pytest.mark.navbar
def test_TC_NAVBAR_041_profile_dropdown_handles_long_name_gracefully(
    page: Page,
    long_name_credentials: tuple[str, str],  # TODO: add fixture in conftest.py
):
    _, nav_bar = _login(page, long_name_credentials)

    nav_bar.open_account_menu(display_name="Bishwo Raj Shrestha Chettri Wagle Dangol")

    nav_bar.verify_account_menu_open()
    box = nav_bar.account_menu.bounding_box()
    viewport = page.viewport_size
    assert box is not None and viewport is not None
    assert box["x"] + box["width"] <= viewport["width"] + 1, (
        "Profile dropdown overflowed the viewport with a long user name."
    )


@pytest.mark.navbar
def test_TC_NAVBAR_042_clicking_administration_navigates_to_admin_section(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()
    nav_bar.click_administration()

    # TODO: add ADMINISTRATION_URL to Config.
    nav_bar.verify_url(Config.ADMINISTRATION_URL)
    nav_bar.verify_account_menu_closed()


@pytest.mark.navbar
def test_TC_NAVBAR_043_administration_hidden_for_non_admin_users(
    page: Page,
    restricted_credentials: tuple[str, str],  # TODO: add fixture in conftest.py
):
    _, nav_bar = _login(page, restricted_credentials)

    nav_bar.open_account_menu(display_name="Restricted User")  # TODO: real display name

    nav_bar.verify_administration_hidden()


@pytest.mark.navbar
def test_TC_NAVBAR_044_sign_out_logs_out_and_redirects_to_login(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()
    nav_bar.click_sign_out()

    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)

    page.go_back()
    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)


@pytest.mark.navbar
def test_TC_NAVBAR_045_sign_out_clears_session_tokens(
    page: Page,
    context,  # Playwright BrowserContext fixture
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    cookies_before = context.cookies()
    assert cookies_before, "Expected at least one auth-related cookie before sign-out."

    nav_bar.open_account_menu()
    nav_bar.click_sign_out()
    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)

    cookies_after = context.cookies()
    local_storage_after = page.evaluate("() => Object.keys(window.localStorage)")

    # TODO: tighten this assertion to check the *specific* auth cookie/token
    # name(s) used by the app, once known, rather than a broad diff.
    assert cookies_after != cookies_before, (
        "Cookies were unchanged after sign-out; session may not have been cleared."
    )
    assert not any("token" in key.lower() for key in local_storage_after), (
        f"Auth-looking token(s) still present in localStorage after sign-out: {local_storage_after}"
    )


@pytest.mark.navbar
def test_TC_NAVBAR_046_rapid_double_click_sign_out_no_errors(
    page: Page,
    credentials: tuple[str, str],
):
    page_errors: list[str] = []
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()
    expect(nav_bar.sign_out_menuitem).to_be_visible()
    # Fire two clicks back-to-back without waiting for navigation in between.
    nav_bar.sign_out_menuitem.click()
    try:
        nav_bar.sign_out_menuitem.click(timeout=1000)
    except Exception:
        pass  # Expected: element likely already gone/navigated away.

    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)
    assert not page_errors, f"Unexpected page errors on double sign-out: {page_errors}"


@pytest.mark.navbar
def test_TC_NAVBAR_047_clicking_outside_dropdown_closes_it(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()
    nav_bar.verify_account_menu_open()

    page.mouse.click(5, 5)

    nav_bar.verify_account_menu_closed()
    nav_bar.verify_network_explorer_url()


@pytest.mark.navbar
def test_TC_NAVBAR_048_escape_closes_profile_dropdown(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_account_menu()
    nav_bar.verify_account_menu_open()

    page.keyboard.press("Escape")

    nav_bar.verify_account_menu_closed()


@pytest.mark.navbar
def test_TC_NAVBAR_049_only_one_overlay_open_at_a_time(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.verify_command_palette_open()

    # Attempt to open the account menu while the palette overlay is up.
    try:
        nav_bar.account_menu_button_default_user.click(timeout=1000)
    except Exception:
        pass  # Acceptable: overlay may intercept the click entirely.

    # Either the palette is still open and the dropdown never appeared, or
    # the palette closed first and only the dropdown is now open - the two
    # must never both be visible simultaneously.
    palette_visible = nav_bar.command_palette.is_visible()
    menu_visible = nav_bar.account_menu.is_visible()
    assert not (palette_visible and menu_visible), (
        "Both the search palette and the account menu were visible at once."
    )


# ---------------------------------------------------------------------------
# SECTION G: Responsiveness (TC_050 - TC_052)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_050_nav_collapses_into_more_menu_on_narrow_viewport(
    page: Page,
    credentials: tuple[str, str],
):
    page.set_viewport_size({"width": 375, "height": 812})
    _, nav_bar = _login(page, credentials)

    nav_bar.verify_more_menu_visible()
    nav_bar.verify_logo_visible()
    expect(nav_bar.open_command_palette_button).to_be_visible()
    expect(nav_bar.account_menu_button_default_user).to_be_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_051_all_links_reachable_via_more_menu_on_mobile(
    page: Page,
    credentials: tuple[str, str],
):
    page.set_viewport_size({"width": 375, "height": 812})
    _, nav_bar = _login(page, credentials)

    for label in nav_bar.ALL_NAV_LABELS_IN_ORDER:
        nav_bar.verify_nav_link_visible(label)


@pytest.mark.navbar
def test_TC_NAVBAR_052_nav_bar_usable_on_tablet_viewport(
    page: Page,
    credentials: tuple[str, str],
):
    page.set_viewport_size({"width": 768, "height": 1024})
    _, nav_bar = _login(page, credentials)

    nav_bar.verify_logo_visible()
    expect(nav_bar.open_command_palette_button).to_be_visible()
    expect(nav_bar.account_menu_button_default_user).to_be_visible()
    nav_bar.click_nav_link("Dashboard")
    nav_bar.verify_url(Config.DASHBOARD_URL)


# ---------------------------------------------------------------------------
# SECTION H: Accessibility & keyboard navigation (TC_053 - TC_056)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_053_nav_bar_fully_navigable_by_keyboard(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    page.keyboard.press("Tab")
    focused_tag = page.evaluate("() => document.activeElement.tagName")
    assert focused_tag is not None

    # TODO: this loop is a smoke check, not an exhaustive focus-order audit -
    # tighten by asserting the *specific* expected sequence of elements
    # (logo -> each nav link -> search -> avatar) once locators/order are
    # fully confirmed.
    for _ in range(10):
        page.keyboard.press("Tab")
    focused_role = page.evaluate(
        "() => document.activeElement.getAttribute('role') || document.activeElement.tagName"
    )
    assert focused_role, "No element retained focus after tabbing through the nav bar."


@pytest.mark.navbar
def test_TC_NAVBAR_054_search_modal_traps_focus(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.open_command_palette_via_click()

    for _ in range(15):
        page.keyboard.press("Tab")

    focus_inside_modal = page.evaluate(
        """() => {
            const modal = document.querySelector('[aria-label="Command palette"]');
            return modal ? modal.contains(document.activeElement) : false;
        }"""
    )  # TODO: confirm the modal's actual root selector matches this query
    assert focus_inside_modal, "Keyboard focus escaped the search modal while it was open."


@pytest.mark.navbar
@pytest.mark.skip(
    reason=(
        "Screen-reader announcement quality is not reliably verifiable with "
        "plain Playwright assertions. Recommend auditing with an "
        "accessibility-tree snapshot (page.accessibility.snapshot()) or an "
        "axe-core integration (e.g. axe-playwright) instead, and/or a manual "
        "pass with NVDA/VoiceOver."
    )
)
def test_TC_NAVBAR_055_nav_bar_has_accessible_labels(
    page: Page,
    credentials: tuple[str, str],
):
    pass


@pytest.mark.navbar
@pytest.mark.skip(
    reason=(
        "Color-contrast ratio requires reading computed styles and running a "
        "WCAG contrast calculation (e.g. via axe-core's color-contrast rule), "
        "not a simple Playwright locator assertion. Recommend wiring in "
        "axe-playwright and asserting zero 'color-contrast' violations."
    )
)
def test_TC_NAVBAR_056_active_inactive_links_meet_contrast_standards(
    page: Page,
    credentials: tuple[str, str],
):
    pass


# ---------------------------------------------------------------------------
# SECTION I: Cross-cutting / edge cases (TC_057 - TC_060)
# ---------------------------------------------------------------------------
@pytest.mark.navbar
def test_TC_NAVBAR_057_nav_bar_renders_correctly_immediately_after_login(
    page: Page,
    credentials: tuple[str, str],
):
    login_page = LoginPage(page)
    nav_bar = NavBar(page)
    username, password = credentials

    login_page.navigate()
    login_page.verify_login_page_visible()
    login_page.login(username, password)

    login_page.verify_login_successful()
    nav_bar.verify_logo_visible()
    nav_bar.verify_direct_nav_links_visible()
    expect(nav_bar.open_command_palette_button).to_be_visible()
    expect(nav_bar.account_menu_button_default_user).to_be_visible()


@pytest.mark.navbar
def test_TC_NAVBAR_058_nav_actions_handled_correctly_after_session_expiry(
    page: Page,
    context,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    # Simulate session/token expiry by wiping cookies and storage.
    # TODO: if the app uses a specific auth cookie/token name, clearing only
    # that one (rather than everything) may be a more faithful simulation of
    # server-side expiry than clearing all client storage.
    context.clear_cookies()
    page.evaluate("() => { window.localStorage.clear(); window.sessionStorage.clear(); }")

    nav_bar.click_nav_link("Dashboard")

    expect(page).to_have_url(Config.LOGIN_URL, timeout=15000)


@pytest.mark.navbar
def test_TC_NAVBAR_059_search_never_exposes_restricted_modules(
    page: Page,
    restricted_credentials: tuple[str, str],  # TODO: add fixture in conftest.py
):
    _, nav_bar = _login(page, restricted_credentials)

    nav_bar.open_command_palette_via_click()
    nav_bar.type_in_search("Outages")  # TODO: use the actual restricted module name

    expect(nav_bar.result_outages).to_be_hidden()
    nav_bar.verify_search_no_results()


@pytest.mark.navbar
def test_TC_NAVBAR_060_browser_back_forward_keeps_nav_highlighting_in_sync(
    page: Page,
    credentials: tuple[str, str],
):
    _, nav_bar = _login(page, credentials)

    nav_bar.click_nav_link("Dashboard")
    nav_bar.verify_nav_link_active("Dashboard")

    nav_bar.click_nav_link("Catalog")
    nav_bar.verify_nav_link_active("Catalog")

    page.go_back()

    nav_bar.verify_url(Config.DASHBOARD_URL)
    nav_bar.verify_nav_link_active("Dashboard")