from .v1_to_v2 import migrate_v1_to_v2
from .v2_to_v3 import migrate_v2_to_v3

migrations = {
    (1, 2): migrate_v1_to_v2,
    (2, 3): migrate_v2_to_v3,
}
