"""
Test data for Catalog - Row Details
(TC_ROWDETAILS_001 .. 041).

Primary region / network / row use fixed sheet names and are created only
if missing. Scenario-specific rows use the fixed sheet names too (ensure-only).
"""
import math
import re

# ---------------------------------------------------------------------------
# Primary hierarchy (ensure-only)
# ---------------------------------------------------------------------------
REGION_NAME = "Region-Row_Details_Test"
NETWORK_NAME = "Network-Row_Details_Test"
PRIMARY_ROW_NAME = "Row_Details_Test"

# Scenario networks / rows (sheet names)
NETWORK_NO_ROW = "Network-Row_Details_No_Row_Test"
NETWORK_INACTIVE_PARENT = "Network-Row_Details_Inactive_Parent_Test"
NETWORK_DELETE = "Network-Row_Details_Delete_Test"
NETWORK_LONG_REGION = "Network-Row_Details_Long_Region_Test"

ROW_ACTIVE = "Row_Details_Active_Test"
ROW_INACTIVE = "Row_Details_Inactive_Test"
ROW_PATH_1 = "Row_Details_Path_Test 1"
ROW_PATH_2 = "Row_Details_Path_Test 2"
ROW_POLYGON = "Row_Details_Polygon_Test"
ROW_NO_POLYGON = "Row_Details_No_Polygon_Test"
ROW_PRECISION = "Row_Details_Precision_Test"
ROW_ONLY = "Row_Details_Only_Row_Test"
ROW_INACTIVE_PARENT = "Row_Details_Inactive_Parent_Test"
ROW_FIFTY = "Row_Details_Fifty_Vertices_Test"
ROW_POLYGON_EDIT = "Row_Details_Polygon_Edit_Test"
ROW_TEXT = "Row_Details_Text_Test"
ROW_LONG_REGION = "Row_Details_Long_Region_Test"
ROW_DELETE_PARENT = "Row_Details_Delete_Parent_Test"
ROW_DELETE_ROW = "Row_Details_Delete_Row_Test"
ROW_SQL = "' OR '1'='1"
ROW_SCRIPT = "<script>alert(1)</script>"
ROW_UNICODE = "बागमती पंक्ति"
ROW_LONG = "Row_Details_Long_Name_Test"
ROW_SPECIAL = 'Row & <Details> "Test"'
LONG_ROW_NAME = "M" * 255          # exactly 255 characters
LONG_ROW_NAME_LENGTH = 255

# TC_021 - typed with 1 leading + 1 trailing space, saved trimmed
ROW_TRIMMED = "Row_Details_Trimmed_Test"
ROW_TRIMMED_TYPED = " Row_Details_Trimmed_Test "

# TC_023 - 255-character region name
LONG_REGION_NAME = "R" * 255
LONG_REGION_NAME_LENGTH = 255

# TC_030 - Details / Remarks text
ROW_TEXT_DETAILS = "Primary fiber row"
ROW_TEXT_REMARKS = "Newly commissioned"

# ---------------------------------------------------------------------------
# UI copy
# ---------------------------------------------------------------------------
MODAL_TITLE = "Row Details"
EDIT_MODAL_TITLE = "Catalog - Edit Row"
PATH_LABEL = "Path"
ID_LABEL = "ID"
LABEL_LABEL = "Label"
NETWORK_LABEL = "Network"
STATUS_LABEL = "Status"
COVERAGE_AREA_LABEL = "Coverage area"
EDIT_BUTTON = "Edit"
CLOSE_BUTTON = "Close"
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"
NO_POLYGON_MESSAGE = "No coverage polygon defined."
POLYGON_INFO_PATTERN = r"Polygon defined with\s+\d+\s+vertices?"
NO_ROW_MESSAGE = re.compile(r"no\s+row", re.IGNORECASE)

ACTIVE_COVERAGE_TITLE = "Active coverage"
ACTIVE_COVERAGE_ONE_ROW = "1 row"

ATTRIBUTION_PATTERN = r"Leaflet\s*\|\s*©\s*OpenStreetMap contributors"
LEAFLET_HREF = "leafletjs.com"
OSM_HREF = "openstreetmap.org/copyright"


def polygon_caption(vertices: int) -> str:
    """Caption shown under the Coverage area map, e.g. 'Polygon defined with 3 vertices.'"""
    return f"Polygon defined with {vertices} vertices."


# ---------------------------------------------------------------------------
# Polygons
# ---------------------------------------------------------------------------
# Parent network (Add Network) – 4 vertices covering most of the map
NETWORK_POLYGON_POINTS = [(0.10, 0.10), (0.90, 0.10), (0.90, 0.90), (0.10, 0.90)]

# Row 3-vertex polygon
ROW_POLYGON_POINTS = [(0.40, 0.40), (0.60, 0.40), (0.50, 0.60)]
ROW_POLYGON_VERTEX_COUNT = 3

# Precision 4-vertex rectangle
PRECISION_POLYGON_POINTS = [(0.30, 0.30), (0.70, 0.30), (0.70, 0.70), (0.30, 0.70)]
PRECISION_VERTEX_COUNT = 4

# TC_024 - vertex inserted in the middle of the top edge in Edit Row
EDIT_VERTEX_POINT = (0.50, 0.40)
EDIT_VERTEX_COUNT_AFTER = 4

# TC_015 - 50 clicks along a circle, centre (50%, 50%), radius 20% of the MAP HEIGHT,
# one click every 7.2 degrees.
# Points are fractions of map width/height, so the x radius is scaled by the
# map aspect ratio (width / height). ASSUMPTION: the Add Row map is ~1.6 : 1.
# Adjust MAP_ASPECT_RATIO if the real Add Row map has another shape.
MAP_ASPECT_RATIO = 1.6


def circle_polygon_points(
    vertices: int = 50,
    radius_of_height: float = 0.20,
    aspect_ratio: float = MAP_ASPECT_RATIO,
    centre: tuple[float, float] = (0.50, 0.50),
) -> list[tuple[float, float]]:
    step = 360.0 / vertices          # 7.2 degrees for 50 vertices
    points = []
    for i in range(vertices):
        angle = math.radians(step * i)
        x = centre[0] + (radius_of_height / aspect_ratio) * math.cos(angle)
        y = centre[1] + radius_of_height * math.sin(angle)
        points.append((round(x, 4), round(y, 4)))
    return points


FIFTY_VERTEX_COUNT = 50
FIFTY_POLYGON_POINTS = circle_polygon_points(FIFTY_VERTEX_COUNT)

SESSION_MESSAGE = re.compile(
    r"unauthenticated|unauthorized"
    r"|session.*(expired|invalid|timed out)|(expired|invalid).*session"
    r"|please (log|sign) ?in",
    re.I,
)