/**
 * API Cache Service
 * -----------------
 * Caches API responses in localStorage with a configurable TTL (default: 1 day).
 * Keys are prefixed with "apicache_" to avoid collisions with other localStorage data.
 *
 * Usage:
 *   ApiCache.get(key)           → returns parsed value or null if expired/missing
 *   ApiCache.set(key, value)    → stores value with expiry timestamp
 *   ApiCache.invalidate(key)    → removes a specific entry
 *   ApiCache.clear()            → removes all apicache_ entries
 *   ApiCache.makeKey(...)       → creates a stable key from args
 */

const PREFIX = 'apicache_';
const ONE_DAY_MS = 24 * 60 * 60 * 1000;

const ApiCache = {
    /**
     * Create a stable cache key from any number of string/object arguments.
     * Objects are serialised deterministically by sorting their keys first.
     */
    makeKey(...parts) {
        const serialised = parts
            .map(p => (typeof p === 'object' && p !== null ? JSON.stringify(this._sortedObject(p)) : String(p)))
            .join('|');
        return PREFIX + serialised;
    },

    /** Retrieve a cached value. Returns null if missing or expired. */
    get(key) {
        try {
            const raw = localStorage.getItem(key);
            if (!raw) return null;
            const { value, expiresAt } = JSON.parse(raw);
            if (Date.now() > expiresAt) {
                localStorage.removeItem(key);
                return null;
            }
            return value;
        } catch {
            return null;
        }
    },

    /** Store a value under key with a TTL of ttlMs milliseconds (default 1 day). */
    set(key, value, ttlMs = ONE_DAY_MS) {
        try {
            const entry = { value, expiresAt: Date.now() + ttlMs };
            localStorage.setItem(key, JSON.stringify(entry));
        } catch (e) {
            // Quota exceeded or private mode – silently skip
            console.warn('[ApiCache] Could not write to localStorage:', e.message);
        }
    },

    /** Remove a specific cache entry. */
    invalidate(key) {
        localStorage.removeItem(key);
    },

    /** Remove all cache entries created by this service. */
    clear() {
        const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX));
        keys.forEach(k => localStorage.removeItem(k));
        console.log(`[ApiCache] Cleared ${keys.length} entries.`);
    },

    /** Remove all entries that are past their expiresAt timestamp. */
    pruneExpired() {
        const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX));
        let pruned = 0;
        keys.forEach(k => {
            try {
                const { expiresAt } = JSON.parse(localStorage.getItem(k));
                if (Date.now() > expiresAt) {
                    localStorage.removeItem(k);
                    pruned++;
                }
            } catch {
                localStorage.removeItem(k); // corrupt entry – remove
                pruned++;
            }
        });
        if (pruned > 0) console.log(`[ApiCache] Pruned ${pruned} expired entries.`);
    },

    // ── internals ────────────────────────────────────────────────────────────────

    /** Deep-sort object keys so the same filters always produce the same JSON. */
    _sortedObject(obj) {
        if (typeof obj !== 'object' || obj === null) return obj;
        if (Array.isArray(obj)) return obj.map(v => this._sortedObject(v));
        return Object.keys(obj)
            .sort()
            .reduce((acc, k) => ({ ...acc, [k]: this._sortedObject(obj[k]) }), {});
    },
};

export default ApiCache;
