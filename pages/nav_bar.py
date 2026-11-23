import re

from playwright.sync_api import Page, Locator, expect
from config.config import Config


class NavBar:
    def __init__(self, page: Page):
        self.page = page
        # -----------------------------------------------------------
        # Logo
        # -----------------------------------------------------------
        self.ucms_logo = page.get_by_role("link", name="UCMS UCMS")

        # -----------------------------------------------------------
        # Primary nav links - CONFIRMED (always directly visible)
        # -----------------------------------------------------------
        self.dashboard_nav = page.get_by_role("link", name="Dashboard")
        self.network_explorer_nav = page.get_by_role("link", name="Network Explorer", exact=True)
        self.access_network_nav = page.get_by_role("link", name="Access Network", exact=True)
        self.port_allocations_nav = page.get_by_role("link", name="Port Allocations")
        self.outages_nav = page.get_by_role("link", name="Outages")

        # -----------------------------------------------------------
        # Overflow ("More") nav links - CONFIRMED
        # -----------------------------------------------------------
        self.more_nav_button = page.get_by_role("button", name="More")
        self.port_trace_nav = page.get_by_role("link", name="Port Trace")
        self.catalog_nav = page.get_by_role("link", name="Catalog")

        # Lookup tables used by the generic helper methods below.
        self._direct_nav_locators: dict[str, Locator] = {
            "Dashboard": self.dashboard_nav,
            "Network Explorer": self.network_explorer_nav,
            "Access Network": self.access_network_nav,
            "Port Allocations": self.port_allocations_nav,
            "Outages": self.outages_nav,
        }
        self._overflow_nav_locators: dict[str, Locator] = {
            "Port Trace": self.port_trace_nav,
            "Catalog": self.catalog_nav,
        }
    
        self.ALL_NAV_LABELS_IN_ORDER = [
            "Dashboard",
            "Network Explorer",
            "Access Network",
            "Port Allocations",
            "Outages",
            "Port Trace",   # lives inside "More"
            "Catalog",      # lives inside "More"
            
        ]

        # -----------------------------------------------------------
        # Global command palette (search) - CONFIRMED
        # -----------------------------------------------------------
        self.open_command_palette_button = page.get_by_label("Open command palette")
        self.command_palette = page.get_by_label("Command palette", exact=True)
        self.search_input = page.get_by_role("textbox", name="Search modules, pages, and actions…")
        self.esc_badge = page.locator("div").filter(has_text=re.compile(r"^Esc$"))

        # Hamburger menu button (responsive nav)
        self.hamburger_menu_button = page.get_by_role("button", name="Open navigation menu")

        # TODO: confirm exact copy of the empty-state message.
        self.search_no_results_text = page.get_by_text(
            re.compile(r"no (results|matches)", re.IGNORECASE)
        )
        # TODO: confirm locators for the footer keyboard hints
        # (only referenced visually in the spec, not exercised by codegen).
        self.search_footer_navigate_hint = page.get_by_text(re.compile("navigate", re.IGNORECASE))
        self.search_footer_open_hint = page.get_by_text(re.compile(r"^open$", re.IGNORECASE))

        # Top-level module results - CONFIRMED accessible names.
        self.result_dashboard = page.get_by_role("button", name="Dashboard Modules")
        self.result_network_explorer = page.get_by_role("button", name="Network Explorer Modules")
        self.result_access_network = page.get_by_role("button", name="Access Network Modules")
        self.result_port_trace = page.get_by_role("button", name="Port Trace Modules")
        self.result_catalog = page.get_by_role("button", name="Catalog Modules")
        self.result_port_allocations = page.get_by_role("button", name="Port Allocations Modules")
        self.result_outages = page.get_by_role("button", name="Outages Modules")
        self.result_ui_kit = page.get_by_role("button", name="UI Kit Design system review")

        self._module_result_locators: dict[str, Locator] = {
            "Dashboard": self.result_dashboard,
            "Network Explorer": self.result_network_explorer,
            "Access Network": self.result_access_network,
            "Port Trace": self.result_port_trace,
            "Catalog": self.result_catalog,
            "Port Allocations": self.result_port_allocations,
            "Outages": self.result_outages,
        }

        # Deep-linked sub-page results - CONFIRMED accessible names.
        self.result_catalog_regions = page.get_by_role("button", name="Catalog · Regions Catalog")
        self.result_olt_inventory = page.get_by_role("button", name="OLT inventory Access Network")

        # Administration entry (with description) + its sub-items - name text
        # was truncated in the captured codegen output, so these use a
        # regex prefix match. TODO: confirm the exact full accessible names.
        self.result_administration = page.get_by_role(
            "button", name=re.compile(r"^Administration Users, roles,")
        )
        self.result_admin_users = page.get_by_role("button", name="Users Administration")
        # TODO: confirm full text - truncated to "Roles & permissions" in the
        # spec / "Roles & permissions" in codegen capture was cut off.
        self.result_admin_roles_permissions = page.get_by_role(
            "button", name=re.compile(r"^Roles")
        )
        self.result_admin_approval_queue = page.get_by_role(
            "button", name="Approval queue Administration"
        )
        self.result_admin_activity_audit = page.get_by_role(
            "button", name="Activity audit Administration"
        )

        # -----------------------------------------------------------
        # User account menu - CONFIRMED
        # -----------------------------------------------------------
        # NOTE: accessible name includes the logged-in user's display name.
        # Use `account_menu_button_for(name)` for a user other than the
        # default fixture user.
        # self._account_menu_label_template = "Account menu for {name}"
        # self.account_menu_button_default_user = page.get_by_label(
        #     f"Account menu for {Config.USER_FULL_NAME}"
        # )
        # self.account_menu_button_restrected_user = page.get_by_label(
        #     f"Account menu for {Config.RESTRICTED_USERNAME}"
        # )
        self.account_menu_button = page.get_by_label(
            re.compile(r"^Account menu for .+$")
        )

        self.account_menu = page.get_by_role("menu")
        self.administration_menuitem = page.get_by_role("menuitem", name="Administration")
        self.sign_out_menuitem = page.get_by_role("menuitem", name="Sign out")

        # self.account_menu_name_text = self.account_menu.get_by_text("Sushan Vaidya", exact=True)
        self.account_menu_email_text = self.account_menu.get_by_text(re.compile(r".+@.+\..+"))

    # =================================================================
    # Logo
    # =================================================================
    def verify_logo_visible(self):
        expect(self.ucms_logo).to_be_visible()

    def click_logo(self):
        expect(self.ucms_logo).to_be_visible()
        self.ucms_logo.click()

    # =================================================================
    # Primary + overflow nav links
    # =================================================================
    # def account_menu_button_for(self, display_name: str) -> Locator:
    #     """Account-menu trigger locator for an arbitrary user's display name."""
    #     return self.page.get_by_label(
    #         self._account_menu_label_template.format(name=display_name)
    #     )

    def _locator_for(self, name: str) -> Locator:
        locator = self._direct_nav_locators.get(name) or self._overflow_nav_locators.get(name)
        if locator is None:
            raise ValueError(f"Unknown nav link: {name!r}")
        return locator

    def verify_direct_nav_links_visible(self):
        """Verify the 5 always-visible nav links render, left to right."""
        for name in ("Dashboard", "Network Explorer", "Access Network",
                     "Port Allocations", "Outages"):
            expect(self._direct_nav_locators[name]).to_be_visible()

    def open_more_menu(self):
        expect(self.more_nav_button).to_be_visible()
        self.more_nav_button.click()

    def verify_more_menu_contains(self, *names: str):
        self.open_more_menu()
        for name in names:
            expect(self._overflow_nav_locators[name]).to_be_visible()

    def click_nav_link(self, name: str):
        """Click a primary nav link, opening the 'More' overflow menu first
        if the link currently lives there."""
        if name in self._overflow_nav_locators:
            self.open_more_menu()
        locator = self._locator_for(name)
        expect(locator).to_be_visible()
        locator.click()

    def verify_nav_link_visible(self, name: str):
        if name in self._overflow_nav_locators:
            self.open_more_menu()
        expect(self._locator_for(name)).to_be_visible()

    def verify_nav_link_hidden(self, name: str):
        """Used for role-based visibility tests (e.g. a restricted module)."""
        if name in self._overflow_nav_locators:
            self.open_more_menu()
        expect(self._locator_for(name)).to_have_count(0)

    def verify_network_explorer_active(self):
        expect(self.network_explorer_nav).to_be_visible()
        expect(self.network_explorer_nav).to_have_attribute("aria-current", "page")

    def verify_nav_link_active(self, name: str):
        if name in self._overflow_nav_locators:
            self.open_more_menu()
        expect(self._locator_for(name)).to_have_attribute("aria-current", "page")

    def verify_network_explorer_url(self):
        expect(self.page).to_have_url(Config.NETWORK_EXPLORER_URL, timeout=15000)

    def verify_url(self, expected_url: str):
        expect(self.page).to_have_url(expected_url, timeout=15000)

    # =================================================================
    # Command palette (search)
    # =================================================================
    def open_command_palette_via_click(self):
        expect(self.open_command_palette_button).to_be_visible()
        self.open_command_palette_button.click()

    def open_command_palette_via_shortcut(self):
        # TODO: confirm whether the app also supports Cmd+K on macOS runs -
        # if the CI only runs on Linux/Windows this is fine as-is.
        self.page.keyboard.press("Control+K")

    def close_command_palette_via_escape(self):
        self.page.keyboard.press("Escape")

    def close_command_palette_via_esc_badge_click(self):
        """The 'Esc' badge itself was clicked in the codegen trace - included
        in case clicking the badge (not just pressing the key) also closes
        the palette. TODO: confirm this is actually clickable/functional."""
        expect(self.esc_badge).to_be_visible()
        self.esc_badge.click()

    def close_command_palette_via_outside_click(self):
        # TODO: confirm a reliable "outside the palette" point - top-left
        # corner of the viewport is used here as a best guess.
        self.page.mouse.click(5, 5)

    def verify_command_palette_open(self):
        expect(self.command_palette).to_be_visible()
        expect(self.search_input).to_be_visible()
        expect(self.search_input).to_be_focused()

    def verify_command_palette_closed(self):
        expect(self.command_palette).to_be_hidden()

    def type_in_search(self, query: str):
        expect(self.search_input).to_be_visible()
        self.search_input.fill(query)

    def clear_search(self):
        self.search_input.fill("")

    def press_arrow_down(self, times: int = 1):
        for _ in range(times):
            self.page.keyboard.press("ArrowDown")

    def press_arrow_up(self, times: int = 1):
        for _ in range(times):
            self.page.keyboard.press("ArrowUp")

    def press_enter(self):
        self.page.keyboard.press("Enter")

    def click_search_result(self, result_locator: Locator):
        expect(result_locator).to_be_visible()
        result_locator.click()

    def click_module_result(self, name: str):
        locator = self._module_result_locators.get(name)
        if locator is None:
            raise ValueError(f"Unknown module search result: {name!r}")
        self.click_search_result(locator)

    def verify_search_no_results(self):
        expect(self.search_no_results_text).to_be_visible()

    def verify_default_result_list_contents(self):
        """Verify the rich default (pre-filter) result set: all 7 modules,
        the UI Kit design entry, both deep-linked sub-pages, and the
        Administration entry with its 4 sub-items."""
        for locator in self._module_result_locators.values():
            expect(locator).to_be_visible()
        expect(self.result_ui_kit).to_be_visible()
        expect(self.result_catalog_regions).to_be_visible()
        expect(self.result_olt_inventory).to_be_visible()
        expect(self.result_administration).to_be_visible()
        expect(self.result_admin_users).to_be_visible()
        expect(self.result_admin_roles_permissions).to_be_visible()
        expect(self.result_admin_approval_queue).to_be_visible()
        expect(self.result_admin_activity_audit).to_be_visible()

    # =================================================================
    # User account menu
    # =================================================================
    def open_account_menu(self):
        expect(self.account_menu_button).to_be_visible()
        self.account_menu_button.click()

    def verify_account_menu_open(self):
        expect(self.account_menu).to_be_visible()

    def verify_account_menu_closed(self):
        expect(self.account_menu).to_be_hidden()

    def verify_account_menu_name_and_email(self, name: str, email: str):
        expect(self.account_menu.get_by_text(name, exact=True)).to_be_visible()
        expect(self.account_menu.get_by_text(email, exact=True)).to_be_visible()

    def click_administration(self):
        expect(self.administration_menuitem).to_be_visible()
        self.administration_menuitem.click()

    def verify_administration_hidden(self):
        expect(self.administration_menuitem).to_have_count(0)

    def click_sign_out(self):
        expect(self.sign_out_menuitem).to_be_visible()
        self.sign_out_menuitem.click()

  
# Responsive / Hamburger navigation
# =================================================================

    def verify_hamburger_menu_visible(self):
        """
        Verify that the responsive hamburger navigation button is visible.
        """
        expect(
            self.hamburger_menu_button
        ).to_be_visible(timeout=10000)


    def click_hamburger_menu(self):
        """
        Open the responsive hamburger navigation menu.
        """
        expect(
            self.hamburger_menu_button
        ).to_be_visible(timeout=10000)

        self.hamburger_menu_button.click()

    def verify_responsive_nav_link_visible(self, name: str):
        """
        Verify that a navigation link is visible inside the
        responsive hamburger menu.

        Unlike the desktop navigation, this method does not
        open the desktop 'More' menu.
        """
        locator = self._locator_for(name)

        expect(
            locator
        ).to_be_visible(timeout=10000)
    

    def verify_all_responsive_nav_links_visible(self):
        """
        Verify all navigation links are visible after opening the
        responsive hamburger menu.
        """
        for name in self.ALL_NAV_LABELS_IN_ORDER:
            self.verify_responsive_nav_link_visible(name)