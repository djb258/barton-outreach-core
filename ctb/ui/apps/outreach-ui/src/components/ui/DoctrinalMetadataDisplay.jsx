import React, { useState, useEffect } from 'react';
import Icon from '../AppIcon';

const DoctrinalMetadataDisplay = ({ 
  uniqueId = 'WF-2025-001',
  processId = 'PRC-001', 
  altitude = 'OPERATIONAL',
  timestamp = new Date()?.toISOString(),
  className = '' 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const getAltitudeBadgeColor = (altitude) => {
    switch (altitude) {
      case 'STRATEGIC': return 'bg-primary text-primary-foreground';
      case 'OPERATIONAL': return 'bg-success text-success-foreground';
      case 'TACTICAL': return 'bg-warning text-warning-foreground';
      case 'TECHNICAL': return 'bg-accent text-accent-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getAltitudeIcon = (altitude) => {
    switch (altitude) {
      case 'STRATEGIC': return 'Crown';
      case 'OPERATIONAL': return 'Target';
      case 'TACTICAL': return 'Zap';
      case 'TECHNICAL': return 'Code';
      default: return 'Circle';
    }
  };

  const formatTime = (date) => {
    return date?.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  const formatDate = (date) => {
    return date?.toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  return (
    <div className={`relative flex items-center space-x-3 ${className}`}>
      {/* Unique ID */}
      <div className="flex items-center space-x-2 px-3 py-1.5 bg-muted rounded-md">
        <Icon name="Hash" size={12} color="var(--color-muted-foreground)" />
        <span className="text-xs font-data text-muted-foreground">
          {uniqueId}
        </span>
      </div>

      {/* Process ID */}
      <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 bg-muted rounded-md">
        <Icon name="Workflow" size={12} color="var(--color-muted-foreground)" />
        <span className="text-xs font-data text-muted-foreground">
          {processId}
        </span>
      </div>

      {/* Altitude Badge */}
      <div className={`
        flex items-center space-x-2 px-3 py-1.5 rounded-md text-xs font-medium
        ${getAltitudeBadgeColor(altitude)}
      `}>
        <Icon name={getAltitudeIcon(altitude)} size={12} />
        <span>{altitude}</span>
      </div>

      {/* Current Time Display */}
      <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 bg-card border border-border rounded-md">
        <Icon name="Clock" size={12} color="var(--color-muted-foreground)" />
        <span className="text-xs font-data text-muted-foreground">
          {formatTime(currentTime)}
        </span>
      </div>

      {/* Expand Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-1.5 rounded-md hover:bg-muted transition-colors duration-200"
        aria-label={isExpanded ? 'Collapse metadata details' : 'Expand metadata details'}
      >
        <Icon 
          name="Info" 
          size={14} 
          color="var(--color-muted-foreground)" 
        />
      </button>

      {/* Expanded Metadata Panel */}
      {isExpanded && (
        <div className="absolute top-full left-0 mt-2 w-72 bg-card border border-border rounded-lg shadow-modal z-[1010] animate-slide-in">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-foreground">Doctrinal Metadata</h3>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1 rounded-md hover:bg-muted transition-colors duration-200"
              >
                <Icon name="X" size={14} color="var(--color-muted-foreground)" />
              </button>
            </div>

            <div className="space-y-3">
              {/* Unique Identifier */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Unique ID:</span>
                <span className="text-xs font-data text-foreground">{uniqueId}</span>
              </div>

              {/* Process Identifier */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Process ID:</span>
                <span className="text-xs font-data text-foreground">{processId}</span>
              </div>

              {/* Altitude Level */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Altitude:</span>
                <div className={`
                  flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium
                  ${getAltitudeBadgeColor(altitude)}
                `}>
                  <Icon name={getAltitudeIcon(altitude)} size={10} />
                  <span>{altitude}</span>
                </div>
              </div>

              {/* Timestamp */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Created:</span>
                <span className="text-xs font-data text-foreground">
                  {formatDate(new Date(timestamp))}
                </span>
              </div>

              {/* Current Session Time */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Current Time:</span>
                <span className="text-xs font-data text-foreground">
                  {formatTime(currentTime)}
                </span>
              </div>

              {/* Session Duration */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Session:</span>
                <span className="text-xs font-data text-success">
                  Active
                </span>
              </div>
            </div>

            {/* Doctrine Information */}
            <div className="mt-4 pt-3 border-t border-border">
              <div className="flex items-start space-x-2">
                <Icon name="BookOpen" size={12} color="var(--color-muted-foreground)" />
                <div className="flex-1">
                  <div className="text-xs font-medium text-foreground mb-1">
                    IMO Doctrine Pattern
                  </div>
                  <div className="text-xs text-muted-foreground leading-relaxed">
                    Enterprise workflow automation following structured data processing pipeline with role-based access control.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctrinalMetadataDisplay;