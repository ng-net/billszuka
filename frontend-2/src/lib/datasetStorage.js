/**
 * datasetStorage.js — IndexedDB storage for preserving uploaded CSV datasets
 * and active dataset selection across reloads and logout/login sessions.
 *
 * Uses IndexedDB to bypass the 5MB localStorage quota limit, allowing datasets
 * with thousands of rows / megabytes of data to persist smoothly.
 */

const DB_NAME = "billszuka_db";
const DB_VERSION = 1;
const STORE_NAME = "datasets";

const KEY_ACTIVE_INFO = "active_info";
const KEY_CUSTOM_DATASET = "custom_dataset";

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

/**
 * Save an uploaded CSV dataset (parsed rows, columns, schema, metadata).
 */
export async function saveCustomDataset({ name, size, rows, columns, schema, parseTimeMs = 0 }) {
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
      store.put(datasetPayload, KEY_CUSTOM_DATASET);
      store.put(activeInfo, KEY_ACTIVE_INFO);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to persist custom dataset to IndexedDB:", err);
  }
}

/**
 * Get the stored custom dataset if available.
 */
export async function getCustomDataset() {
  try {
    const db = await openDB();
    if (!db) return null;
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(KEY_CUSTOM_DATASET);
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  } catch (err) {
    console.warn("Failed to retrieve custom dataset from IndexedDB:", err);
    return null;
  }
}

/**
 * Get active dataset metadata ({ type: "master" | "custom", name: string, size?: number }).
 */
export async function getActiveDatasetInfo() {
  try {
    const db = await openDB();
    if (!db) return { type: "master", name: "master.csv" };
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(KEY_ACTIVE_INFO);
      req.onsuccess = () => resolve(req.result || { type: "master", name: "master.csv" });
      req.onerror = () => reject(req.error);
    });
  } catch {
    return { type: "master", name: "master.csv" };
  }
}

/**
 * Set active dataset type ("master" or "custom").
 */
export async function setActiveDatasetType(type, meta = {}) {
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
      store.put(activeInfo, KEY_ACTIVE_INFO);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to set active dataset type:", err);
  }
}

/**
 * Clear custom uploaded dataset and reset active selection to master.csv.
 */
export async function clearCustomDataset() {
  try {
    const db = await openDB();
    if (!db) return;
    await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      const store = tx.objectStore(STORE_NAME);
      store.delete(KEY_CUSTOM_DATASET);
      store.put({ type: "master", name: "master.csv", updatedAt: Date.now() }, KEY_ACTIVE_INFO);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  } catch (err) {
    console.warn("Failed to clear custom dataset:", err);
  }
}
