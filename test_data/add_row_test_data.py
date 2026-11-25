"""
Test data for Catalog - Add Row modal.

NOTE: Region / network / row IDs are system-generated and change on every
creation, so NO ID is hard-coded here. Tests resolve IDs at runtime from
the hierarchy row text.
"""
import re

# ---------------------------------------------------------------------------
# Locators / labels
# ---------------------------------------------------------------------------
MODAL_TITLE = "Catalog - Add Row"
ROW_NAME_PLACEHOLDER = "e.g., Row A1"
ROW_NAME_LABEL = "Row Name"
DETAILS_LABEL = "Details"
REMARKS_LABEL = "Remarks"
COVERAGE_AREA_LABEL = "Coverage area"
ACTIVE_CHECKBOX_LABEL = "Active"
SUBMIT_BUTTON_LABEL = "Add Row"
CANCEL_BUTTON_LABEL = "Cancel"
NETWORK_BANNER_PREFIX = "Creating row under network: "

# ---------------------------------------------------------------------------
# Regions / networks (names only - IDs resolved at runtime)
# ---------------------------------------------------------------------------
REGION_NAME = "Region-Add_Row_Test"
NETWORK_NAME = "Network-Add_Row_Test"
NETWORK_OTHER_NAME = "Network-Add_Row_Other_Test"
NETWORK_FIRST_ROW_NAME = "Network-Add_Row_First_Row_Test"
NETWORK_DELETE_NAME = "Network-Add_Row_Delete_Test"
NETWORK_ZERO_ROW_NAME = "Zero Row Test"

# ---------------------------------------------------------------------------
# Coverage polygon used by most creation cases (see "Polygon" in Test Data):
# 3 vertices at approx. 40%/40%, 60%/40% and 50%/60% (x/y) of the map box.
# ---------------------------------------------------------------------------
POLYGON_POINTS = [(0.40, 0.40), (0.60, 0.40), (0.50, 0.60)]

# Parent network polygon (covers most of the map so row polygons fit inside)
NETWORK_POLYGON_POINTS = [(0.10, 0.10), (0.90, 0.10), (0.90, 0.90), (0.10, 0.90)]

# Outside-boundary points (for TC_031)
OUTSIDE_POLYGON_POINTS = [(0.93, 0.35), (0.97, 0.55), (0.92, 0.70)]

# Self-intersecting points (for TC_032)
SELF_INTERSECT_POINTS = [(0.40, 0.40), (0.60, 0.60), (0.60, 0.40), (0.40, 0.60)]

# ---------------------------------------------------------------------------
# Validation / feedback messages
# ---------------------------------------------------------------------------
ROW_NAME_REQUIRED = "Row Name is required"
ROW_NAME_TOO_LONG = "The label field must not be greater than 255 characters."
DETAILS_TOO_LONG = "must not be greater than"
PARENT_NETWORK_INVALID_MESSAGE = "The selected network is invalid."
UNAUTHENTICATED_MESSAGE = "Unauthenticated."
SERVER_UNREACHABLE_MESSAGE = (
    "Unable to reach the server. Check your connection and try again."
)
# Restricted user without row.create (TC_061)
PERMISSION_ERROR_MESSAGE = "Missing required permission [row.create]."
PERMISSION_ERROR_PATTERN = re.compile(
    r"Missing required permission\s*\[?\s*row\.create\s*\]?",
    re.IGNORECASE,
)

ROW_ADDED_SUCCESS_PATTERN = re.compile(
    r"(added|created).*success|success.*(added|created)|row.*(added|created)",
    re.IGNORECASE,
)
PARENT_NETWORK_ERROR_PATTERN = re.compile(
    r"(network.*(invalid|no longer exists|not found)|selected network is invalid)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Field-length boundaries
# ---------------------------------------------------------------------------
MAX_ROW_NAME_LENGTH = 255
LENGTH_255_FILLER = "M"                                          # TC_011
OVER_MAX_LENGTH_ROW_NAME = "R" * (MAX_ROW_NAME_LENGTH + 1)       # TC_012 (256)
OVER_MAX_DETAILS = "D" * 5001                                    # TC_019
OVER_MAX_REMARKS = "R" * 501                                     # TC_024

# ---------------------------------------------------------------------------
# Scenario-specific row names (exactly as in the test case sheet).
# Tests that CREATE a row wrap these in unique(...) so re-runs never collide.
# ---------------------------------------------------------------------------
NAME_BANNER_CHECK = "Banner Check Row"                           # 003
NAME_CLOSE = "Add_Row_Close_Test"                                # 004
NAME_CANCEL = "Temp Row"                                         # 006
NAME_DUPLICATE = "Add_Row_Test_Duplicate"                        # 009
NAME_REUSE = "Row Reuse Test"                                    # 010
NAME_SINGLE_CHAR = "A"                                           # 014
NAME_TRIMMED = "Add_Row_Trimmed_Test"                            # 016
LEADING_TRAILING_SPACES = " "                                    # 016
NAME_DETAILS_VALID = "Valid Details Test"                        # 017
NAME_EMPTY_DETAILS = "Row Detail Empty Test"                     # 018
NAME_LARGE_DETAILS = "Large Details Test"                        # 019
NAME_HTML_INJECTION = "Html Script Injection Test in Row Detail" # 020
NAME_REMARKS_VALID = "Valid Remarks Test"                        # 021
NAME_EMPTY_REMARKS = "Empty Remarks Test"                        # 022
NAME_SCRIPT_REMARKS = "Script Injection Test"                    # 023
NAME_MAX_REMARKS = "Max character test for remarks"              # 024
NAME_FIFTY_VERTICES = "Fifty Vertices Test"                      # 036
NAME_ACTIVE_UNCHECKED = "Active Unchecked Test"                  # 038
NAME_ACTIVE_CHECKED = "Active Checked Test"                      # 039
NAME_ISOLATED = "Isolated Row Test"                              # 042
NAME_E2E = "Add_Row_Test_Left"                                   # 043
NAME_NO_REFRESH = "Row Without Refresh Test"                     # 048
NAME_OFFLINE = "Temp Row Offline Test"                           # 049
NAME_DOUBLE_SUBMIT = "Rapid Double Submission"                   # 050
NAME_PARENT_REF = "Parent Reference Test"                        # 051
NAME_PARENT_DELETED = "Parent Deleted Test"                      # 052
NAME_SESSION_CLEARED = "Cookies and Session Cleared"             # 053
NAME_RESIDUAL = "Residual Data Test"                             # 058
NAME_SQL_ROW = "' OR '1'='1"                                     # 059
NAME_SQL_REMARKS = "SQL Remarks Test"                            # 060
NAME_UNAUTHORIZED = "Unauthorized Row Test"                      # 061

# XSS / injection payloads
SCRIPT_PAYLOAD = "<script>alert(1)</script>"                     # 013
IMG_ONERROR_PAYLOAD = "<img src=x onerror=alert(1)>"             # 020
SCRIPT_XSS_PAYLOAD = "<script>alert('XSS')</script>"             # 023
SQL_PAYLOAD = "' OR '1'='1"                                      # 059 / 060

# Details / remarks content
DETAILS_VALID = "This is test row details"                       # 017
DETAILS_CANCEL = "This is test row detail"                       # 006
REMARKS_VALID = "Pending fiber splice confirmation"              # 021
REMARKS_CANCEL = "Temp remark"                                   # 006
REMARKS_E2E = "Test Remarks"                                     # 043
DETAILS_E2E = "Test Row Details (Left)"                          # 043

# Map attribution
MAP_ATTRIBUTION = "Leaflet | © OpenStreetMap contributors"

# Isolated points panel
ISOLATED_POINTS_LABEL = "Selected network - not in Row Points or end_point"
SHOW_ISOLATED_CHECKBOX = "Show isolated points"
NO_ROW_TEXT = "No row"
