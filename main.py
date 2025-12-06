"""
=============================================================================
MAIN ENTRY POINT - CRYPTO ANALYTICS SYSTEM
=============================================================================
Initializes configuration, logs, and starts the GUI.
"""
import argparse
import logging
import tkinter as tk

import urllib3

from ui import CryptoAnalyticsApp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = [
    'pymongo',
    'pydantic',
    'mongoengine',
    'requests',
    'scrapy',
    'dnspython'
]

print(">>> SYSTEM CHECK: Verifying installed packages...")
for package in REQUIRED_PACKAGES:
    try:
        __import__(package.replace('-', '_'))
    except ImportError:
        logger.warning("Package '%s' might be missing.", package)

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crypto Analytics System Enterprise")
    parser.add_argument('--limit', type=int, default=50, help="Number of tokens to track")
    args = parser.parse_args()

    print(f">>> Initializing GUI with limit={args.limit}...")

    root = tk.Tk()
    app = CryptoAnalyticsApp(root, limit=args.limit)
    root.mainloop()