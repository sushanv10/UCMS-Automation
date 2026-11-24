"""
Test data for Catalog - Add Row
(TC_ADDROW_001 .. 060).

Values are copied from the test-case sheet. Row names that are created
by a test are wrapped with utils.helpers.unique() inside the tests so
re-runs never collide under the shared network.
"""
import re

# ---------------------------------------------------------------------------
# Region / network (created only if missing)
# ---------------------------------------------------------------------------
REGION_NAME = "Region-Add_Row_Test"
NETWORK_NAME = "Network-Add_Row_Test"
NETWORK_OTHER = "Network-Add_Row_Other_Test"
NETWORK_DELETE = "Network-Add_Row_Delete_Test"
NETWORK_ZERO_ROWS = "Zero Row Test"

# ---------------------------------------------------------------------------
# Parent-network coverage polygon (Add Network precondition – 4 vertices)
# clicks at (10%, 10%), (90%, 10%), (90%, 90%), (10%, 90%) of the map
# ---------------------------------------------------------------------------
NETWORK_POLYGON_POINTS = [(0.10, 0.10), (0.90, 0.10), (0.90, 0.90), (0.10, 0.90)]

# ---------------------------------------------------------------------------
# Row coverage polygon (Add Row – 3 vertices; auto-closes after 3 points)
# clicks at (40%, 40%), (60%, 40%), (50%, 60%) of the map
# ---------------------------------------------------------------------------
ROW_POLYGON_POINTS = [(0.40, 0.40), (0.60, 0.40), (0.50, 0.60)]
ROW_POLYGON_VERTEX_COUNT = 3

# ---------------------------------------------------------------------------
# UI copy
# ---------------------------------------------------------------------------
MODAL_TITLE = "Catalog - Add Row"
ROW_NAME_PLACEHOLDER = "e.g., Row A1"
ROW_NAME_LABEL = "Row Name"
DETAILS_LABEL = "Details"
REMARKS_LABEL = "Remarks"
ACTIVE_CHECKBOX_LABEL = "Active"
COVERAGE_AREA_LABEL = "Coverage area"
SUBMIT_BUTTON_LABEL = "Add Row"
CANCEL_BUTTON_LABEL = "Cancel"
LOADING_BUTTON_TEXT = "Please wait"
BANNER_PREFIX = "Creating row under network:"

# ---------------------------------------------------------------------------
# Validation / feedback
# ---------------------------------------------------------------------------
ROW_NAME_REQUIRED = "Row Name is required"
ROW_NAME_TOO_LONG = "The label field must not be greater than 255 characters."
DETAILS_TOO_LONG_PATTERN = re.compile(r"must not be greater than", re.IGNORECASE)
PARENT_NETWORK_INVALID = re.compile(
    r"(selected network is invalid|network.*(invalid|no longer exists|not found))",
    re.IGNORECASE,
)
UNAUTHENTICATED_MESSAGE = "Unauthenticated."
SERVER_UNREACHABLE_MESSAGE = (
    "Unable to reach the server. Check your connection and try again."
)
ROW_ADDED_SUCCESS_PATTERN = re.compile(
    r"(added|created).*success|success.*(added|created)|row.*(added|created)",
    re.IGNORECASE,
)
NO_ROW_MESSAGE = re.compile(r"no\s+row", re.IGNORECASE)

# ---------------------------------------------------------------------------
# API route for create-row interception
# ---------------------------------------------------------------------------
CREATE_ROW_API_ROUTE_PATTERN = r".*/api/map/(rows|row)s?/?$"

# ---------------------------------------------------------------------------
# Field limits
# ---------------------------------------------------------------------------
MAX_ROW_NAME_LENGTH = 255
OVER_MAX_ROW_NAME = "M" * (MAX_ROW_NAME_LENGTH + 1)
MAX_LENGTH_FILLER = "M"

# ---------------------------------------------------------------------------
# Scenario row names (sheet values; tests wrap with unique() when creating)
# ---------------------------------------------------------------------------
NAME_BANNER_CHECK = "Banner Check Row"                   # 003
NAME_CLOSE = "Add_Row_Close_Test"                        # 004
NAME_CANCEL = "Temp Row"                                 # 006
DETAILS_CANCEL = "This is test row detail"
REMARKS_CANCEL = "Temp remark"
NAME_DUPLICATE = "Add_Row_Test_Duplicate"                 # 009
NAME_REUSE = "Row Reuse Test"                            # 010
NAME_NUMERIC = "20260"                                   # numeric
NAME_ALPHANUMERIC = "Row A1 Segment"                     # alphanumeric
NAME_SPECIAL = "Row-Zone_1 (North) & South"              # special chars
NAME_UNICODE = "बागमती पंक्ति"                            # unicode
NAME_TRIM = "Add_Row_Trim_Test"                          # trim
NAME_DETAILS_VALID = "Add_Row_Details_Valid"
DETAILS_VALID = "Primary fiber segment"
NAME_EMPTY_DETAILS = "Add_Row_Empty_Details"
NAME_MULTILINE = "Add_Row_Multiline"
DETAILS_MULTILINE = "Line one\nLine two"
NAME_REMARKS = "Add_Row_Remarks_Test"
REMARKS_VALID = "Installer note"
NAME_ACTIVE_CHECKED = "Add_Row_Active_Checked"
NAME_ACTIVE_UNCHECKED = "Add_Row_Active_Unchecked"
NAME_END_TO_END = "Add_Row_End_To_End"
DETAILS_E2E = "End to end row"
REMARKS_E2E = "E2E remark"
NAME_DOUBLE_CLICK = "Rapid Double Submission"            # 050
NAME_PARENT_REF = "Parent Reference Test"                # 051
NAME_PARENT_DELETED = "Parent Deleted Test"              # 052
NAME_SESSION = "Cookies and Session Cleared"             # 053
NAME_LOADING = "Button Disabled Test"                    # 057
NAME_RESIDUAL = "Residual Data Test"                     # 058
DETAILS_RESIDUAL = "Residual details"
REMARKS_RESIDUAL = "Residual remarks"
NAME_SQL = "' OR '1'='1"                                 # 059
NAME_SQL_REMARKS = "SQL Remarks Test"                    # 060
REMARKS_SQL = "' OR '1'='1"
NAME_WHITESPACE = "   "                                  # 008
NAME_VALIDATION_CLEAR = "Add_Row_Validation_Clear"

# Offline / server failure
NAME_OFFLINE = "Add_Row_Offline_Test"
NAME_SERVER_FAIL = "Add_Row_Server_Failure_Test"
