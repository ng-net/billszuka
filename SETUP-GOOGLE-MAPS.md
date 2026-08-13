# Setup: Google Places API Configuration for BILLSzuka

To configure the Google Places API for the `gmaps_search.py` lead discovery tool, follow these steps within the Google Cloud Platform console and set up your API key in your project's `.env` file.

The `gmaps_search.py` script is already designed to read the `GOOGLE_MAPS_API_KEY` from your `.env` file. No code changes are needed in the script itself.

---

## Step-by-Step Configuration Guide

### 1. Set Up a Google Cloud Project
If you don't already have one, you'll need a Google Cloud Project:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.

### 2. Enable the Places API (New)
The `gmaps_search.py` script uses the modern "Places API (New)" with the `/v1/places:searchText` endpoint:
1. In the Google Cloud Console, navigate to the **APIs & Services > Library**.
2. Search for **"Places API (New)"** and enable it for your project.

### 3. Enable Billing
The Places API is a paid service. While Google offers a free tier, you must enable billing to use the live API:
1. In the Google Cloud Console, navigate to **Billing**.
2. Link an active billing account to your project.
*(The `gmaps_search.py` script includes a cost notice warning to prevent accidental excessive usage).*

### 4. Create and Restrict an API Key
To secure your credentials:
1. In the Google Cloud Console, navigate to **APIs & Services > Credentials**.
2. Click **+ Create Credentials** and select **API Key**.
3. Once generated, click edit on the key and under **API restrictions**, select **"Restrict key"**.
4. Check **"Places API (New)"** only. This prevents your key from being used for other Google Cloud services if leaked.

### 5. Add the API Key to Your `.env` File
The `gmaps_search.py` script looks for the `GOOGLE_MAPS_API_KEY` variable in a file named `.env` located in the project's root directory (`/Volumes/MC-BRAIN/Dev-Ext/BILLSzuka/.env`).

1. Open your `.env` file in the project's root directory.
2. Add your key at the bottom:
   ```env
   GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"
   ```
   *(Replace `"YOUR_API_KEY_HERE"` with the actual API key you obtained from the Google Cloud Console).*

---

## Development & Prototyping (Alternative)

If you do not want to set up billing yet, you can obtain a free, temporary **Maps Demo Key**:
1. Open [Google Maps Demo Key Generator](https://mapsplatform.google.com/maps-demo-key?utm_campaign=gmp_git_agentskills_v1).
2. Sign in with a personal Google account (no billing card required).
3. Generate the key, copy it, and paste it as `GOOGLE_MAPS_API_KEY` in your `.env`.

*Note: The script automatically falls back to a dry-run mock mode if no key is present in `.env`.*
