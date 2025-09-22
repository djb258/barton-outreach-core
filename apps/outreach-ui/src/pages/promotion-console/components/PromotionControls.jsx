import React from 'react';
import Button from '../../../components/ui/Button';
import Icon from '../../../components/AppIcon';

const PromotionControls = ({ 
  onPromote, 
  onDownload, 
  onBack, 
  isLoading = false,
  canDownload = false,
  className = ''
}) => {
  return (
    <div className={`bg-card border border-border rounded-lg p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Promotion Actions</h3>
          <p className="text-sm text-muted-foreground">
            Manage record promotion and audit trail downloads
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-4">
        {/* Primary Action: Promote Records */}
        <Button
          onClick={onPromote}
          disabled={isLoading}
          loading={isLoading}
          iconName="Send"
          iconPosition="left"
          variant="default"
          size="lg"
          className="bg-primary hover:bg-primary/90 text-primary-foreground"
        >
          {isLoading ? 'Processing...' : 'Promote Valid Records'}
        </Button>

        {/* Download Audit Log */}
        <Button
          onClick={onDownload}
          disabled={!canDownload}
          iconName="Download"
          iconPosition="left"
          variant="outline"
          size="lg"
        >
          Download Audit Log
        </Button>

        {/* Navigation Back */}
        <Button
          onClick={onBack}
          iconName="ArrowLeft"
          iconPosition="left"
          variant="secondary"
          size="lg"
        >
          Back to Adjuster (Step 3)
        </Button>
      </div>

      {/* Help Text */}
      <div className="mt-6 p-4 bg-muted/50 rounded-lg">
        <div className="flex items-start space-x-3">
          <Icon name="Info" size={16} className="text-info mt-0.5 shrink-0" />
          <div className="text-sm text-muted-foreground">
            <p className="font-medium mb-1">Promotion Process:</p>
            <ul className="space-y-1 text-xs">
              <li>• <strong>Promote Valid Records:</strong> Executes batch promotion of validated company records</li>
              <li>• <strong>Download Audit Log:</strong> Downloads detailed promotion history for compliance tracking</li>
              <li>• <strong>Back to Adjuster:</strong> Return to Step 3 for additional data adjustments</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-warning animate-pulse' : 'bg-success'}`} />
            <span>System Status: {isLoading ? 'Processing' : 'Ready'}</span>
          </span>
        </div>
        
        <div className="flex items-center space-x-1">
          <Icon name="Shield" size={12} className="text-muted-foreground" />
          <span>Execution Layer • High Priority</span>
        </div>
      </div>
    </div>
  );
};

export default PromotionControls;