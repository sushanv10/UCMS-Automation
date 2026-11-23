"""
Test data for Catalog - Edit Region
(TC_NETWORK_EXPLORER_CATALOG_EDIT_REGION_001 ... 056).

Values are copied 1:1 from the test-case sheet, one block per test case.

* Region IDs are auto-generated and change - no ID is stored here. Regions are
  found by NAME and their IDs are read from the Coverage tree at runtime.
* Regions that a test SAVES changes to are created per test with a unique name
  (unique(<prefix>)), and every new name that is saved is wrapped with unique()
  inside the tests, so re-running never collides.
  Exceptions that must keep the exact sheet value (a unique suffix would change
  the scenario): TC_028 ('E'), TC_031 ('20260'), TC_050 ('@@@###$$$').
* Regions that tests only open / cancel use a fixed name and are created only
  if they do not exist yet.
"""
import re

TC_PREFIX = "TC_EDIT_REGION"

# ---------------------------------------------------------------------------
# UI copy
# ---------------------------------------------------------------------------
MODAL_TITLE = "Catalog - Edit Region"
CANCEL_BUTTON_LABEL = "Cancel"
SAVE_BUTTON_LABEL = "Save Changes"
LOADING_BUTTON_TEXT = "Please wait"
REGION_NAME_PLACEHOLDER = "e.g. Hilly Region"               # TC_011
MAP_HELPER_TEXT = (                                           # TC_003
    "Click the map to add vertices, click a line to insert one, drag to move, "
    "and right-click a vertex to remove it. The polygon saves automatically after 3 points."
)
MAP_CAPTION_TEXT = "Draw a polygon on the map to define the coverage area."   # TC_003
REQUIRED_ASTERISK = "*"                                       # TC_008

# ---------------------------------------------------------------------------
# Validation / feedback messages
# ---------------------------------------------------------------------------
REGION_NAME_REQUIRED = "Region Name is required"
REGION_NAME_TOO_LONG = "The label field must not be greater than 255 characters."
DUPLICATE_PATTERN = re.compile(r"already exists|already been taken|duplicate", re.IGNORECASE)
REGION_UPDATED_SUCCESS_PATTERN = re.compile(
    r"(updated|saved).*success|success.*(updated|saved)", re.IGNORECASE
)
UNAUTHENTICATED_MESSAGE = "Unauthenticated."
SERVER_UNREACHABLE_MESSAGE = "Unable to reach the server. Check your connection and try again."
PERMISSION_PATTERN = re.compile(
    r"permission|unauthori[sz]ed|forbidden|not allowed|403", re.IGNORECASE
)
STACK_TRACE_PATTERN = re.compile(r"traceback|stack trace", re.IGNORECASE)

# ---------------------------------------------------------------------------
# Boundaries and viewports
# ---------------------------------------------------------------------------
MAX_NAME_LENGTH = 255
LOADING_DELAY_MS = 2000
# Approximate browser zoom 80% / 100% / 150% / 200% plus a 768 px wide window (TC_021)
ZOOM_VIEWPORTS = [(1500, 1000), (1200, 800), (800, 533), (600, 400), (768, 800)]

# ---------------------------------------------------------------------------
# Regions used by the UI cases (001 - 021)
# ---------------------------------------------------------------------------
REGION_DEFAULT = "Edit_Region_Test"                          # 001-003,005,008-018,020,021,041-045
REGION_PREFILL = "Edit_Region_Prefill_Test"                  # 004
REGION_OPEN_FIRST = "Edit_Region_Open_First_Test"            # 007
REGION_OPEN_SECOND = "Edit_Region_Open_Second_Test"          # 007
TYPED_INPUT = "ABC"                                          # 005

REGION_ID_CHECK = "Edit_Region_ID_Check_Test"                # 006
REGION_ID_CHECK_NEW = "Edit_Region_ID_Check_Updated"

PLACEHOLDER_TYPED_CHAR = "H"                                 # 011
CLOSE_ICON_NAME = "Edit Close Icon Test"                     # 012
ESCAPE_NAME = "Edit Escape Test"                             # 013
CANCEL_NAME = "Edit Cancel Test"                             # 014
BACKDROP_NAME = "Edit Backdrop Test"                         # 015
DISCARDED_NAME = "Discarded Value"                           # 017

REGION_ENTER_KEY = "Edit_Region_Enter_Key_Test"              # 019
ENTER_KEY_NEW = "Test Region Enter Key"

# ---------------------------------------------------------------------------
# Functional cases (022 - 040)
# ---------------------------------------------------------------------------
REGION_VALID_UPDATE = "Edit_Region_Valid_Update_Test"        # 022
VALID_UPDATE_NEW = "Edit_Region_Valid_Update_Updated"

REGION_NOTIFICATION = "Edit_Region_Notification_Test"        # 023
NOTIFICATION_NEW = "Edit Notification Test"

REGION_MODAL_CLOSE = "Edit_Region_Modal_Close_Test"          # 024
MODAL_CLOSE_NEW = "Edit Modal Close Test"

REGION_NO_CHANGE = "Edit_Region_No_Change_Test"              # 025

REGION_REVERT = "Edit_Region_Revert_Name_Test"               # 026
REVERT_TEMP = "Temporary Name"

REGION_CONSECUTIVE = "Edit_Region_Consecutive_Test"          # 027
CONSECUTIVE_NAMES = ["Edit One", "Edit Two", "Edit Three"]

REGION_MIN_LENGTH = "Edit_Region_Min_Length_Test"            # 028
MIN_LENGTH_NAME = "E"                                        # exact value (not unique)

REGION_MAX_255 = "Edit_Region_Max_Length_255_Test"           # 029
MAX_255_FILLER = "A"
REGION_MAX_254 = "Edit_Region_Max_Length_254_Test"           # 030
MAX_254_LENGTH = 254
MAX_254_FILLER = "B"

REGION_NUMERIC = "Edit_Region_Numeric_Name_Test"             # 031
NUMERIC_NAME = "20260"                                       # exact value (not unique)

REGION_ALPHANUMERIC = "Edit_Region_Alphanumeric_Name_Test"   # 032
ALPHANUMERIC_NAME = "Region 101 North"

REGION_SPECIAL = "Edit_Region_Special_Name_Test"             # 033
SPECIAL_NAME = "Bagmati-East (Zone_1) & Hills"

REGION_UNICODE = "Edit_Region_Unicode_Name_Test"             # 034
UNICODE_NAME = "बागमती प्रदेश"

REGION_CASE = "Edit_Region_Case_Test"                        # 035 (new name = original.upper())

REGION_TRIM = "Edit_Region_Trim_Test"                        # 037
TRIM_NAME = "Test Region Trim"                               # entered as ' <name> '

REGION_LOADING = "Edit_Region_Loading_State_Test"            # 039
LOADING_NEW = "Edit Loading State"

REGION_DOUBLE_CLICK = "Edit_Region_Double_Click_Test"        # 040
DOUBLE_CLICK_NEW = "Edit Double Click"

# ---------------------------------------------------------------------------
# Validation cases (041 - 052)
# ---------------------------------------------------------------------------
WHITESPACE_NAME = "   "                                      # 042 (3 spaces)
VALID_AFTER_ERROR = "Valid Region Name"                      # 043
OVER_MAX_NAME = "K" * (MAX_NAME_LENGTH + 1)                  # 044 (256)
PASTE_LONG_NAME = "J" * 300                                  # 045 (300)

REGION_DUPLICATE = "Edit_Region_Duplicate_Test"              # 046
REGION_DUPLICATE_EXISTING = "Edit_Region_Duplicate_Existing"
REGION_DUPLICATE_CASE = "Edit_Region_Duplicate_Case_Test"    # 047
REGION_DUPLICATE_CASE_EXISTING = "Edit_Region_Duplicate_Case_Existing"
REGION_DUPLICATE_SPACE = "Edit_Region_Duplicate_Space_Test"  # 048
REGION_DUPLICATE_SPACE_EXISTING = "Edit_Region_Duplicate_Space_Existing"

REGION_EMOJI = "Edit_Region_Emoji_Test"                      # 049
EMOJI_NAME = "Region 🏔️ North"

REGION_SPECIAL_ONLY = "Edit_Region_Special_Chars_Only_Test"  # 050
SPECIAL_ONLY_NAME = "@@@###$$$"                              # exact value (not unique)

REGION_MULTILINE = "Edit_Region_Multiline_Name_Test"         # 051
MULTILINE_TEXT = "Line One\nLine Two"

REGION_VALIDATION_FAILURE = "Edit_Region_Validation_Failure_Test"   # 052

# ---------------------------------------------------------------------------
# Security cases (053 - 056)
# ---------------------------------------------------------------------------
REGION_XSS = "Edit_Region_XSS_Name_Test"                     # 053
XSS_PAYLOAD = "<script>alert(1)</script>"
XSS_SELECTOR = 'script:has-text("alert(1)")'

REGION_HTML = "Edit_Region_HTML_Name_Test"                   # 055
HTML_PAYLOAD = "<b>Bold</b><img src=x onerror=alert(1)>"
HTML_SELECTOR = "img[src='x'], b:has-text('Bold')"

REGION_PERMISSION = "Edit_Region_Permission_Test"            # 056
PERMISSION_NEW = "Edit_Region_Permission_Updated"