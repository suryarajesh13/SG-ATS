"""
Configuration settings for the hiring agent application.
"""
import os

# Reads from environment variable DEVELOPMENT_MODE.
# Defaults to True if not set, so local dev works out of the box.
# Set DEVELOPMENT_MODE=false in production to disable caching.
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
