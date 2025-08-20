import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { HEIRIntegration, HEIRValidationResult } from '@/lib/imo/heir-integration';
import { IMOManifest } from '@/lib/imo/types';
import { CheckCircle2, AlertCircle, XCircle, RefreshCw, Activity, Shield } from 'lucide-react';

interface IMOHEIRStatusProps {
  manifest: IMOManifest;
  onEnrichManifest?: (manifest: IMOManifest) => void;
}

export function IMOHEIRStatus({ manifest, onEnrichManifest }: IMOHEIRStatusProps) {
  const [validationResult, setValidationResult] = useState<HEIRValidationResult | null>(null);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const heirIntegration = new HEIRIntegration();

  useEffect(() => {
    fetchRecentEvents();
  }, []);

  const validateManifest = async () => {
    setLoading(true);
    try {
      const result = await heirIntegration.validateManifest(manifest);
      setValidationResult(result);
      
      await heirIntegration.logEvent(
        'imo.validation.completed',
        {
          app_name: manifest.meta.app_name,
          valid: result.valid,
          errors: result.errors.length,
          warnings: result.warnings.length,
        }
      );
      
      fetchRecentEvents();
    } catch (error) {
      console.error('Validation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const enrichWithDoctrine = () => {
    const enrichedManifest = heirIntegration.enrichManifestWithDoctrine(manifest);
    if (onEnrichManifest) {
      onEnrichManifest(enrichedManifest);
    }
    
    heirIntegration.logEvent(
      'imo.doctrine.enriched',
      {
        app_name: enrichedManifest.meta.app_name,
        unique_id: enrichedManifest.doctrine?.unique_id,
        process_id: enrichedManifest.doctrine?.process_id,
      }
    );
  };

  const fetchRecentEvents = async () => {
    try {
      const events = await heirIntegration.getRecentEvents(5);
      setRecentEvents(events);
    } catch (error) {
      console.error('Failed to fetch events:', error);
    }
  };

  const getValidationIcon = () => {
    if (!validationResult) return <AlertCircle className="h-5 w-5 text-gray-400" />;
    if (validationResult.valid) return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };

  const getValidationStatus = () => {
    if (!validationResult) return 'Not Validated';
    if (validationResult.valid) return 'Valid';
    return 'Invalid';
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              HEIR Compliance Status
            </div>
            <Badge variant={validationResult?.valid ? 'default' : 'destructive'}>
              {getValidationStatus()}
            </Badge>
          </CardTitle>
          <CardDescription>
            Hierarchical Error-handling, ID management, and Reporting
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getValidationIcon()}
                <span className="text-sm">
                  {validationResult 
                    ? `${validationResult.errors.length} errors, ${validationResult.warnings.length} warnings`
                    : 'Click validate to check compliance'}
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={enrichWithDoctrine}
                  disabled={!manifest}
                >
                  <Shield className="h-4 w-4 mr-1" />
                  Enrich
                </Button>
                <Button
                  size="sm"
                  onClick={validateManifest}
                  disabled={loading}
                >
                  {loading ? (
                    <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4 mr-1" />
                  )}
                  Validate
                </Button>
              </div>
            </div>

            {validationResult && validationResult.errors.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-red-600">Errors:</h4>
                {validationResult.errors.map((error, idx) => (
                  <div key={idx} className="text-sm text-red-600 pl-4">
                    • {error}
                  </div>
                ))}
              </div>
            )}

            {validationResult && validationResult.warnings.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-yellow-600">Warnings:</h4>
                {validationResult.warnings.map((warning, idx) => (
                  <div key={idx} className="text-sm text-yellow-600 pl-4">
                    • {warning}
                  </div>
                ))}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-4 border-t text-sm">
              <div>
                <span className="text-muted-foreground">Unique ID:</span>
                <p className="font-mono text-xs mt-1">
                  {manifest.doctrine?.unique_id || 'Not generated'}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Process ID:</span>
                <p className="font-mono text-xs mt-1">
                  {manifest.doctrine?.process_id || 'Not generated'}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Blueprint Hash:</span>
                <p className="font-mono text-xs mt-1">
                  {manifest.doctrine?.blueprint_version_hash || 'Not generated'}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">Schema Version:</span>
                <p className="font-mono text-xs mt-1">
                  {manifest.doctrine?.schema_version || 'HEIR/1.0'}
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {recentEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-4 w-4" />
              Recent Events
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentEvents.map((event, idx) => (
                <div key={idx} className="text-xs border-l-2 border-gray-200 pl-3 py-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{event.type}</span>
                    <span className="text-muted-foreground">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {event.payload?.app_name && (
                    <span className="text-muted-foreground">
                      App: {event.payload.app_name}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}