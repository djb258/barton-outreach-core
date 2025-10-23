import React, { useEffect, useRef } from 'react';
import { StepModalProps, ALTITUDE_CONFIG, AltitudeLevel } from '../../types';

/**
 * StepModal - Detailed view of a process step with Barton Doctrine compliance info
 * Accessible modal with focus trapping and ESC key handling
 */
const StepModal: React.FC<StepModalProps> = ({ step, onClose }) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const firstFocusableRef = useRef<HTMLButtonElement>(null);

  const config = ALTITUDE_CONFIG[step.altitude as AltitudeLevel];

  useEffect(() => {
    // Focus first element when modal opens
    if (firstFocusableRef.current) {
      firstFocusableRef.current.focus();
    }

    // Handle ESC key
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    // Handle click outside
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscKey);
    document.addEventListener('mousedown', handleClickOutside);

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleEscKey);
      document.removeEventListener('mousedown', handleClickOutside);
      document.body.style.overflow = 'unset';
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
      <div
        ref={modalRef}
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Modal Header */}
        <div className={`${config?.bgColor || 'bg-gray-100'} px-6 py-4 border-b border-gray-200`}>
          <div className="flex items-center justify-between">
            <h2 id="modal-title" className="text-lg font-bold text-gray-900">
              Process Step Details
            </h2>
            <button
              ref={firstFocusableRef}
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close modal"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="px-6 py-4 space-y-6">
          {/* Process Information */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">{step.process_id}</h3>

            {/* Altitude Badge */}
            {config && (
              <div className="mb-4">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.textColor} border ${config.borderColor}`}>
                  {config.label} Level (ALT: {step.altitude.toLocaleString()})
                </span>
              </div>
            )}
          </div>

          {/* Barton ID Details */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Barton ID Compliance</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Unique ID:</span>
                <code className="text-sm bg-white px-2 py-1 rounded border">{step.unique_id}</code>
              </div>
              <div className="text-xs text-gray-500">
                Format: XX.XX.XX.XX.ALTITUDE.SEQUENCE
              </div>
            </div>
          </div>

          {/* Technical Details */}
          <div className="space-y-4">
            {step.tool_id && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">Tool Integration</h4>
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    Tool ID: {step.tool_id}
                  </span>
                  <span className="text-sm text-blue-700">MCP-enabled process</span>
                </div>
              </div>
            )}

            {step.table_reference && (
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-green-900 mb-2">Database Reference</h4>
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                    Table: {step.table_reference}
                  </span>
                  <span className="text-sm text-green-700">Neon integration via MCP</span>
                </div>
              </div>
            )}
          </div>

          {/* Doctrine Text Placeholder */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-yellow-900 mb-2">Barton Doctrine Compliance</h4>
            <p className="text-sm text-yellow-800 mb-2">
              This process step adheres to Barton Doctrine standards for:
            </p>
            <ul className="text-sm text-yellow-700 space-y-1 list-disc list-inside">
              <li>Unique ID formatting and altitude-based organization</li>
              <li>MCP-first execution through Composio integration</li>
              <li>Process reference validation against shq_process_key_reference</li>
              <li>Audit logging and compliance tracking</li>
            </ul>
            <div className="mt-3 text-xs text-yellow-600 bg-yellow-100 p-2 rounded">
              📝 Builder.io Editor Note: This section can be customized with specific doctrine requirements for each process type.
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Close
          </button>
          <button
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            onClick={() => {
              // Placeholder for edit action in Builder.io
              console.log('Edit process in Builder.io:', step.unique_id);
            }}
          >
            Edit in Builder.io
          </button>
        </div>
      </div>
    </div>
  );
};

export default StepModal;