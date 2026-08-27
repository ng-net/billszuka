/**
 * datasetStorage.js — IndexedDB storage for preserving uploaded CSV datasets,
 * active dataset selection, and table snapshots across sessions per profile.
 */
import { getActiveProfile } from "./auth";

const DB_NAME = "billszuka_db";
const DB_VERSION = 1;
const STORE_NAME = "datasets";

function openDB() {
  return new Promise((resolve, reject) => {
    if (typeof window === "undefined" || !window.indexedDB) {
      resolve(null);
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function getActiveInfoKey(profileId) {
  return `active_info_${profileId || getActiveProfile() || "default"}`;
}
function getCustomDatasetKey(profileId) {
  return `custom_dataset_${profileId || getActiveProfile() || "default"}`;
}
function getSnapshotsKey(profileId) {
  return `snapshots_${profileId || getActiveProfile() || "default"}`;
}

export async function saveCustomDataset(profileId, { name, size, rows, columns, schema, parseTimeMs = 0 }) {
  try {
    const db = await openDB();
    if (!db) return;
    const now = Date.now();
    const datasetPayload = {
      name: name || "uploaded.csv",
      size: size || 0,
      rows: rows || [],
      columns: columns || [],
      schema: schema || [],
      parseTimeMs,
      updatedAt: now,
    };
    const activeInfo = {
      type: "custom",
      name: name || "uploaded.csv",
      size: size || 0,
      updatedAt: now,
    };

    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      store.put(datasetPayload, getCustomDatasetKey(profileId));
      store.put(activeInfo, getActiveInfoKey(profileId));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to persist custom dataset:", err);
  }
}

export async function getCustomDataset(profileId) {
  try {
    const db = await openDB();
    if (!db) return null;
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(getCustomDatasetKey(profileId));
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn("Failed to retrieve custom dataset:", err);
    return null;
  }
}

export async function getActiveDatasetInfo(profileId) {
  try {
    const db = await openDB();
    if (!db) return { type: "master", name: "master.csv" };
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(getActiveInfoKey(profileId));
      req.onsuccess = () => resolve(req.result || { type: "master", name: "master.csv" });
      req.onerror = () => reject(req.error);
    });
  } catch {
    return { type: "master", name: "master.csv" };
  }
}

export async function setActiveDatasetType(profileId, type, meta = {}) {
  try {
    const db = await openDB();
    if (!db) return;
    const activeInfo = {
      type: type === "custom" ? "custom" : "master",
      name: meta.name || (type === "custom" ? "uploaded.csv" : "master.csv"),
      size: meta.size || 0,
      updatedAt: Date.now(),
    };
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      store.put(activeInfo, getActiveInfoKey(profileId));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to set active dataset type:", err);
  }
}

export async function clearCustomDataset(profileId) {
  try {
    const db = await openDB();
    if (!db) return;
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      store.delete(getCustomDatasetKey(profileId));
      store.put({ type: "master", name: "master.csv", updatedAt: Date.now() }, getActiveInfoKey(profileId));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to clear custom dataset:", err);
  }
}

// --- Snapshots / Time-travel ---

export async function saveSnapshot(profileId, snapshotData) {
  try {
    const db = await openDB();
    if (!db) return;
    
    // First get existing snapshots
    let snapshots = await getSnapshots(profileId);
    
    // Add new snapshot
    snapshots.push({
      ...snapshotData,
      id: Date.now().toString(),
      timestamp: Date.now()
    });
    
    // Keep only last 3
    if (snapshots.length > 3) {
      snapshots = snapshots.slice(-3);
    }
    
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      store.put(snapshots, getSnapshotsKey(profileId));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to save snapshot:", err);
  }
}

export async function getSnapshots(profileId) {
  try {
    const db = await openDB();
    if (!db) return [];
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(getSnapshotsKey(profileId));
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn("Failed to retrieve snapshots:", err);
    return [];
  }
}
