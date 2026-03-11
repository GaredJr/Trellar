from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Keep tests deterministic and independent of local .env Supabase credentials.
os.environ.setdefault("TRELLAR_USE_SUPABASE", "0")
