"""
Test data for Network Details modal.

Mirrors the 'Test Data' column of the Network Details manual test case sheet
(TC_NETWORK_DETAILS_001 .. 027).

NOTE: Region / Network IDs are system-generated and change on every creation,
so NO ID is hard-coded here. Tests resolve IDs at runtime from the Coverage
tree rows ("<ID> - <Name>").
"""
import re

# ---------------------------------------------------------------------------
# Modal chrome
# ---------------------------------------------------------------------------
MODAL_TITLE = "Network Details"
EDIT_MODAL_TITLE = "Catalog - Edit Network"

# ---------------------------------------------------------------------------
# Primary region / network (TC_001–006, 009–011, 013–016, 022–023, 026–027)
# Fixed names from the sheet. Created only if missing via _ensure_region /
# _ensure_network so re-runs never collide.
# ---------------------------------------------------------------------------
PRIMARY_REGION_NAME = "Region - Network_Details_Test"
PRIMARY_NETWORK_NAME = "Network_Details_Test"

# ---------------------------------------------------------------------------
# Scenario-specific network name prefixes (wrapped with unique() on create)
# ---------------------------------------------------------------------------
NAME_ACTIVE = "Network_Details_Active_Test"              # TC_007
NAME_INACTIVE = "Network_Details_Inactive_Test"          # TC_008
NAME_FRESH = "Network_Details_Fresh_Test"                # TC_012
NAME_DELETE = "Network_Details_Delete_Test"              # TC_017
NAME_NO_POLYGON = "Network_Details_No_Polygon_Test"      # TC_019
NAME_POLYGON = "Network_Details_Polygon_Test"            # TC_021
NAME_RENAME_REGION_OLD = "Region - Network_Details_Rename_Test"   # TC_020
NAME_RENAME_REGION_NEW = "Region - Network_Details_Renamed_Test"  # TC_020
NAME_RENAME_NETWORK = "Network_Details_Rename_Test"      # TC_020
NAME_UNICODE = "बागमती नेटवर्क"                           # TC_024
NAME_HTML_XSS = "<b>XSS Test</b>"                        # TC_025

# Backwards-compatible aliases used by older test helpers
ACTIVE_NETWORK_PREFIX = NAME_ACTIVE
INACTIVE_NETWORK_PREFIX = NAME_INACTIVE
SECOND_NETWORK_PREFIX = NAME_FRESH
NO_POLYGON_NETWORK_PREFIX = NAME_NO_POLYGON
POLYGON_NETWORK_PREFIX = NAME_POLYGON
UNICODE_NETWORK_PREFIX = NAME_UNICODE
HTML_NETWORK_PREFIX = NAME_HTML_XSS

# ---------------------------------------------------------------------------
# Coverage polygon (4 vertices – matches sheet and Edit Network create path)
# Approx. relative positions inside the map box.
# ---------------------------------------------------------------------------
POLYGON_POINTS = [(0.30, 0.30), (0.70, 0.30), (0.70, 0.70), (0.30, 0.70)]
POLYGON_VERTEX_COUNT = 4

# ---------------------------------------------------------------------------
# Expected UI text
# ---------------------------------------------------------------------------
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"
NO_POLYGON_MESSAGE = "No coverage polygon defined."
POLYGON_INFO_PATTERN = r"^Polygon defined with \d+ vertices?\.?$"
POLYGON_INFO_4 = "Polygon defined with 4 vertices."

# TC_015 – load failure
LOAD_ERROR_PATTERN = (
    r"(failed to load|unable to load|something went wrong|"
    r"try again|network not found|could not load)"
)

# TC_017 – network deleted in another session
NETWORK_NOT_FOUND_PATTERN = re.compile(
    r"(network not found|no longer exists|does not exist|not found)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Long-name boundary (TC_018)
# ---------------------------------------------------------------------------
LONG_NAME_LENGTH = 255
LONG_REGION_FILLER = "R"
LONG_NETWORK_FILLER = "N"

# ---------------------------------------------------------------------------
# Keyboard input used to verify read-only fields (TC_004, TC_005, TC_014)
# ---------------------------------------------------------------------------
READ_ONLY_TYPED_INPUT = "Read Only Field Test"
ID_EDIT_TYPED = "ID Edit Test"
LABEL_EDIT_TYPED = "Label Edit Test"

# TC_026: how many times the modal is opened and closed
REPEAT_COUNT = 4
"""
Test data for Network Details modal.

Mirrors the 'Test Data' column of the Network Details manual test case sheet
(TC_NETWORK_DETAILS_001 .. 027).

NOTE: Region / Network IDs are system-generated and change on every creation,
so NO ID is hard-coded here. Tests resolve IDs at runtime from the Coverage
tree rows ("<ID> - <Name>").
"""
import re

# ---------------------------------------------------------------------------
# Modal chrome
# ---------------------------------------------------------------------------
MODAL_TITLE = "Network Details"
EDIT_MODAL_TITLE = "Catalog - Edit Network"

# ---------------------------------------------------------------------------
# Primary region / network (TC_001–006, 009–011, 013–016, 022–023, 026–027)
# Fixed names from the sheet. Created only if missing via _ensure_region /
# _ensure_network so re-runs never collide.
# ---------------------------------------------------------------------------
PRIMARY_REGION_NAME = "Region - Network_Details_Test"
PRIMARY_NETWORK_NAME = "Network_Details_Test"

# ---------------------------------------------------------------------------
# Scenario-specific network name prefixes (wrapped with unique() on create)
# ---------------------------------------------------------------------------
NAME_ACTIVE = "Network_Details_Active_Test"              # TC_007
NAME_INACTIVE = "Network_Details_Inactive_Test"          # TC_008
NAME_FRESH = "Network_Details_Fresh_Test"                # TC_012
NAME_DELETE = "Network_Details_Delete_Test"              # TC_017
NAME_NO_POLYGON = "Network_Details_No_Polygon_Test"      # TC_019
NAME_POLYGON = "Network_Details_Polygon_Test"            # TC_021
NAME_RENAME_REGION_OLD = "Region - Network_Details_Rename_Test"   # TC_020
NAME_RENAME_REGION_NEW = "Region - Network_Details_Renamed_Test"  # TC_020
NAME_RENAME_NETWORK = "Network_Details_Rename_Test"      # TC_020
NAME_UNICODE = "बागमती नेटवर्क"                           # TC_024
NAME_HTML_XSS = "<b>XSS Test</b>"                        # TC_025

# Backwards-compatible aliases used by older test helpers
ACTIVE_NETWORK_PREFIX = NAME_ACTIVE
INACTIVE_NETWORK_PREFIX = NAME_INACTIVE
SECOND_NETWORK_PREFIX = NAME_FRESH
NO_POLYGON_NETWORK_PREFIX = NAME_NO_POLYGON
POLYGON_NETWORK_PREFIX = NAME_POLYGON
UNICODE_NETWORK_PREFIX = NAME_UNICODE
HTML_NETWORK_PREFIX = NAME_HTML_XSS

# ---------------------------------------------------------------------------
# Coverage polygon (4 vertices – matches sheet and Edit Network create path)
# Approx. relative positions inside the map box.
# ---------------------------------------------------------------------------
POLYGON_POINTS = [(0.30, 0.30), (0.70, 0.30), (0.70, 0.70), (0.30, 0.70)]
POLYGON_VERTEX_COUNT = 4

# ---------------------------------------------------------------------------
# Expected UI text
# ---------------------------------------------------------------------------
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"
NO_POLYGON_MESSAGE = "No coverage polygon defined."
POLYGON_INFO_PATTERN = r"^Polygon defined with \d+ vertices?\.?$"
POLYGON_INFO_4 = "Polygon defined with 4 vertices."

# TC_015 – load failure
LOAD_ERROR_PATTERN = (
    r"(failed to load|unable to load|something went wrong|"
    r"try again|network not found|could not load)"
)

# TC_017 – network deleted in another session
NETWORK_NOT_FOUND_PATTERN = re.compile(
    r"(network not found|no longer exists|does not exist|not found)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Long-name boundary (TC_018)
# ---------------------------------------------------------------------------
LONG_NAME_LENGTH = 255
LONG_REGION_FILLER = "R"
LONG_NETWORK_FILLER = "N"

# ---------------------------------------------------------------------------
# Keyboard input used to verify read-only fields (TC_004, TC_005, TC_014)
# ---------------------------------------------------------------------------
READ_ONLY_TYPED_INPUT = "Read Only Field Test"
ID_EDIT_TYPED = "ID Edit Test"
LABEL_EDIT_TYPED = "Label Edit Test"

# TC_026: how many times the modal is opened and closed
REPEAT_COUNT = 4
