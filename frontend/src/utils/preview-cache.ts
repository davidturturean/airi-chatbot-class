/**
 * Preview Cache Manager
 * Session-scoped caching for document previews with aggressive caching strategy
 * Performance target: <200ms preview load from cache
 */

import type { CacheEntry, DocumentPreview, ExcelDocumentData, WordDocumentData, CitationGalleryData } from '../types/document-preview';

class PreviewCacheManager {
  private previews = new Map<string, CacheEntry<DocumentPreview>>();
  private excelData = new Map<string, CacheEntry<ExcelDocumentData>>();
  private wordData = new Map<string, CacheEntry<WordDocumentData>>();
  private gallery = new Map<string, CacheEntry<CitationGalleryData>>();

  // Track in-flight requests to prevent duplicate prefetches
  private inFlightExcelRequests = new Map<string, Promise<ExcelDocumentData | null>>();
  private inFlightWordRequests = new Map<string, Promise<WordDocumentData | null>>();

  private sessionId: string | null = null;
  private readonly defaultExpiry = 30 * 60 * 1000; // 30 minutes

  setSessionId(sessionId: string) {
    if (this.sessionId !== sessionId) {
      // Clear all caches when session changes
      this.clearAll();
      this.sessionId = sessionId;
    }
  }

  private getCacheKey(rid: string): string {
    return `${this.sessionId}-${rid}`;
  }

  // Preview Cache
  getPreview(rid: string): DocumentPreview | null {
    const key = this.getCacheKey(rid);
    const entry = this.previews.get(key);

    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.previews.delete(key);
      return null;
    }

    return entry.data;
  }

  setPreview(rid: string, data: DocumentPreview, expiry?: number): void {
    const key = this.getCacheKey(rid);
    this.previews.set(key, {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + (expiry || this.defaultExpiry)
    });
  }

  // Excel Data Cache
  getExcelData(rid: string): ExcelDocumentData | null {
    const key = this.getCacheKey(rid);
    const entry = this.excelData.get(key);

    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.excelData.delete(key);
      return null;
    }

    return entry.data;
  }

  setExcelData(rid: string, data: ExcelDocumentData, expiry?: number): void {
    const key = this.getCacheKey(rid);
    this.excelData.set(key, {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + (expiry || this.defaultExpiry)
    });
  }

  /**
   * Prefetch Excel data in the background (non-blocking).
   * Prevents duplicate requests for the same RID.
   * Use when hover preview detects Excel type to pre-load data before user clicks.
   */
  async prefetchExcelData(rid: string): Promise<ExcelDocumentData | null> {
    if (!this.sessionId) {
      console.warn('Cannot prefetch Excel data: session ID not set');
      return null;
    }

    const key = this.getCacheKey(rid);

    // Check if already cached
    const cached = this.getExcelData(rid);
    if (cached) {
      console.log(`Excel data already cached for ${rid}, skipping prefetch`);
      return cached;
    }

    // Check if request already in flight
    const inFlight = this.inFlightExcelRequests.get(key);
    if (inFlight) {
      console.log(`Excel prefetch already in progress for ${rid}, reusing promise`);
      return inFlight;
    }

    // Start new prefetch request
    const startTime = performance.now();
    console.log(`Starting Excel prefetch for ${rid}...`);

    const fetchPromise = (async () => {
      try {
        // Prefetch WITHOUT formatting for maximum speed (formatting is optional enhancement)
        const response = await fetch(`/api/document/${rid}/excel?session_id=${this.sessionId}&include_formatting=false`);

        if (!response.ok) {
          throw new Error(`Failed to prefetch Excel data: ${response.statusText}`);
        }

        const data = await response.json();

        // Enhance with source_location from preview cache if available
        const preview = this.getPreview(rid);
        if (preview && preview.source_location) {
          data.source_location = preview.source_location;
        }

        // Store in cache
        this.setExcelData(rid, data);

        const duration = performance.now() - startTime;
        console.log(`Excel prefetch completed for ${rid} in ${duration.toFixed(2)}ms`);

        return data;
      } catch (error) {
        console.warn(`Excel prefetch failed for ${rid}:`, error);
        return null;
      } finally {
        // Clean up in-flight tracking
        this.inFlightExcelRequests.delete(key);
      }
    })();

    // Track in-flight request
    this.inFlightExcelRequests.set(key, fetchPromise);

    return fetchPromise;
  }

  // Word Data Cache
  getWordData(rid: string): WordDocumentData | null {
    const key = this.getCacheKey(rid);
    const entry = this.wordData.get(key);

    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.wordData.delete(key);
      return null;
    }

    return entry.data;
  }

  setWordData(rid: string, data: WordDocumentData, expiry?: number): void {
    const key = this.getCacheKey(rid);
    this.wordData.set(key, {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + (expiry || this.defaultExpiry)
    });
  }

  /**
   * Prefetch Word data in the background (non-blocking).
   * Prevents duplicate requests for the same RID.
   * Use when hover preview detects Word type to pre-load data before user clicks.
   */
  async prefetchWordData(rid: string): Promise<WordDocumentData | null> {
    if (!this.sessionId) {
      console.warn('Cannot prefetch Word data: session ID not set');
      return null;
    }

    const key = this.getCacheKey(rid);

    // Check if already cached
    const cached = this.getWordData(rid);
    if (cached) {
      console.log(`Word data already cached for ${rid}, skipping prefetch`);
      return cached;
    }

    // Check if request already in flight
    const inFlight = this.inFlightWordRequests.get(key);
    if (inFlight) {
      console.log(`Word prefetch already in progress for ${rid}, reusing promise`);
      return inFlight;
    }

    // Start new prefetch request
    const startTime = performance.now();
    console.log(`Starting Word prefetch for ${rid}...`);

    const fetchPromise = (async () => {
      try {
        const response = await fetch(`/api/document/${rid}/word?session_id=${this.sessionId}`);

        if (!response.ok) {
          throw new Error(`Failed to prefetch Word data: ${response.statusText}`);
        }

        const data = await response.json();

        // Store in cache
        this.setWordData(rid, data);

        const duration = performance.now() - startTime;
        console.log(`Word prefetch completed for ${rid} in ${duration.toFixed(2)}ms`);

        return data;
      } catch (error) {
        console.warn(`Word prefetch failed for ${rid}:`, error);
        return null;
      } finally {
        // Clean up in-flight tracking
        this.inFlightWordRequests.delete(key);
      }
    })();

    // Track in-flight request
    this.inFlightWordRequests.set(key, fetchPromise);

    return fetchPromise;
  }

  // Gallery Cache
  getGallery(sessionId: string): CitationGalleryData | null {
    const key = `gallery-${sessionId}`;
    const entry = this.gallery.get(key);

    if (!entry) return null;

    if (Date.now() > entry.expiry) {
      this.gallery.delete(key);
      return null;
    }

    return entry.data;
  }

  setGallery(sessionId: string, data: CitationGalleryData, expiry?: number): void {
    const key = `gallery-${sessionId}`;
    this.gallery.set(key, {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + (expiry || this.defaultExpiry)
    });
  }

  // Cache Management
  clearPreview(rid: string): void {
    const key = this.getCacheKey(rid);
    this.previews.delete(key);
  }

  clearAll(): void {
    this.previews.clear();
    this.excelData.clear();
    this.wordData.clear();
    this.gallery.clear();
    this.inFlightExcelRequests.clear();
    this.inFlightWordRequests.clear();
  }

  // Performance Metrics
  getCacheStats() {
    return {
      previewCount: this.previews.size,
      excelCount: this.excelData.size,
      wordCount: this.wordData.size,
      galleryCount: this.gallery.size,
      totalSize: this.previews.size + this.excelData.size + this.wordData.size + this.gallery.size
    };
  }

  // Cleanup expired entries
  cleanup(): void {
    const now = Date.now();

    for (const [key, entry] of this.previews.entries()) {
      if (now > entry.expiry) {
        this.previews.delete(key);
      }
    }

    for (const [key, entry] of this.excelData.entries()) {
      if (now > entry.expiry) {
        this.excelData.delete(key);
      }
    }

    for (const [key, entry] of this.wordData.entries()) {
      if (now > entry.expiry) {
        this.wordData.delete(key);
      }
    }

    for (const [key, entry] of this.gallery.entries()) {
      if (now > entry.expiry) {
        this.gallery.delete(key);
      }
    }
  }
}

// Singleton instance
export const previewCache = new PreviewCacheManager();

// Auto cleanup every 5 minutes
setInterval(() => {
  previewCache.cleanup();
}, 5 * 60 * 1000);
