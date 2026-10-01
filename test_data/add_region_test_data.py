
# ---------------------------------------------------------------------------
# Confirmed UI copy (captured via Codegen)
# ---------------------------------------------------------------------------
import re


MODAL_TITLE = "Catalog - Add Region"
REGION_NAME_PLACEHOLDER = "e.g., Hilly Region"

# ---------------------------------------------------------------------------
# Expected validation / feedback messages
# ---------------------------------------------------------------------------
REGION_NAME_REQUIRED = "Region Name is required"
REGION_NAME_DUPLICATE = "Region Already exists"
REGION_NAME_TOO_LONG = "The label field must not be greater than 255 characters."

# ---------------------------------------------------------------------------
# Field-length boundaries
# ---------------------------------------------------------------------------
MAX_REGION_NAME_LENGTH = 255
MAX_LENGTH_REGION_NAME = "M" * MAX_REGION_NAME_LENGTH
OVER_MAX_LENGTH_REGION_NAME = "R" * (MAX_REGION_NAME_LENGTH + 1)

# ---------------------------------------------------------------------------
# General field test data
# ---------------------------------------------------------------------------
SINGLE_CHARACTER_REGION_NAME = "R"
WHITESPACE_ONLY_REGION_NAME = "   "
UNTRIMMED_REGION_NAME = "  Test Region  "
TRIMMED_REGION_NAME = "Test Region"

SCRIPT_INJECTION_PAYLOAD = "<script>alert(1)</script>"
SQL_INJECTION_PAYLOAD = "' OR '1'='1" 

# Success / error notifications (adjust to the exact app wording once confirmed)
REGION_ADDED_SUCCESS_PATTERN = re.compile(
    r"(added|created).*success|success.*(added|created)", re.IGNORECASE
)
NETWORK_ERROR_PATTERN = "Unauthenticated."
SESSION_ERROR_PATTERN = "Unable to reach the server. Check your connection and try again." 

# ---------------------------------------------------------------------------
# Region names used by specific scenario / end-to-end tests
# ---------------------------------------------------------------------------
REGION_NAME_CLOSE_ICON_TEST = "Test Region Close Icon"
REGION_NAME_ESC_TEST = "Test Region Esc"
REGION_NAME_CANCEL_TEST = "Temp Region"
REGION_NAME_NO_REFRESH_TEST = "Test Region No Refresh"
REGION_NAME_NOTIFICATION_TEST = "Test Region Notification"
REGION_NAME_OFFLINE_TEST = "Temp Region Offline Test"
REGION_NAME_DOUBLE_CLICK_TEST = "Test Region Double Click"
REGION_NAME_SESSION_CLEARED_TEST = "Session Cleared Region"
REGION_NAME_LOADING_STATE_TEST = "Test Region Loading State"
REGION_NAME_END_TO_END_TEST = "Test Region Bagmati"
REGION_NAME_VALID_GENERIC = "Valid Region Name"

# ---------------------------------------------------------------------------
# API route pattern used to intercept create-region requests for
# network-failure / loading-state simulation tests.
# ---------------------------------------------------------------------------
CREATE_REGION_API_ROUTE_PATTERN = r".*/api/map/regions$"