// idb-mock.js — tiny in-memory IndexedDB shim, used only by tests.
// happy-dom's IDB is incomplete and silently swallows writes; this shim
// covers what datasetStorage.js exercises (openDB, getStore with put/get/delete
// inside readwrite/readonly transactions).
//
// Only implements what we need: single object store, sync transactions
// resolved via the standard { oncomplete, onerror, onsuccess } hooks.

class FakeIDBRequest {
  constructor() {
    this.onsuccess = null;
    this.onerror = null;
    this.result = undefined;
    this.error = null;
  }
}

class FakeIDBObjectStore {
  constructor(name) {
    this.name = name;
    this.data = new Map();
  }
  put(value, key) {
    this.data.set(key, value);
    const req = new FakeIDBRequest();
    req.result = key;
    queueMicrotask(() => req.onsuccess?.(null));
    return req;
  }
  get(key) {
    const req = new FakeIDBRequest();
    req.result = this.data.has(key) ? this.data.get(key) : undefined;
    queueMicrotask(() => req.onsuccess?.(null));
    return req;
  }
  delete(key) {
    this.data.delete(key);
    const req = new FakeIDBRequest();
    queueMicrotask(() => req.onsuccess?.(null));
    return req;
  }
}

class FakeIDBTransaction {
  constructor(store) {
    this.store = store;
    this.oncomplete = null;
    this.onerror = null;
    // Resolve on the next tick — mimics the real IDB tx.oncomplete timing
    // closely enough for the datasetStorage call sites.
    queueMicrotask(() => this.oncomplete?.(null));
  }
  objectStore(_name) {
    return this.store;
  }
}

class FakeIDBDatabase {
  constructor() {
    this._store = new FakeIDBObjectStore("datasets");
  }
  transaction(_name, _mode) {
    return new FakeIDBTransaction(this._store);
  }
  objectStore(_name) {
    return this._store;
  }
}

class FakeIDBOpenRequest extends FakeIDBRequest {
  constructor() {
    super();
    this.onupgradeneeded = null;
  }
}

export function installIdbMock() {
  // Reuse a single FakeIDBDatabase across opens — each call to
  // indexedDB.open() would otherwise create a fresh in-memory store and
  // writes from one call would never be visible to the next.
  const sharedDb = new FakeIDBDatabase();
  const fakeOpen = (_name, _version) => {
    const req = new FakeIDBOpenRequest();
    queueMicrotask(() => {
      req.result = sharedDb;
      req.onsuccess?.(null);
    });
    return req;
  };
  // datasetStorage.js probes `window.indexedDB` (not globalThis), so we
  // need to install on both — happy-dom leaves window.indexedDB undefined.
  globalThis.indexedDB = { open: fakeOpen };
  if (typeof window !== "undefined") window.indexedDB = globalThis.indexedDB;
}