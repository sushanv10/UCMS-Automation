"""
Test data for Catalog - Add Network modal.

Mirrors the 'Test Data' column of the Add Network manual test case sheet
(TC_NETWORK_EXPLORER_CATALOG_ADD_NETWORK_001 .. 054).

NOTE: Region / network IDs are system-generated and change on every creation,
so NO ID is hard-coded here. Tests resolve the Region ID at runtime from the
hierarchy row text "<ID> - <Region Name>".
"""
import re

# ---------------------------------------------------------------------------
# Locators / labels
# ---------------------------------------------------------------------------
MODAL_TITLE = "Catalog - Add Network"
NETWORK_NAME_PLACEHOLDER = "e.g., Lalitpur"
NETWORK_NAME_LABEL = "Network Name"
DETAILS_LABEL = "Details"
COVERAGE_AREA_LABEL = "Coverage area"
ACTIVE_CHECKBOX_LABEL = "Active"
SUBMIT_BUTTON_LABEL = "Add Network"
CANCEL_BUTTON_LABEL = "Cancel"
REGION_BANNER_PREFIX = "Creating network under region: "

# ---------------------------------------------------------------------------
# Regions (names only - IDs are resolved at runtime)
# ---------------------------------------------------------------------------
REGION_NAME = "Region-Add_Network_Test"                        # most cases
REGION_HIERARCHY = "Region-Add_Network_Hierarchy_Test"         # 052
REGION_EMPTY = "Region-Add_Network_Empty_Test"                 # 053
REGION_DELETED = "Region-Add_Network_Deleted_Region_Test"      # 050
REGION_DUPLICATE_ID = "Region-Add_Network_Duplicate_ID_Test"   # 054

# ---------------------------------------------------------------------------
# Coverage polygon used by every creation case (see "Polygon" in Test Data):
# 3 vertices at approx. 25%/25%, 75%/25% and 50%/75% (x/y) of the map box.
# ---------------------------------------------------------------------------
POLYGON_POINTS = [(0.25, 0.25), (0.75, 0.25), (0.50, 0.75)]

# ---------------------------------------------------------------------------
# Validation / feedback messages
# ---------------------------------------------------------------------------
NETWORK_NAME_REQUIRED = "Network Name is required"
NETWORK_NAME_TOO_LONG = "The label field must not be greater than 255 characters."
DETAILS_TOO_LONG = "must not be greater than"
DUPLICATE_NAME_ERROR = "already exists"
PARENT_REGION_INVALID_MESSAGE = "The selected region is invalid."
RAW_SQL_ERROR_FRAGMENT = "SQLSTATE"

NETWORK_ADDED_SUCCESS_PATTERN = re.compile(
    r"(added|created).*success|success.*(added|created)|network.*(added|created)",
    re.IGNORECASE,
)
NETWORK_ERROR_PATTERN = "Unauthenticated."
SESSION_ERROR_PATTERN = (
    "Unable to reach the server. Check your connection and try again."
)
PARENT_REGION_ERROR_PATTERN = re.compile(
    r"(region.*(invalid|no longer exists|not found)|selected region is invalid)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Field-length boundaries
# ---------------------------------------------------------------------------
MAX_NETWORK_NAME_LENGTH = 255
# Fillers for boundary names: the tests append unique("...") and keep the
# total length EXACT (254 / 255).
LENGTH_254_FILLER = "Q"                                          # 020
MAX_LENGTH_FILLER = "B"                                          # 021
OVER_MAX_LENGTH_NETWORK_NAME = "K" * (MAX_NETWORK_NAME_LENGTH + 1)  # 044 (256)
OVER_MAX_DETAILS = "D" * 5000                                    # 045

# ---------------------------------------------------------------------------
# Scenario-specific network names (exactly as in the test case sheet).
# Tests that CREATE a network wrap these in unique(...) so re-runs never collide;
# fixed names are kept only where the exact value is the scenario (N, 20260).
# ---------------------------------------------------------------------------
NAME_CLOSE_ICON = "Add_Network_Close_Icon_Test"                  # 007
NAME_BACKDROP = "Add_Network_Backdrop_Test"                      # 008
NAME_ESCAPE = "Add_Network_Escape_Test"                          # 009
NAME_CANCEL = "Add_Network_Cancel_Test"                          # 010
NAME_REOPEN_DISCARDED = "Add_Network_Reopen_Discarded_Test"      # 011
NAME_ENTER_KEY = "Add_Network_Enter_Key_Test"                    # 013
NAME_SINGLE_CHAR = "N"                                           # 019
NAME_NUMERIC = "20260"                                           # 022
NAME_ALPHANUMERIC = "Metro Network 101"                          # 023
NAME_SPECIAL_CHARS = "Lalitpur-Metro (Zone_1) & Hills"           # 024
NAME_UNICODE_NEPALI = "ललितपुर नेटवर्क"                            # 025
NAME_TRIMMED = "Add_Network_Trim_Test"                           # 026
LEADING_TRAILING_SPACES = " "                                    # 026 (1 space each side)
NAME_DETAILS_VALID = "Add_Network_Details_Valid_Test"            # 027
NAME_EMPTY_DETAILS = "Add_Network_Empty_Details_Test"            # 028
NAME_MULTILINE_DETAILS = "Add_Network_Multiline_Details_Test"    # 029
NAME_SPECIAL_DETAILS = "Add_Network_Special_Details_Test"        # 030
NAME_WHITESPACE_DETAILS = "Add_Network_Whitespace_Details_Test"  # 031
NAME_ACTIVE_CHECKED = "Add_Network_Active_Checked_Test"          # 032
NAME_ACTIVE_UNCHECKED = "Add_Network_Active_Unchecked_Test"      # 033
NAME_INACTIVE_STATUS = "Add_Network_Inactive_Status_Test"        # 034
NAME_END_TO_END = "Add_Network_End_To_End_Test"                  # 035
NAME_PAYLOAD_CHECK = "Add_Network_Payload_Check_Test"            # 036
NAME_DOUBLE_CLICK = "Add_Network_Double_Click_Test"              # 037
NAME_LOADING_STATE = "Add_Network_Loading_State_Test"            # 038
NAME_VALIDATION_CLEAR = "Add_Network_Validation_Clear_Test"      # 043
NAME_LONG_DETAILS = "Add_Network_Long_Details_Test"              # 045
NAME_DUPLICATE_TEST = "Add_Network_Duplicate_Test"               # 046
NAME_XSS_DETAILS = "Add_Network_XSS_Details_Test"                # 048
NAME_SERVER_FAILURE = "Add_Network_Server_Failure_Test"          # 049
NAME_DELETED_REGION = "Add_Network_Deleted_Region_Test"          # 050
NAME_SESSION_CLEARED = "Add_Network_Session_Cleared_Test"        # 051
NAME_HIERARCHY = "Add_Network_Hierarchy_Test"                    # 052
NAME_DUPLICATE_ID = "Add_Network_Duplicate_ID_Test"              # 054

# ---------------------------------------------------------------------------
# Details values
# ---------------------------------------------------------------------------
DETAILS_CANCEL = "Details entered before cancel"                 # 010
DETAILS_DISCARDED = "Discarded details"                          # 011
DETAILS_VALID = "Primary fiber route covering Naya Baneshwor"    # 027
DETAILS_MULTILINE = "Line one\nLine two"                         # 029
DETAILS_SPECIAL_UNICODE = "Zone #1 / Phase-2 (100% fiber) - काठमाडौं"  # 030
DETAILS_WHITESPACE_ONLY = "   "                                  # 031 (3 spaces)
DETAILS_PRIMARY = "Primary fiber route"                          # 035
DETAILS_WHITESPACE_NAME_CASE = "Details for whitespace-only name test"  # 040
DETAILS_SERVER_FAILURE = "Details retained after server failure"  # 049
DETAILS_SESSION_CLEARED = "Valid details after session clear"    # 051

# ---------------------------------------------------------------------------
# Name edge cases / payloads
# ---------------------------------------------------------------------------
WHITESPACE_ONLY_NETWORK_NAME = "   "                            # 040 (3 spaces)
SCRIPT_INJECTION_PAYLOAD = "<script>alert(1)</script>"           # 047
SQL_INJECTION_PAYLOAD = "' OR '1'='1"                            # 047
HTML_INJECTION_DETAILS = "<img src=x onerror=alert(1)>"          # 048

# ---------------------------------------------------------------------------
# API route pattern for create-network interception
# ---------------------------------------------------------------------------
CREATE_NETWORK_API_ROUTE_PATTERN = r".*/api/map/networks$"