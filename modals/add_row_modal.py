"""
Page Object for the Catalog - Add Row modal.

Opened from a network row's '+' control in the Coverage panel of
Network Explorer.
"""
import re

from playwright.sync_api import Page, expect

from test_data import add_row_test_data as td


class AddRowModal:
    """
    Page Object for the Catalog - Add Row modal.

    Opened from a network row's '+' control in the Coverage panel of
    Network Explorer.
    """

    def __init__(self, page: Page):
        self.page = page

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        self.close_button = page.get_by_title("Close", exact=True)

        # Network context banner (read-only)
        self.network_banner = page.get_by_text(
            re.compile(r"^Creating row under network:\s*\S+", re.IGNORECASE)
        )

        # -----------------------------------------------------------
        # Form fields
        # -----------------------------------------------------------
        self.row_name_label = page.get_by_text(
            re.compile(r"^\s*Row Name\s*\*?\s*$")
        ).first
        self.row_name_input = page.locator("#add-row-label")

        self.details_label = page.get_by_text(
            re.compile(r"^\s*Details\s*\*?\s*$")
        ).first
        self.details_input = page.locator("#add-row-details")

        self.remarks_label = page.get_by_text(
            re.compile(r"^\s*Remarks\s*\*?\s*$")
        ).first
        self.remarks_input = page.locator("#add-row-remarks")

        self.coverage_area_label = page.get_by_text(td.COVERAGE_AREA_LABEL, exact=True)
        self.map_container = page.locator(".leaflet-container").last
        self.leaflet_zoom_in_button = page.locator("a.leaflet-control-zoom-in").last
        self.leaflet_zoom_out_button = page.locator("a.leaflet-control-zoom-out").last
        self.fullscreen_button = page.get_by_label("Enter fullscreen")
        self.exit_fullscreen_button = page.get_by_label("Exit fullscreen")
        self.active_checkbox = page.get_by_role(
            "checkbox", name=td.ACTIVE_CHECKBOX_LABEL, exact=True
        )

        # -----------------------------------------------------------
        # Actions
        # The modal submit is type="submit". Role-name "Add Row" may
        # also match other controls, so prefer type="submit".
        # -----------------------------------------------------------
        self.submit_button = page.locator('button[type="submit"]')
        self.cancel_button = page.get_by_role("button", name=td.CANCEL_BUTTON_LABEL)

        # -----------------------------------------------------------
        # Validation errors
        # -----------------------------------------------------------
        self.row_name_required_error = page.get_by_text(
            re.compile(re.escape(td.ROW_NAME_REQUIRED), re.IGNORECASE)
        ).first
        self.name_too_long_error = page.get_by_text(td.ROW_NAME_TOO_LONG).first
        self.details_too_long_error = page.get_by_text(
            re.compile(re.escape(td.DETAILS_TOO_LONG), re.IGNORECASE)
        ).first
        self.parent_network_error = page.get_by_text(
            td.PARENT_NETWORK_ERROR_PATTERN
        ).first

        # -----------------------------------------------------------
        # Notifications
        # -----------------------------------------------------------
        self.success_toast = page.get_by_text(td.ROW_ADDED_SUCCESS_PATTERN).first
        self.unauthenticated_error_toast = page.get_by_text(
            td.UNAUTHENTICATED_MESSAGE, exact=True
        )
        self.server_unreachable_error_toast = page.get_by_text(
            td.SERVER_UNREACHABLE_MESSAGE, exact=True
        )
        self.error_toast = page.get_by_role("alert")

        # Map attribution
        self.map_attribution = page.get_by_text(
            re.compile(r"Leaflet\s*\|\s*©\s*OpenStreetMap", re.IGNORECASE)
        )

        self.permission_error = page.get_by_text(
            td.PERMISSION_ERROR_PATTERN
        ).first

    # =================================================================
    # Open / close
    # =================================================================
    def verify_modal_open(self):
        expect(self.modal_heading).to_be_visible(timeout=15000)

    def verify_modal_closed(self):
        expect(self.modal_heading).to_be_hidden(timeout=10000)

    def close_via_x(self):
        expect(self.close_button).to_be_visible()
        self.close_button.click()

    def cancel(self):
        expect(self.cancel_button).to_be_visible()
        self.cancel_button.click()

    def click_outside_to_dismiss(self):
        """Click the dimmed backdrop outside the modal to dismiss it."""
        self.page.mouse.click(10, 10)

    # =================================================================
    # Form actions
    # =================================================================
    def fill_row_name(self, name: str):
        expect(self.row_name_input).to_be_visible()
        self.row_name_input.fill(name)

    def clear_row_name(self):
        expect(self.row_name_input).to_be_visible()
        self.row_name_input.fill("")

    def fill_details(self, text: str):
        expect(self.details_input).to_be_visible()
        self.details_input.fill(text)

    def fill_remarks(self, text: str):
        expect(self.remarks_input).to_be_visible()
        self.remarks_input.fill(text)

    def set_active(self, checked: bool = True):
        expect(self.active_checkbox).to_be_visible()
        if checked:
            self.active_checkbox.check()
        else:
            self.active_checkbox.uncheck()

    def submit(self):
        expect(self.submit_button).to_be_visible()
        self.submit_button.click()

    def press_enter_on_name(self):
        self.row_name_input.press("Enter")

    def draw_coverage_polygon(self, points: list[tuple[float, float]] | None = None):
        """
        Click the given relative positions on the modal map to draw a polygon.

        The modal auto-closes the polygon after 3 vertices (see UI hint).
        Tests that need a valid polygon may call this; pure coverage / UI
        cases leave the map empty.
        """
        points = points or td.POLYGON_POINTS
        expect(self.map_container).to_be_visible()
        self.page.wait_for_timeout(300)

        box = self.map_container.bounding_box()
        assert box, "Coverage map is not visible"
        for rel_x, rel_y in points:
            self.page.mouse.click(
                box["x"] + box["width"] * rel_x,
                box["y"] + box["height"] * rel_y,
            )
            self.page.wait_for_timeout(250)
        # Allow Leaflet to finish the polygon after the last vertex.
        self.page.wait_for_timeout(400)

    # =================================================================
    # Assertions
    # =================================================================
    def verify_network_banner(self, network_name: str, network_id: str | None = None):
        """Banner must read 'Creating row under network: {name} ({id})'."""
        expect(self.network_banner).to_be_visible()
        expect(self.network_banner).to_contain_text(network_name)
        if network_id:
            expect(self.network_banner).to_contain_text(network_id)

    def verify_default_form_state(self):
        """Row Name empty, Details empty, Remarks empty, Active checked, no validation error."""
        expect(self.row_name_input).to_have_value("")
        expect(self.details_input).to_have_value("")
        expect(self.remarks_input).to_have_value("")
        expect(self.active_checkbox).to_be_checked()
        expect(self.row_name_required_error).to_have_count(0)

    def verify_row_name_value(self, expected: str):
        expect(self.row_name_input).to_have_value(expected)

    def verify_details_value(self, expected: str):
        expect(self.details_input).to_have_value(expected)

    def verify_remarks_value(self, expected: str):
        expect(self.remarks_input).to_have_value(expected)

    def verify_submit_disabled(self):
        expect(self.submit_button).to_be_disabled()

    def verify_submit_enabled(self):
        expect(self.submit_button).to_be_enabled()

    def verify_form_elements_visible(self):
        """Every element listed in TC_001 / TC_002."""
        expect(self.modal_heading).to_be_visible()
        expect(self.close_button).to_be_visible()
        expect(self.network_banner).to_be_visible()
        expect(self.row_name_label).to_be_visible()
        expect(self.row_name_input).to_be_visible()
        expect(self.details_label).to_be_visible()
        expect(self.details_input).to_be_visible()
        expect(self.remarks_label).to_be_visible()
        expect(self.remarks_input).to_be_visible()
        expect(self.coverage_area_label).to_be_visible()
        expect(self.map_container).to_be_visible()
        expect(self.active_checkbox).to_be_visible()
        expect(self.cancel_button).to_be_visible()
        expect(self.submit_button).to_be_visible()

    def verify_row_name_has_focus(self):
        try:
            expect(self.row_name_input).to_be_focused(timeout=3000)
        except AssertionError:
            is_active = self.row_name_input.evaluate(
                "el => el === document.activeElement"
            )
            assert is_active, "Row Name field does not have focus"

    def verify_placeholder_visible(self):
        expect(self.row_name_input).to_have_attribute(
            "placeholder", td.ROW_NAME_PLACEHOLDER
        )

    def verify_active_checked(self):
        expect(self.active_checkbox).to_be_checked()

    def verify_active_unchecked(self):
        expect(self.active_checkbox).not_to_be_checked()

    def verify_fullscreen_button_visible(self):
        expect(self.fullscreen_button).to_be_visible()
        expect(self.fullscreen_button).to_be_enabled()

    def verify_fullscreen_exit_button_visible(self):
        """Verify the fullscreen exit control is visible and enabled."""
        expect(self.exit_fullscreen_button).to_be_visible()
        expect(self.exit_fullscreen_button).to_be_enabled()

    def get_map_area(self):
        """Return the current Coverage Area map's total display area."""
        expect(self.map_container).to_be_visible()

        box = self.map_container.bounding_box()
        assert box is not None, "Coverage Area map dimensions could not be retrieved."

        return box["width"] * box["height"]

    def verify_map_enlarged(self, original_area: float):
        """Verify the map is larger after entering fullscreen mode."""
        fullscreen_area = self.get_map_area()

        assert fullscreen_area > original_area, (
            f"Coverage Area map did not enlarge. "
            f"Original area: {original_area}, "
            f"Fullscreen area: {fullscreen_area}"
        )

    def get_interactive_path_count(self):
        """Return the number of visible, valid Leaflet paths."""
        paths = self.map_container.locator(
            'path.leaflet-interactive:visible:not([d="M0 0"])'
        )
        return paths.count()

    def verify_polygon_created(self, initial_path_count: int):
        """Verify a new visible polygon path was created."""
        paths = self.map_container.locator(
            'path.leaflet-interactive:visible:not([d="M0 0"])'
        )

        current_count = paths.count()

        assert current_count > initial_path_count, (
            f"Polygon was not created on the fullscreen map. "
            f"Initial visible paths: {initial_path_count}, "
            f"Current visible paths: {current_count}"
        )

        return current_count

    def verify_polygon_persisted(self, expected_path_count: int):
        """Verify the polygon remains visible after exiting fullscreen."""

        paths = self.map_container.locator(
            'path.leaflet-interactive:visible:not([d="M0 0"])'
        )

        current_count = paths.count()

        assert current_count >= expected_path_count, (
            f"Polygon was not retained after exiting fullscreen. "
            f"Expected at least {expected_path_count} visible paths, "
            f"but found {current_count}."
        )

        expect(paths.first).to_be_visible()

    def zoom_out_map_until_polygon_visible(self, max_clicks: int = 15):
        """
        Keep zooming out until the complete coverage polygon
        is visible within the map viewport.
        """

        expect(self.map_container).to_be_visible()
        expect(self.leaflet_zoom_out_button).to_be_visible()

        for click_count in range(max_clicks + 1):

            polygon_visibility = self.map_container.evaluate("""
                container => {
                    const mapRect = container.getBoundingClientRect();

                    const polygons = Array.from(
                        container.querySelectorAll(
                            'path.leaflet-interactive'
                        )
                    ).filter(path => {
                        const d = (path.getAttribute('d') || '').trim();

                        return (
                            d &&
                            !/^M\\s*0\\s*0\\s*$/.test(d) &&
                            /z\\s*$/i.test(d) &&
                            path.getAttribute('fill') !== 'none'
                        );
                    });

                    if (!polygons.length) {
                        return {
                            found: false,
                            fullyVisible: false
                        };
                    }

                    // Check the most recently drawn polygon
                    const polygon = polygons[polygons.length - 1];
                    const rect = polygon.getBoundingClientRect();

                    const tolerance = 2;

                    const fullyVisible = (
                        rect.width > 0 &&
                        rect.height > 0 &&
                        rect.left >= mapRect.left - tolerance &&
                        rect.top >= mapRect.top - tolerance &&
                        rect.right <= mapRect.right + tolerance &&
                        rect.bottom <= mapRect.bottom + tolerance
                    );

                    return {
                        found: true,
                        fullyVisible: fullyVisible
                    };
                }
            """)

            assert polygon_visibility["found"], (
                "No valid coverage polygon was found on the map."
            )

            if polygon_visibility["fullyVisible"]:
                return

            if click_count == max_clicks:
                break

            # Zoom out one level and check again
            self.leaflet_zoom_out_button.click()
            self.page.wait_for_timeout(300)

        assert polygon_visibility["fullyVisible"], (
            f"Complete coverage polygon is still not visible "
            f"after {max_clicks} zoom-out clicks."
        )

    def verify_map_restored(self, fullscreen_area: float):
        """Verify the map returns to a smaller modal view after fullscreen."""
        restored_area = self.get_map_area()

        assert restored_area < fullscreen_area, (
            f"Coverage Area map did not return to modal size. "
            f"Fullscreen area: {fullscreen_area}, "
            f"Restored area: {restored_area}"
        )
