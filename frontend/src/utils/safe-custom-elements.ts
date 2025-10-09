/**
 * Safe Custom Elements Utility
 *
 * Provides defensive registration for custom elements to prevent
 * "already defined" errors when scripts load multiple times or
 * when external scripts (like Webflow) define the same elements.
 *
 * @module safe-custom-elements
 */

/**
 * Safely define a custom element, ignoring errors if already defined.
 * Prevents "already defined" errors when scripts load multiple times.
 *
 * This is particularly useful when:
 * - The app is embedded in an iframe within a page that also loads the same components
 * - External scripts (e.g., Webflow, TinyMCE) define web components
 * - There's a race condition between multiple script loads
 *
 * @param name - The custom element tag name (e.g., 'mce-autosize-textarea')
 * @param constructor - The custom element constructor class
 * @param options - Optional element definition options (e.g., { extends: 'div' })
 *
 * @example
 * ```typescript
 * import { safeDefineElement } from './utils/safe-custom-elements';
 *
 * class MyElement extends HTMLElement {
 *   connectedCallback() {
 *     this.textContent = 'Hello!';
 *   }
 * }
 *
 * // Safe registration - won't throw if already defined
 * safeDefineElement('my-element', MyElement);
 * ```
 */
export function safeDefineElement(
  name: string,
  constructor: CustomElementConstructor,
  options?: ElementDefinitionOptions
): void {
  // Check if element is already defined
  if (customElements.get(name)) {
    console.warn(
      `Custom element '${name}' already defined, skipping re-registration. ` +
      `This is normal when the app is embedded in a page with external scripts.`
    );
    return;
  }

  try {
    // Attempt to define the element
    customElements.define(name, constructor, options);
    console.debug(`Custom element '${name}' registered successfully`);
  } catch (error) {
    // Handle race condition where element was defined between check and define
    if (error instanceof DOMException && error.name === 'NotSupportedError') {
      console.warn(
        `Custom element '${name}' was defined concurrently (race condition), ignoring. ` +
        `The first definition will be used.`
      );
    } else {
      // Unexpected error - re-throw to surface the issue
      console.error(`Failed to define custom element '${name}':`, error);
      throw error;
    }
  }
}

/**
 * Check if a custom element is already defined
 *
 * @param name - The custom element tag name to check
 * @returns True if the element is defined, false otherwise
 *
 * @example
 * ```typescript
 * if (isElementDefined('my-element')) {
 *   console.log('my-element is already registered');
 * }
 * ```
 */
export function isElementDefined(name: string): boolean {
  return customElements.get(name) !== undefined;
}

/**
 * Get all defined custom element names
 *
 * Note: This returns an empty array as there's no standard API to enumerate
 * all custom elements. It's provided for future compatibility if browsers
 * add this capability.
 *
 * @returns Array of custom element tag names (currently always empty)
 */
export function getDefinedElements(): string[] {
  // Unfortunately, there's no standard way to enumerate all custom elements
  // This is a placeholder for future browser support
  console.warn(
    'getDefinedElements() cannot enumerate custom elements - ' +
    'no standard browser API exists for this operation'
  );
  return [];
}
