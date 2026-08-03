import os
import json
import shutil
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv

load_dotenv()

# Base project directory
BASE_DIR = os.path.dirname(__file__)

# External storage volume path (Will fallback to local if WD drive is unattached)
EXTERNAL_VOLUME = "/Volumes/WD_1TB/BILLSzuka_Resources"
LOCAL_DATA_DIR = os.path.join(BASE_DIR, "data")

def get_active_data_dir():
    if os.path.exists("/Volumes/WD_1TB"):
        os.makedirs(EXTERNAL_VOLUME, exist_ok=True)
        return EXTERNAL_VOLUME
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    return LOCAL_DATA_DIR

def migrate_local_data_to_external():
    """Sync local CSV resources to external WD drive when connected."""
    active_dir = get_active_data_dir()
    if active_dir == EXTERNAL_VOLUME and os.path.exists(LOCAL_DATA_DIR):
        for item in os.listdir(LOCAL_DATA_DIR):
            s = os.path.join(LOCAL_DATA_DIR, item)
            d = os.path.join(EXTERNAL_VOLUME, item)
            if os.path.isfile(s) and not os.path.exists(d):
                shutil.copy2(s, d)

# Configured paths
DATA_DIR = get_active_data_dir()
migrate_local_data_to_external()
