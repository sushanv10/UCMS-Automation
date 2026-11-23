"""
Test data for Catalog - Edit Network
(TC_NETWORK_EXPLORER_CATALOG_EDIT_NETWORK_001 ... 109).

Values are copied 1:1 from the test-case sheet. Network names that are
created or saved by a test are wrapped with utils.helpers.unique() inside the
tests, so every constant below is a base name / prefix and re-runs never
collide inside the single shared region.
"""
import re

# ---------------------------------------------------------------------------
# Regions (only ONE shared region; created only if it does not exist yet)
# OTHER_REGION_NAME is needed only by TC_073 (cross-region duplicate rule).
# ---------------------------------------------------------------------------
REGION_NAME = "Region-Edit_Network_Test"
OTHER_REGION_NAME = "Region-Edit_Network_Other"

# ---------------------------------------------------------------------------
# UI copy
# ---------------------------------------------------------------------------
MODAL_TITLE = "Catalog - Edit Network"
NETWORK_NAME_PLACEHOLDER = "e.g., Lalitpur"
CANCEL_BUTTON_LABEL = "Cancel"
LOADING_BUTTON_TEXT = "Please wait"
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"

# ---------------------------------------------------------------------------
# Validation / feedback messages
# ---------------------------------------------------------------------------
NETWORK_NAME_REQUIRED = "Network Name is required"
NETWORK_NAME_TOO_LONG = "The label field must not be greater than 255 characters."
DETAILS_TOO_LONG_PATTERN = re.compile(r"must not be greater than", re.IGNORECASE)
DUPLICATE_ERROR_PATTERN = re.compile(
    r"already exists|already been taken|duplicate", re.IGNORECASE
)
SUCCESS_PATTERN = re.compile(r"success", re.IGNORECASE)
UNAUTHENTICATED_MESSAGE = "Unauthenticated."
SERVER_UNREACHABLE_MESSAGE = (
    "Unable to reach the server. Check your connection and try again."
)
RAW_SERVER_ERROR_PATTERN = re.compile(r"traceback|stack trace", re.IGNORECASE)

# ---------------------------------------------------------------------------
# API route used to intercept the update request (non-GET only).
# Adjust once developers confirm the exact endpoint.
# ---------------------------------------------------------------------------
UPDATE_NETWORK_API_ROUTE_PATTERN = r".*/api/map/networks/[^/]+/?$"

# ---------------------------------------------------------------------------
# Polygon (precondition: "valid polygon (4 vertices)")
# Relative positions inside the map container.
# ---------------------------------------------------------------------------
POLYGON_POINTS = [(0.30, 0.30), (0.70, 0.30), (0.70, 0.70), (0.30, 0.70)]
POLYGON_VERTEX_COUNT = 4
NEW_VERTEX_POINT = (0.85, 0.80)

# ---------------------------------------------------------------------------
# Shared values
# ---------------------------------------------------------------------------
DETAILS_ORIGINAL = "Original details for edit test"
TYPED_INPUT = "ABC"

# Approximate browser zoom 80% / 100% / 150% / 200% as viewport sizes (TC_024)
ZOOM_VIEWPORTS = [(1500, 1000), (1200, 800), (800, 533), (600, 400)]

# ---------------------------------------------------------------------------
# UI cases (001 - 025)
# ---------------------------------------------------------------------------
DEFAULT_EDIT_NAME = "Edit_Network_Test"                      # 001-003,005,006,009-012,014-021,023-025

NAME_PREFILL = "Edit_Network_Prefill_Test"              # 004
DETAILS_PREFILL = "Prefill details for Edit Network test"

NAME_OTHER = "Edit_Network_Other_Test"                  # 008
DETAILS_OTHER = "Other network details"

NAME_ACTIVE_SAVED = "Edit_Network_Active_Test"          # 013
NAME_INACTIVE_SAVED = "Edit_Network_Inactive_Test"

PLACEHOLDER_TYPED_CHAR = "L"                            # 012

CLOSE_ICON_NAME = "Edit Close Icon Test"                # 015
CLOSE_ICON_DETAILS = "Close icon details"
ESCAPE_NAME = "Edit Escape Test"                        # 016
BACKDROP_NAME = "Edit Backdrop Test"                    # 017
CANCEL_NAME = "Edit_Network_Cancel_Test"                # 018
CANCEL_DETAILS = "Cancel_Test_Details"
DISCARDED_NAME = "Discarded Value"                      # 020
DISCARDED_DETAILS = "Discarded details"

ENTER_ORIGINAL = "Edit_Network_Enter_Key_Test"          # 022
ENTER_NEW = "Test Network Enter Key"

# ---------------------------------------------------------------------------
# Functional cases (038 - 063)
# ---------------------------------------------------------------------------
NAME_ONLY_ORIGINAL = "Edit_Network_Name_Only_Test"      # 038
NAME_ONLY_NEW = "Edit_Network_Name_Only_Updated"

DETAILS_ONLY_ORIGINAL = "Edit_Network_Details_Only_Test"   # 039
DETAILS_ONLY_NEW = "Test segment covering central Naya Baneshwor"

ACTIVE_ONLY_ORIGINAL = "Edit_Network_Active_Only_Test"  # 041

MULTI_ORIGINAL = "Edit_Network_Multi_Field_Test"        # 042
MULTI_NEW = "Edit_Network_Multi_Field_Updated"
MULTI_DETAILS_NEW = "Updated multi-field details"

VALID_SAVE_ORIGINAL = "Edit_Network_Valid_Save_Test"    # 043
VALID_SAVE_NEW = "Edit_Network_Valid_Save_Updated"
VALID_SAVE_DETAILS = "Valid save details"

NOTIFICATION_ORIGINAL = "Edit_Network_Notification_Test"    # 044
NOTIFICATION_NEW = "Edit Notification Test"

MODAL_CLOSE_ORIGINAL = "Edit_Network_Modal_Close_Test"  # 045
MODAL_CLOSE_NEW = "Edit Modal Close Test"

NO_CHANGE_ORIGINAL = "Edit_Network_No_Change_Test"      # 046

REVERT_ORIGINAL = "Edit_Network_Revert_Name_Test"       # 047
REVERT_TEMP = "Temporary Name"

CONSECUTIVE_ORIGINAL = "Edit_Network_Consecutive_Test"  # 048
CONSECUTIVE_NAMES = ["Edit One", "Edit Two", "Edit Three"]

REOPEN_ORIGINAL = "Edit_Network_Reopen_After_Save_Test"     # 049
REOPEN_NEW = "Edit_Network_Reopen_After_Save_Updated"
REOPEN_DETAILS_NEW = "Reopen after save details"

MIN_LENGTH_ORIGINAL = "Edit_Network_Min_Length_Test"   # 050
MIN_LENGTH_NEW = "E"                                    # exact value (kept as in sheet)

MAX_NAME_LENGTH = 255
MAX_255_ORIGINAL = "Edit_Network_Max_Length_255_Test"  # 051
MAX_255_FILLER = "A"
MAX_254_ORIGINAL = "Edit_Network_Max_Length_254_Test"  # 052
MAX_254_LENGTH = 254
MAX_254_FILLER = "B"

NUMERIC_ORIGINAL = "Edit_Network_Numeric_Name_Test"     # 053
NUMERIC_NEW = "20260"                                   # exact value (kept as in sheet)

ALPHANUMERIC_ORIGINAL = "Edit_Network_Alphanumeric_Name_Test"   # 054
ALPHANUMERIC_NEW = "Metro Network 101"

SPECIAL_ORIGINAL = "Edit_Network_Special_Name_Test"     # 055
SPECIAL_NEW = "Lalitpur-Metro (Zone_1) & Hills"

UNICODE_ORIGINAL = "Edit_Network_Unicode_Name_Test"     # 056
UNICODE_NEW = "ललितपुर नेटवर्क"

CASE_ORIGINAL = "Edit_Network_Case_Test"                # 057 (new name = original.upper())

TRIM_ORIGINAL = "Edit_Network_Trim_Test"                # 058
TRIM_BASE = "Test Network Trim"                         # entered as ' <base> '

MULTILINE_DETAILS_ORIGINAL = "Edit_Network_Multiline_Details_Test"  # 059
MULTILINE_DETAILS_NEW = "Line one\nLine two"

SPECIAL_DETAILS_ORIGINAL = "Edit_Network_Special_Details_Test"      # 060
SPECIAL_DETAILS_NEW = "Zone #1 / Phase-2 (100% fiber) - काठमाडौं"

CLEAR_DETAILS_ORIGINAL = "Edit_Network_Clear_Details_Test"          # 061
CLEAR_DETAILS_TEXT = "Details to be cleared"

LOADING_ORIGINAL = "Edit_Network_Loading_State_Test"    # 062
LOADING_NEW = "Edit_Network_Loading_State_Updated"
LOADING_DELAY_MS = 2000

DOUBLE_CLICK_ORIGINAL = "Edit_Network_Double_Click_Test"    # 063
DOUBLE_CLICK_NEW = "Edit Double Click"

# ---------------------------------------------------------------------------
# Validation cases (064 - 079)
# ---------------------------------------------------------------------------
EMPTY_NAME_ORIGINAL = "Edit_Network_Empty_Name_Test"            # 064
WHITESPACE_NAME_ORIGINAL = "Edit_Network_Whitespace_Name_Test"  # 065
WHITESPACE_NAME = "     "

VALIDATION_CLEAR_ORIGINAL = "Edit_Network_Validation_Clear_Test"    # 066
VALIDATION_CLEAR_NEW = "Edit_Network_Validation_Cleared"

EXCEEDED_ORIGINAL = "Edit_Network_Max_Length_Exceeded_Test"     # 067
OVER_MAX_NAME_K = "K" * (MAX_NAME_LENGTH + 1)

PASTE_LONG_ORIGINAL = "Edit_Network_Paste_Long_Name_Test"      # 068
PASTE_LONG_NAME = "J" * 300

LONG_DETAILS_ORIGINAL = "Edit_Network_Long_Details_Test"       # 069
OVER_MAX_DETAILS = "D" * 5001

DUP_EXACT_ORIGINAL = "Edit_Network_Duplicate_Test"              # 070
DUP_EXACT_EXISTING = "Edit_Network_Duplicate_Existing"

DUP_CASE_ORIGINAL = "Edit_Network_Duplicate_Case_Test"          # 071
DUP_CASE_EXISTING = "Edit_Network_Duplicate_Case_Existing"

DUP_SPACE_ORIGINAL = "Edit_Network_Duplicate_Space_Test"        # 072
DUP_SPACE_EXISTING = "Edit_Network_Duplicate_Space_Existing"

CROSS_REGION_ORIGINAL = "Edit_Network_Cross_Region_Test"        # 073
CROSS_REGION_EXISTING = "Edit_Network_Cross_Region_Existing"

EMOJI_ORIGINAL = "Edit_Network_Emoji_Test"                      # 074
EMOJI_NEW = "Network 🏔️ South"

SPECIAL_ONLY_ORIGINAL = "Edit_Network_Special_Chars_Only_Test"  # 075
SPECIAL_ONLY_NEW = "@@@###$$$"                                  # exact value

MULTILINE_NAME_ORIGINAL = "Edit_Network_Multiline_Name_Test"    # 076
MULTILINE_NAME_NEW = "Line One\nLine Two"

VALIDATION_FAILURE_ORIGINAL = "Edit_Network_Validation_Failure_Test"    # 079

# ---------------------------------------------------------------------------
# Security cases (080 - 083)
# ---------------------------------------------------------------------------
XSS_NAME_ORIGINAL = "Edit_Network_XSS_Name_Test"                # 080
XSS_NAME_PAYLOAD = "<script>alert('test')</script>"

XSS_DETAILS_ORIGINAL = "Edit_Network_XSS_Details_Test"          # 081
XSS_DETAILS_PAYLOAD = "<img src=x onerror=alert(1)>"

HTML_NAME_ORIGINAL = "Edit_Network_HTML_Name_Test"              # 082
HTML_NAME_PAYLOAD = "<b>Bold</b><img src=x onerror=alert(1)>"

PERMISSION_ORIGINAL = "Edit_Network_Permission_Test"            # 083
PERMISSION_NEW = "Edit_Network_Permission_Updated"

# ---------------------------------------------------------------------------
# Error handling cases (085 - 093)
# ---------------------------------------------------------------------------
OFFLINE_ORIGINAL = "Edit_Network_Offline_Test"                  # 085
OFFLINE_NEW = "Offline Edit Test"

SERVER_ERROR_ORIGINAL = "Edit_Network_Server_Error_Test"        # 086
SERVER_ERROR_NEW = "Server Error Test"

TIMEOUT_ORIGINAL = "Edit_Network_Timeout_Test"                  # 087
TIMEOUT_NEW = "Timeout Test"
TIMEOUT_DELAY_MS = 3000

BACKEND_VALIDATION_ORIGINAL = "Edit_Network_Backend_Validation_Test"    # 088
BACKEND_VALIDATION_NAME = "L" * (MAX_NAME_LENGTH + 1)

SESSION_CLEARED_ORIGINAL = "Edit_Network_Session_Cleared_Test"  # 089
SESSION_CLEARED_NEW = "Session Cleared Edit"

EXPIRED_SESSION_ORIGINAL = "Edit_Network_Expired_Session_Test"  # 090
EXPIRED_SESSION_NEW = "Expired Session Edit"

REFRESH_ORIGINAL = "Edit_Network_Page_Refresh_Test"             # 091
REFRESH_NEW = "Refresh Test"

CONCURRENT_ORIGINAL = "Edit_Network_Concurrent_Test"            # 093
CONCURRENT_NAME_A = "Edited By A"
CONCURRENT_NAME_B = "Edited By B"

# ---------------------------------------------------------------------------
# Hierarchy / Details verification cases (094 - 109)
# ---------------------------------------------------------------------------
HIERARCHY_UPDATE_ORIGINAL = "Edit_Network_Hierarchy_Update_Test"    # 094
HIERARCHY_UPDATE_NEW = "Edit_Network_Hierarchy_Updated"
HIERARCHY_UPDATE_DETAILS = "Hierarchy updated details"

REFRESH_PERSIST_ORIGINAL = "Edit_Network_Refresh_Persist_Test"      # 095
REFRESH_PERSIST_NEW = "Edit_Network_Refresh_Persist_Updated"

ID_UNCHANGED_ORIGINAL = "Edit_Network_ID_Unchanged_Test"            # 096
ID_UNCHANGED_NEW = "Edit_Network_ID_Unchanged_Updated"

OLD_REMOVED_ORIGINAL = "Edit_Network_Old_Name_Removed_Test"         # 097
OLD_REMOVED_NEW = "Edit_Network_Old_Name_Removed_Updated"

ISOLATION_ORIGINAL = "Edit_Network_Isolation_Test"                  # 098
ISOLATION_NEW = "Edit_Network_Isolation_Updated"
ISOLATION_OTHER = "Edit_Network_Isolation_Other"
ISOLATION_OTHER_DETAILS = "Isolation other details"

LONG_DISPLAY_ORIGINAL = "Edit_Network_Long_Name_Display_Test"       # 099
LONG_DISPLAY_BASE = "ABCDEFGHIJ" * 5
LONG_DISPLAY_LENGTH = 50

SPECIAL_DISPLAY_ORIGINAL = "Edit_Network_Special_Display_Test"      # 100
SPECIAL_DISPLAY_NEW = 'A&B <Network> "North"'

OTHER_USER_ORIGINAL = "Edit_Network_Other_User_Test"                # 101
OTHER_USER_NEW = "Edit_Network_Other_User_Updated"

LOGOUT_LOGIN_ORIGINAL = "Edit_Network_Logout_Login_Test"            # 102
LOGOUT_LOGIN_NEW = "Edit_Network_Logout_Login_Updated"

ADD_DUPLICATE_ORIGINAL = "Edit_Network_Add_Duplicate_Test"          # 103
ADD_DUPLICATE_NEW = "Edit_Network_Add_Duplicate_Updated"

OLD_REUSE_ORIGINAL = "Edit_Network_Old_Name_Reuse_Test"             # 104
OLD_REUSE_NEW = "Edit_Network_Old_Name_Reuse_Updated"

DETAILS_NAME_ORIGINAL = "Edit_Network_Details_Name_Test"            # 105
DETAILS_NAME_NEW = "Edit_Network_Details_Name_Updated"

DETAILS_ID_ORIGINAL = "Edit_Network_Details_ID_Test"                # 106
DETAILS_ID_NEW = "Edit_Network_Details_ID_Updated"

DETAILS_PATH_ORIGINAL = "Edit_Network_Details_Path_Test"            # 107
DETAILS_PATH_NEW = "Edit_Network_Details_Path_Updated"

DETAILS_TEXT_ORIGINAL = "Edit_Network_Details_Text_Test"            # 108
DETAILS_TEXT_NEW = "Updated network details"

STATUS_BADGE_ORIGINAL = "Edit_Network_Status_Badge_Test"            # 109
