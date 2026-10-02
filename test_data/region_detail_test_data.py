# ---------------------------------------------------------------------------
# Confirmed UI copy (captured via Codegen)
# ---------------------------------------------------------------------------
from uuid import uuid4


MODAL_TITLE = "Region Details"
EDIT_MODAL_TITLE = "Catalog - Edit Region"


# ---------------------------------------------------------------------------
# Primary seeded region used by most tests (TC_001 - TC_009, 015 - 027)
# ---------------------------------------------------------------------------
PRIMARY_REGION_ID = "G36"
PRIMARY_REGION_NAME = "Test Region"

# A second, distinct seeded region used for the "not a sibling region" /
# "opens fresh, not cached" checks (TC_007, TC_022).
SECONDARY_REGION_ID = "G03"
SECONDARY_REGION_NAME = "Bagmati Province"

# ---------------------------------------------------------------------------
# Two regions sharing an identical Label but different IDs (TC_010)
# ---------------------------------------------------------------------------
DUPLICATE_LABEL_REGION_A_ID = "G31"
DUPLICATE_LABEL_REGION_B_ID = "G32"
DUPLICATE_LABEL_REGION_NAME = "Duplicate Region"

# ---------------------------------------------------------------------------
# A region with a very long name, rendered truncated with an ellipsis in
# the hierarchy tree (TC_011).
# ---------------------------------------------------------------------------
LONG_NAME_REGION_ID = "G33"

LONG_NAME_REGION_NAME = "M" * 255

# ---------------------------------------------------------------------------
# A region with a single-character name (TC_012).
# ---------------------------------------------------------------------------
SHORT_NAME_REGION_ID = "G35"
SHORT_NAME_REGION_NAME = "R"

# ---------------------------------------------------------------------------
# Injection-payload region name (TC_013). No pre-existing seeded region
# with this name was observed, so the test creates one itself (via
# AddRegionModal) rather than depending on external seed data.
# ---------------------------------------------------------------------------
SCRIPT_INJECTION_REGION_NAME = f"<script>alert({uuid4().hex[:8]})</script>"
SQL_INJECTION_REGION_NAME = "' OR '1'='1"


# ---------------------------------------------------------------------------
UNTRIMMED_REGION_NAME = "  Trimmed Test Region  "
TRIMMED_REGION_NAME = "Trimmed Test Region"

# ---------------------------------------------------------------------------
# Renamed-region data used by the "reflects updated Label after an edit"
# scenario (referenced from the earlier full test-case list; not in the
# condensed 28-case sheet but kept here in case that case is reinstated).
# ---------------------------------------------------------------------------
RENAMED_REGION_NAME = "Renamed Test Region"

# ---------------------------------------------------------------------------
# Keyboard input used to verify the read-only fields reject typing (TC_028)
# ---------------------------------------------------------------------------
READ_ONLY_FIELD_TYPED_INPUT = "abc123"