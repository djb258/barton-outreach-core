import React from 'react';
import { PhaseGroupProps, ALTITUDE_CONFIG, AltitudeLevel } from '../../types';
import StepCard from './StepCard';

/**
 * PhaseGroup - Groups steps by altitude level (Vision/Category/Execution)
 * Enforces Barton Doctrine visual hierarchy and process organization
 */
const PhaseGroup: React.FC<PhaseGroupProps> = ({ altitude, title, steps }) => {
  const config = ALTITUDE_CONFIG[altitude as AltitudeLevel];

  if (!config) {
    console.warn(`Unknown altitude level: ${altitude}`);
    return null;
  }

  return (
    <div className={`rounded-lg border-2 ${config.borderColor} ${config.bgColor} p-6 mb-6`}>
      {/* Phase Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor} border ${config.borderColor}`}>
            {config.label}
          </span>
          <span className="text-sm text-gray-600 font-mono">
            ALT: {altitude.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Steps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {steps.map((step) => (
          <StepCard
            key={step.unique_id}
            process_id={step.process_id}
            unique_id={step.unique_id}
            tool_id={step.tool_id}
            table_reference={step.table_reference}
          />
        ))}
      </div>

      {/* Phase Summary */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>{steps.length} process{steps.length !== 1 ? 'es' : ''} at {config.label} level</span>
          <span className="font-mono">Phase: {altitude}</span>
        </div>
      </div>
    </div>
  );
};

export default PhaseGroup;