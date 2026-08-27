// auth.js — Lightweight profile/session manager

const KEY_ACTIVE = "czat-table.activeProfile";
const KEY_PROFILES = "czat-table.profiles";

const DEFAULT_PROFILES = ["Iz", "Marceli", "Guest"];

export function getActiveProfile() {
  if (typeof window === "undefined" || !window.localStorage) return null;
  return localStorage.getItem(KEY_ACTIVE) || null;
}

export function setActiveProfile(profileId) {
  if (typeof window === "undefined" || !window.localStorage) return;
  if (!profileId) {
    localStorage.removeItem(KEY_ACTIVE);
  } else {
    localStorage.setItem(KEY_ACTIVE, profileId);
    
    // Add to available profiles if not exists
    const profiles = getAvailableProfiles();
    if (!profiles.includes(profileId)) {
      profiles.push(profileId);
      localStorage.setItem(KEY_PROFILES, JSON.stringify(profiles));
    }
  }
}

export function getAvailableProfiles() {
  if (typeof window === "undefined" || !window.localStorage) return DEFAULT_PROFILES;
  try {
    const raw = localStorage.getItem(KEY_PROFILES);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {}
  return DEFAULT_PROFILES;
}
