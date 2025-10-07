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
