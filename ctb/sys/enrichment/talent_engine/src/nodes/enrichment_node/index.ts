/**
 * Enrichment Node
 * ===============
 * UTILITY NODE for external data enrichment adapters
 *
 * Provides vendor-agnostic adapters for all external services.
 * Not a processing node - serves as adapter layer for other nodes.
 *
 * Re-exports from adapters directory for convenience.
 */

// Re-export all adapters
export * from "../../adapters";

/**
 * Adapter Categories:
 *
 * Company Lookup:
 * - externalCompanyLookupAdapter
 *
 * LinkedIn:
 * - linkedInResolverAdapter
 * - linkedInProfileAdapter
 * - linkedInAccessibilityAdapter
 *
 * Email:
 * - emailPatternAdapter
 * - emailFinderAdapter
 * - emailVerificationAdapter
 *
 * Person:
 * - personEmploymentLookupAdapter
 * - slotDiscoveryAdapter
 *
 * All adapters support:
 * - mock_mode for testing
 * - timeout configuration
 * - retry logic
 * - cost tracking
 */
