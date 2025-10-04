import React, { useState } from 'react';
import { StepCardProps } from '../../types';
import StepModal from './StepModal';

/**
 * StepCard - Individual process step display with Barton ID compliance
 * Clickable card that opens detailed view in modal
 */
const StepCard: React.FC<StepCardProps> = ({
  process_id,
  unique_id,
  tool_id,
  table_reference,
  onClick
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCardClick = () => {
    if (onClick) {
      onClick();
    } else {
      setIsModalOpen(true);
    }
  };

  const stepData = {
    unique_id,
    process_id,
    altitude: parseInt(unique_id.split('.')[4]) || 10000, // Extract altitude from Barton ID
    tool_id,
    table_reference
  };

  return (
    <>
      <div
        onClick={handleCardClick}
        className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all duration-200 transform hover:scale-[1.02]"
      >
        {/* Card Header */}
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 leading-tight">
            {process_id}
          </h3>
          {(tool_id || table_reference) && (
            <div className="flex flex-col space-y-1 ml-2">
              {tool_id && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  T:{tool_id}
                </span>
              )}
              {table_reference && (
                <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                  DB
                </span>
              )}
            </div>
          )}
        </div>

        {/* Barton ID Display */}
        <div className="mb-3">
          <span className="text-xs text-gray-500 block mb-1">Barton ID</span>
          <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono text-gray-700 break-all">
            {unique_id}
          </code>
        </div>

        {/* Table Reference (if present) */}
        {table_reference && (
          <div className="mb-2">
            <span className="text-xs text-gray-500 block mb-1">Table</span>
            <code className="text-xs bg-yellow-50 text-yellow-700 px-2 py-1 rounded font-mono">
              {table_reference}
            </code>
          </div>
        )}

        {/* Status Indicator */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs text-gray-600">Active</span>
          </div>
          <span className="text-xs text-gray-400 hover:text-blue-600">
            Click for details →
          </span>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <StepModal
          step={stepData}
          onClose={() => setIsModalOpen(false)}
        />
      )}
    </>
  );
};

export default StepCard;