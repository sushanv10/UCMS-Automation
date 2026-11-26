"""
Page Object for the Catalog - Row Details modal.

Opened by clicking a row label in the Coverage tree (not the checkbox).
"""
import re

from playwright.sync_api import Locator, Page, expect

from test_data import row_details_test_data as td

# JS run in the browser: returns the rectangle the text actually occupies.
# For elements that clip their content (overflow hidden / ellipsis) the element
# box is used; otherwise the text range is used so overflow is detected.
_TEXT_RECT_JS = """
el => {
    const cs = getComputedStyle(el);
    const clipped = cs.overflowX !== 'visible';   // ellipsis / hidden = clipped by element
    const box = el.getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(el);
    const txt = range.getBoundingClientRect();
    return {
        left: clipped ? box.left : Math.min(box.left, txt.left),
        right: clipped ? box.right : Math.max(box.right, txt.right),
        top: box.top,
        bottom: clipped ? box.bottom : Math.max(box.bottom, txt.bottom),
    };
}
"""

# Font size / colour (converted to sRGB through a canvas) of an element.
_STYLE_JS = """
el => {
    const cs = getComputedStyle(el);
    const c = document.createElement('canvas');
    c.width = c.height = 1;
    const g = c.getContext('2d', { willReadFrequently: true });
    g.fillStyle = cs.color;
    g.fillRect(0, 0, 1, 1);
    const px = g.getImageData(0, 0, 1, 1).data;
    return {
        fontSize: parseFloat(cs.fontSize),
        fontWeight: cs.fontWeight,
        r: px[0], g: px[1], b: px[2],
    };
}
"""

# True when a full-page fixed/absolute overlay (the dimmed backdrop) sits on top at (5, 5).
_OVERLAY_JS = """
() => {
    const el = document.elementFromPoint(5, 5);
    if (!el || el === document.body || el === document.documentElement) return false;
    if (el.closest('.leaflet-container')) return false;
    const r = el.getBoundingClientRect();
    const pos = getComputedStyle(el).position;
    return (pos === 'fixed' || pos === 'absolute')
        && r.width >= window.innerWidth * 0.95
        && r.height >= window.innerHeight * 0.95;
}
"""

# True when the element that currently has the focus shows an outline or a box-shadow ring.
_FOCUS_RING_JS = """
() => {
    const el = document.activeElement;
    if (!el || el === document.body) return false;
    const cs = getComputedStyle(el);
    const outline = cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0;
    const shadow = cs.boxShadow && cs.boxShadow !== 'none';
    return Boolean(outline || shadow);
}
"""

_IS_FOCUSED_JS = """
el => {
    const a = document.activeElement;
    if (!a || a === document.body || a === document.documentElement) return false;
    if (el === a || el.contains(a)) return true;
    return ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(a.tagName) && a.contains(el);
}
"""


class RowDetailsModal:
    """Page Object for Row Details (read-only view)."""

    def __init__(self, page: Page):
        self.page = page
        self._page = page

        self.opened_region_id: str | None = None
        self.opened_network_id: str | None = None
        self.opened_row_id: str | None = None

        # -----------------------------------------------------------
        # Modal chrome
        # -----------------------------------------------------------
        self.modal_heading = page.get_by_role("heading", name=td.MODAL_TITLE)
        # X icon in the modal header (title="Close") – prefer last to avoid panel icon
        self.close_icon = page.get_by_title("Close").last
        # Footer "Close" text button – use exact text, last match is the modal footer
        self.close_button = page.get_by_text(td.CLOSE_BUTTON, exact=True).last
        self.edit_button = page.get_by_role("button", name=td.EDIT_BUTTON, exact=True)
        # Modal container (the dialog that holds the heading)
        self.modal_container = self.modal_heading.locator(
            "xpath=ancestor::*[@role='dialog' or contains(@class,'modal')][1]"
        )

        # -----------------------------------------------------------
        # Field labels
        # -----------------------------------------------------------
        self.path_label = page.get_by_text(re.compile(r"^Path:", re.IGNORECASE))
        self.id_label = page.get_by_text(td.ID_LABEL, exact=True)
        self.label_label = page.get_by_text(td.LABEL_LABEL, exact=True)
        self.network_label = page.get_by_text(td.NETWORK_LABEL, exact=True)
        self.status_label = page.get_by_text(td.STATUS_LABEL, exact=True)
        self.coverage_area_label = page.get_by_text(td.COVERAGE_AREA_LABEL, exact=True)

        # -----------------------------------------------------------
        # Coverage area (Leaflet map inside the modal)
        # -----------------------------------------------------------
        self.map_container = page.locator(".leaflet-container").last
        self.zoom_in_button = page.get_by_label("Zoom in")
        self.zoom_out_button = page.get_by_label("Zoom out")
        self.polygon_shapes = self.map_container.locator("path.leaflet-interactive")
        self.no_polygon_message = page.get_by_text(td.NO_POLYGON_MESSAGE, exact=True)
        self.polygon_info = page.get_by_text(re.compile(td.POLYGON_INFO_PATTERN, re.I))
        self.attribution = self.map_container.locator(".leaflet-control-attribution")

        # Edit hand-off
        self.edit_modal_heading = page.get_by_role(
            "heading", name=re.compile(re.escape(td.EDIT_MODAL_TITLE))
        )

        # -----------------------------------------------------------
        # Edit Row form (opened with the Edit button)
        # -----------------------------------------------------------
        self.edit_row_name_input = page.get_by_label(re.compile(r"^Row Name"))
        self.edit_details_input = page.get_by_label(re.compile(r"^Details"))
        self.edit_remarks_input = page.get_by_label(re.compile(r"^Remarks"))
        self.edit_active_checkbox = page.get_by_role(
            "checkbox", name="Active", exact=True
        )
        self.edit_submit_button = page.locator('button[type="submit"]').last

        # -----------------------------------------------------------
        # "Active coverage" panel (bottom-left of the Network Explorer)
        # -----------------------------------------------------------
        self.active_coverage_title = page.get_by_text(
            td.ACTIVE_COVERAGE_TITLE, exact=True
        )
        self.active_coverage_one_row = page.get_by_text(
            td.ACTIVE_COVERAGE_ONE_ROW, exact=True
        )

    # =================================================================
    # Field value locators
    # =================================================================
    def path_text(
        self,
        region_id: str,
        region_name: str,
        network_id: str,
        network_name: str,
        row_id: str,
        row_name: str,
    ) -> Locator:
        """
        Path: {RegionID} - {Region} / {NetworkID} - {Network} / {RowID} - {Row}
        """
        return self._page.get_by_text(
            f"Path: {region_id} - {region_name} / "
            f"{network_id} - {network_name} / "
            f"{row_id} - {row_name}",
            exact=True,
        )

    def id_value(self, row_id: str) -> Locator:
        return self._page.get_by_text(row_id, exact=True)

    def label_value(self, row_name: str) -> Locator:
        return self._page.get_by_text(row_name, exact=True)

    def label_value_in_modal(self, row_name: str) -> Locator:
        """Same as label_value but limited to the Row Details dialog (ignores the tree)."""
        return self.modal_container.get_by_text(row_name, exact=True)

    def network_value(self, network_id: str) -> Locator:
        return self._page.get_by_text(network_id, exact=True)

    def status_badge(self, status: str) -> Locator:
        return self._page.get_by_text(status, exact=True)

    def active_coverage_entry(
        self,
        region_id: str,
        region_name: str,
        network_id: str,
        network_name: str,
        row_id: str,
        row_name: str,
    ) -> Locator:
        """
        Active coverage card that contains
        '<Region ID> - Region / <Network ID> - Network / <Row ID> - Row'.
        The parts sit in separate elements, so match on the container's combined
        text and tolerate whitespace around '-' and '/'.
        """
        sep_dash = r"\s*-\s*"
        sep_slash = r"\s*/\s*"
        pattern = re.compile(
            f"{re.escape(region_id)}{sep_dash}{re.escape(region_name)}{sep_slash}"
            f"{re.escape(network_id)}{sep_dash}{re.escape(network_name)}{sep_slash}"
            f"{re.escape(row_id)}{sep_dash}{re.escape(row_name)}"
        )
        return (
            self.page.locator("div")
            .filter(has=self.active_coverage_title)
            .filter(has_text=pattern)
            .filter(has_not=self.modal_heading)  # never match a container that holds the Row Details modal
            .last                                 # innermost matching div = the Active coverage card
        )

    def row_checkbox(self, row_id: str, row_name: str) -> Locator:
        """Checkbox of a tree row, e.g. 'Select G290-D01-R01 - Row_Details_Test'."""
        return self.page.get_by_role(
            "checkbox", name=f"Select {row_id} - {row_name}", exact=True
        )

    # =================================================================
    # Open / close
    # =================================================================
    def verify_modal_open(self):
        expect(self.modal_heading).to_be_visible(timeout=15000)

    def verify_modal_closed(self):
        expect(self.modal_heading).to_be_hidden(timeout=10000)

    def close_via_x(self):
        expect(self.close_icon).to_be_visible()
        self.close_icon.click()

    def close_via_button(self):
        expect(self.close_button).to_be_visible()
        self.close_button.click()

    def click_edit(self):
        expect(self.edit_button).to_be_visible()
        self.edit_button.click()

    def verify_edit_modal_open(self):
        expect(self.edit_modal_heading).to_be_visible(timeout=10000)

    # =================================================================
    # Assertions
    # =================================================================
    def verify_row_details(
        self,
        region_id: str,
        region_name: str,
        network_id: str,
        network_name: str,
        row_id: str,
        row_name: str,
        status: str = td.STATUS_ACTIVE,
    ):
        self.verify_modal_open()
        expect(
            self.path_text(
                region_id, region_name, network_id, network_name, row_id, row_name
            )
        ).to_be_visible()
        expect(self.id_value(row_id)).to_be_visible()
        expect(self.label_value(row_name)).to_be_visible()
        expect(self.network_value(network_id)).to_be_visible()
        expect(self.status_badge(status)).to_be_visible()
        expect(self.coverage_area_label).to_be_visible()
        expect(self.map_container).to_be_visible()
        expect(self.edit_button).to_be_visible()
        expect(self.close_button).to_be_visible()

    def verify_no_polygon(self):
        expect(self.no_polygon_message).to_be_visible()
        expect(self.polygon_info).to_have_count(0)

    def verify_polygon_defined(self, min_vertices: int = 3):
        expect(self.polygon_shapes.first).to_be_visible(timeout=10000)
        expect(self.polygon_info).to_be_visible()
        text = self.polygon_info.inner_text()
        match = re.search(r"(\d+)", text)
        assert match, f"No vertex count in polygon caption: {text!r}"
        assert int(match.group(1)) >= min_vertices

    def verify_fields_visible(self):
        expect(self.modal_heading).to_be_visible()
        expect(self.path_label).to_be_visible()
        expect(self.id_label).to_be_visible()
        expect(self.label_label).to_be_visible()
        expect(self.network_label).to_be_visible()
        expect(self.status_label).to_be_visible()
        expect(self.coverage_area_label).to_be_visible()
        expect(self.map_container).to_be_visible()
        expect(self.edit_button).to_be_visible()
        expect(self.close_button).to_be_visible()
        expect(self.close_icon).to_be_visible()

    # =================================================================
    # Polygon / caption helpers
    # =================================================================
    def verify_caption(self, vertices: int):
        """Caption below the map reads exactly 'Polygon defined with N vertices.'"""
        caption = td.polygon_caption(vertices)
        expect(self.page.get_by_text(caption, exact=True)).to_be_visible(timeout=10000)
        expect(self.no_polygon_message).to_have_count(0)

    def polygon_box(self) -> dict:
        box = self.polygon_shapes.first.bounding_box()
        assert box, "Polygon has no bounding box"
        return box

    def polygon_path_d(self) -> str:
        return self.polygon_shapes.first.get_attribute("d") or ""

    def polygon_vertex_count(self) -> int:
        """Number of corners drawn (M / L commands of the SVG path)."""
        return len(re.findall(r"[ML]", self.polygon_path_d()))

    def verify_polygon_inside_map(self, tol: float = 4.0):
        m = self.map_container.bounding_box()
        p = self.polygon_box()
        assert m, "Map has no bounding box"
        assert p["x"] >= m["x"] - tol, "Polygon is cut off on the left of the map"
        assert p["y"] >= m["y"] - tol, "Polygon is cut off at the top of the map"
        assert p["x"] + p["width"] <= m["x"] + m["width"] + tol, (
            "Polygon is cut off on the right of the map"
        )
        assert p["y"] + p["height"] <= m["y"] + m["height"] + tol, (
            "Polygon is cut off at the bottom of the map"
        )

    def verify_no_polygon_drawn(self):
        expect(self.polygon_shapes).to_have_count(0)

    # =================================================================
    # Layout helpers (overflow checks)
    # =================================================================
    def visible_text_rect(self, locator: Locator) -> dict:
        """Rect of the text as actually rendered (includes overflow, excludes clipped text)."""
        return locator.first.evaluate(_TEXT_RECT_JS)

    def assert_inside_modal(self, locator: Locator, name: str, tol: float = 1.0):
        modal = self.modal_container.first.bounding_box()
        assert modal, "Modal has no bounding box"
        r = self.visible_text_rect(locator)
        assert r["left"] >= modal["x"] - tol, (
            f"{name} overflows modal on the left ({r['left']} < {modal['x']})"
        )
        assert r["right"] <= modal["x"] + modal["width"] + tol, (
            f"{name} overflows modal on the right "
            f"({r['right']} > {modal['x'] + modal['width']})"
        )

    def assert_modal_inside_viewport(self, tol: float = 2.0):
        modal = self.modal_container.first.bounding_box()
        vp = self.page.viewport_size
        assert modal and vp, "Modal or viewport size not available"
        assert modal["x"] >= -tol and modal["y"] >= -tol, "Modal starts outside the window"
        assert modal["x"] + modal["width"] <= vp["width"] + tol, (
            f"Modal is wider than the window ({modal['x'] + modal['width']} > {vp['width']})"
        )
        if modal["y"] + modal["height"] > vp["height"] + tol:
            # Taller than the window: acceptable only because the overlay scrolls,
            # and only if the footer buttons can be scrolled into view.
            for name, btn in (("Edit", self.edit_button), ("Close", self.close_button)):
                btn.scroll_into_view_if_needed()
                box = btn.bounding_box()
                assert box and box["y"] >= -tol and box["y"] + box["height"] <= vp["height"] + tol, (
                    f"{name} button is cut off and cannot be reached by scrolling"
                )

    def assert_inside_viewport(self, locator: Locator, name: str, tol: float = 2.0):
        box = locator.first.bounding_box()
        vp = self.page.viewport_size
        assert box and vp, f"{name} has no bounding box"
        assert box["x"] >= -tol and box["x"] + box["width"] <= vp["width"] + tol, (
            f"{name} is cut off horizontally"
        )

    def assert_no_overlap(self, items: list[tuple[str, Locator]], tol: float = 1.0):
        boxes = []
        for name, loc in items:
            box = loc.first.bounding_box()
            assert box, f"{name} has no bounding box"
            boxes.append((name, box))
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                n1, a = boxes[i]
                n2, b = boxes[j]
                ix = min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])
                iy = min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
                assert not (ix > tol and iy > tol), f"{n1} overlaps {n2}"

    def verify_overlay_dims_page(self):
        assert self.page.evaluate(_OVERLAY_JS), (
            "No full-page overlay (dimmed background) found behind the modal"
        )

    # =================================================================
    # Style helpers (label vs value)
    # =================================================================
    def text_style(self, locator: Locator) -> dict:
        s = locator.first.evaluate(_STYLE_JS)
        s["luminance"] = 0.2126 * s["r"] + 0.7152 * s["g"] + 0.0722 * s["b"]
        return s

    # =================================================================
    # Keyboard / focus helpers
    # =================================================================
    def is_focused(self, locator: Locator) -> bool:
        try:
            if locator.count() == 0:
                return False
            return bool(locator.first.evaluate(_IS_FOCUSED_JS, timeout=2000))
        except Exception:
            return False

    def focused_control(self) -> str | None:
        """'x', 'edit' or 'close' for the three modal buttons, otherwise None."""
        if self.is_focused(self.close_icon):
            return "x"
        if self.is_focused(self.edit_button):
            return "edit"
        if self.is_focused(self.close_button):
            return "close"
        return None

    def focus_ring_visible(self) -> bool:
        return bool(self.page.evaluate(_FOCUS_RING_JS))

    def focus_inside_modal(self) -> bool:
        return bool(
            self.modal_container.first.evaluate(
                "m => m.contains(document.activeElement)"
            )
        )

    # =================================================================
    # Map interaction helpers
    # =================================================================
    def click_map_fraction(self, fx: float, fy: float):
        """Click at (fx, fy) of the map width / height (fractions 0..1)."""
        box = self.map_container.bounding_box()
        assert box, "Map has no bounding box"
        self.page.mouse.click(
            box["x"] + box["width"] * fx, box["y"] + box["height"] * fy
        )