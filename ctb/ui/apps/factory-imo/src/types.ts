/**
 * Barton Doctrine Types - Process Tracking & Altitude Management
 */

export type Step = {
  unique_id: string
  process_id: string
  altitude: number
  tool_id?: string
  table_reference?: string
}

export type PhaseGroupProps = {
  altitude: number
  title: string
  steps: Step[]
}

export type StepCardProps = {
  process_id: string
  unique_id: string
  tool_id?: string
  table_reference?: string
  onClick?: () => void
}

export type StepModalProps = {
  step: Step
  onClose: () => void
}

export type AltitudeLevel = 30000 | 20000 | 10000

export const ALTITUDE_CONFIG = {
  30000: { label: 'Vision', color: 'red', bgColor: 'bg-red-100', textColor: 'text-red-800', borderColor: 'border-red-300' },
  20000: { label: 'Category', color: 'yellow', bgColor: 'bg-yellow-100', textColor: 'text-yellow-800', borderColor: 'border-yellow-300' },
  10000: { label: 'Execution', color: 'green', bgColor: 'bg-green-100', textColor: 'text-green-800', borderColor: 'border-green-300' }
} as const