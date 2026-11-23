# ---------------------------------------------------------------------------
# Add Region module test data
#
# Region names that a test CREATES are base names: the test makes them unique
# with utils.helpers.unique() so re-running the suite never collides.
# Names a test only types (and never saves) are used as they are.
# Every value below belongs to one specific test case (TC number in comments).
# ---------------------------------------------------------------------------
import re

from utils.helpers import unique

# ---------------------------------------------------------------------------
# Confirmed UI copy (captured via Codegen)
# ---------------------------------------------------------------------------
MODAL_TITLE = "Catalog - Add Region"
REGION_NAME_PLACEHOLDER = "e.g., Hilly Region"
REQUIRED_ASTERISK = "*"                                  # TC_015
LOADING_TEXT = "Please wait…"                            # TC_024

# ---------------------------------------------------------------------------
# Expected validation / feedback messages
# ---------------------------------------------------------------------------
REGION_NAME_REQUIRED = "Region Name is required"
REGION_NAME_TOO_LONG = "The label field must not be greater than 255 characters."
REGION_NAME_DUPLICATE = "Region Already exists"          # currently unused (TC_019 allows duplicates)

# Success / error notifications (adjust to the exact app wording once confirmed)
REGION_ADDED_SUCCESS_PATTERN = re.compile(
    r"(added|created).*success|success.*(added|created)", re.IGNORECASE
)
PERMISSION_ERROR_PATTERN = re.compile(                                                 # TC_026
    r"permission|unauthori[sz]ed|forbidden|not allowed|not authori[sz]ed|403",
    re.IGNORECASE,
)
UNAUTHENTICATED_MESSAGE = "Unauthenticated."                                           # TC_021
SERVER_UNREACHABLE_MESSAGE = "Unable to reach the server. Check your connection and try again."  # TC_018

# ---------------------------------------------------------------------------
# Field-length boundaries (TC_008, TC_009)
# ---------------------------------------------------------------------------
MAX_REGION_NAME_LENGTH = 255
MAX_LENGTH_FILLER = "M"                                  # TC_008: 255-char name is built from this
OVER_MAX_LENGTH_REGION_NAME = "R" * (MAX_REGION_NAME_LENGTH + 1)   # TC_009 (never saved)


def long_name(length: int, filler: str) -> str:
    """Unique name of exactly `length` characters."""
    suffix = unique("")  # "_" + 6 characters
    return filler * (length - len(suffix)) + suffix


# ---------------------------------------------------------------------------
# Region names per test case
# ---------------------------------------------------------------------------
# Typed but never saved
REGION_NAME_CLOSE_ICON_TEST = "Test Region Close Icon"   # TC_003
REGION_NAME_CANCEL_TEST = "Temp Region"                  # TC_005
WHITESPACE_ONLY_REGION_NAME = "   "                      # TC_007
PLACEHOLDER_TYPED_CHAR = "H"                             # TC_012
REGION_NAME_VALID_AFTER_ERROR = "Valid Region Name"      # TC_014
REGION_NAME_OFFLINE_TEST = "Temp Region Offline Test"    # TC_018
REGION_NAME_SESSION_CLEARED_TEST = "Session Cleared Region"  # TC_021

# Created by the test (base names - the test adds a unique suffix)
SCRIPT_INJECTION_PAYLOAD = "<script>alert(1)</script>"   # TC_010
SCRIPT_PAYLOAD_TEXT = "alert(1)"                         # TC_010: must not appear in a <script> element
SINGLE_CHARACTER_REGION_NAME = "R"                       # TC_011 (cannot be made unique - counted instead)
TRIMMED_REGION_NAME = "Test Region Untrimmed"            # TC_013
LEADING_TRAILING_SPACES = "  "                           # TC_013: placed before and after the name
REGION_NAME_NO_REFRESH_TEST = "Test Region No Refresh"   # TC_016
REGION_NAME_NOTIFICATION_TEST = "Test Region Notification"  # TC_017
REGION_NAME_DUPLICATE_TEST = "Test Region Duplicate"     # TC_019
REGION_NAME_DOUBLE_CLICK_TEST = "Test Region Double Click"  # TC_020
REGION_NAME_LOADING_STATE_TEST = "Test Region Loading State"  # TC_024
REGION_NAME_END_TO_END_TEST = "Test Region Bagmati"      # TC_025
REGION_NAME_UNAUTHORIZED_TEST = "Test Region Unauthorized"  # TC_026 (saved only if the app wrongly allows it)

# ---------------------------------------------------------------------------
# Coverage polygon: relative (x, y) click positions inside the modal map
# (used where the test steps say "draw a polygon": 005, 016, 018, 020, 021, 024, 026)
# ---------------------------------------------------------------------------
POLYGON_POINTS = [(0.30, 0.30), (0.70, 0.30), (0.70, 0.70), (0.30, 0.70)]

# ---------------------------------------------------------------------------
# API route pattern used to intercept create-region requests for
# network-failure / loading-state simulation tests (TC_018, TC_024).
# ---------------------------------------------------------------------------
CREATE_REGION_API_ROUTE_PATTERN = r".*/api/map/regions$"
LOADING_DELAY_MS = 1500                                  # TC_024