import { useEffect, useState } from "react"
import type { Step } from "../types"

type FetchOptions = {
  microprocess_id?: string
  blueprint_id?: string
}

/**
 * Custom hook for fetching Doctrine-compliant process steps from MCP server
 * Enforces Barton ID validation and integrates with Composio MCP
 */
export function useDoctrineSteps({ microprocess_id, blueprint_id }: FetchOptions) {
  const [steps, setSteps] = useState<Step[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSteps() {
      setLoading(true)
      setError(null)

      try {
        // Use environment variable for MCP endpoint or fallback to localhost
        const mcpEndpoint = import.meta.env.VITE_MCP_ENDPOINT || 'http://localhost:3001'

        const res = await fetch(
          `${mcpEndpoint}/doctrine/steps`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Composio-Api-Key": import.meta.env.VITE_COMPOSIO_API_KEY || "ak_t-F0AbvfZHUZSUrqAGNn"
            },
            body: JSON.stringify({
              microprocess_id,
              blueprint_id,
              // Add Barton Doctrine metadata
              metadata: {
                unique_id: `DOCTRINE-FETCH-${Date.now()}`,
                process_id: 'doctrine-steps-fetch',
                orbt_layer: 10000,
                timestamp: new Date().toISOString()
              }
            }),
          }
        )

        if (!res.ok) {
          throw new Error(`MCP fetch failed: HTTP ${res.status} - ${res.statusText}`)
        }

        const data = await res.json()

        // Enforce Barton Doctrine ID compliance with multiple patterns
        const validSteps = (data.steps || []).filter((s: Step) => {
          // Standard Barton ID pattern: XX.XX.XX.XX.XXXXX.XXX
          const standardPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d{3}$/
          // Extended pattern: XX.XX.XX.XX.XXXXX.XXX.XXX.XXXX
          const extendedPattern = /^\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{5}\.\d+\.\d+\.[A-Z0-9]+$/
          // Short prefixed pattern: CMP-, PER-, AUDIT-, etc.
          const shortPattern = /^(CMP|PER|CNT|AUDIT|NEON|HIST|DOCTRINE)-/

          return standardPattern.test(s.unique_id) ||
                 extendedPattern.test(s.unique_id) ||
                 shortPattern.test(s.unique_id)
        })

        // Sort by altitude (descending) then by sequence
        const sortedSteps = validSteps.sort((a, b) => {
          if (a.altitude !== b.altitude) {
            return b.altitude - a.altitude // Vision > Category > Execution
          }
          return a.unique_id.localeCompare(b.unique_id)
        })

        setSteps(sortedSteps)

        // Log successful fetch for audit purposes
        console.log(`✅ Fetched ${sortedSteps.length} valid Doctrine steps`, {
          microprocess_id,
          blueprint_id,
          total_fetched: data.steps?.length || 0,
          valid_count: sortedSteps.length
        })

      } catch (err: any) {
        const errorMessage = err.message || 'Unknown error fetching doctrine steps'
        setError(errorMessage)

        // Log error for debugging
        console.error('❌ Doctrine steps fetch failed:', {
          error: errorMessage,
          microprocess_id,
          blueprint_id,
          endpoint: import.meta.env.VITE_MCP_ENDPOINT || 'http://localhost:3001'
        })
      } finally {
        setLoading(false)
      }
    }

    fetchSteps()
  }, [microprocess_id, blueprint_id])

  // Helper functions for component use
  const stepsByAltitude = (altitude: number) =>
    steps.filter(step => step.altitude === altitude)

  const totalSteps = steps.length

  const hasStepsAtAltitude = (altitude: number) =>
    steps.some(step => step.altitude === altitude)

  return {
    steps,
    loading,
    error,
    stepsByAltitude,
    totalSteps,
    hasStepsAtAltitude
  }
}