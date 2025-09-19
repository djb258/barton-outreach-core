import React, { useState, useCallback } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';

const FileUploadZone = ({ onFileSelect, isProcessing }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDragOver = useCallback((e) => {
    e?.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e?.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e?.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e?.dataTransfer?.files);
    const csvFile = files?.find(file => file?.type === 'text/csv' || file?.name?.endsWith('.csv'));
    
    if (csvFile) {
      if (csvFile?.size > 50 * 1024 * 1024) { // 50MB limit
        alert('File size exceeds 50MB limit. Please upload a smaller file.');
        return;
      }
      onFileSelect(csvFile);
    } else {
      alert('Please upload a CSV file only.');
    }
  }, [onFileSelect]);

  const handleFileInput = useCallback((e) => {
    const file = e?.target?.files?.[0];
    if (file) {
      if (file?.size > 50 * 1024 * 1024) {
        alert('File size exceeds 50MB limit. Please upload a smaller file.');
        return;
      }
      onFileSelect(file);
    }
  }, [onFileSelect]);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i))?.toFixed(2)) + ' ' + sizes?.[i];
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
          ${isDragOver 
            ? 'border-accent bg-accent/5 scale-[1.02]' 
            : 'border-border bg-card hover:border-accent/50 hover:bg-accent/2'
          }
          ${isProcessing ? 'pointer-events-none opacity-60' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {/* Upload Icon */}
        <div className={`
          flex items-center justify-center w-16 h-16 mx-auto mb-4 rounded-full
          ${isDragOver ? 'bg-accent text-accent-foreground' : 'bg-muted text-muted-foreground'}
          transition-all duration-200
        `}>
          <Icon name="Upload" size={24} />
        </div>

        {/* Upload Text */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-foreground mb-2">
            {isDragOver ? 'Drop your CSV file here' : 'Upload Company Data'}
          </h3>
          <p className="text-sm text-muted-foreground mb-2">
            Drag and drop your CSV file here, or click to browse
          </p>
          <p className="text-xs text-muted-foreground">
            Maximum file size: 50MB • Supported format: CSV
          </p>
        </div>

        {/* File Input */}
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={isProcessing}
          id="file-upload"
        />

        {/* Upload Button */}
        <Button
          variant="outline"
          iconName="FolderOpen"
          iconPosition="left"
          disabled={isProcessing}
          className="pointer-events-none"
        >
          Choose File
        </Button>

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="absolute inset-0 flex items-center justify-center bg-card/80 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              <span className="text-sm font-medium text-foreground">Processing...</span>
            </div>
          </div>
        )}
      </div>

      {/* Upload Guidelines */}
      <div className="mt-6 p-4 bg-muted/50 rounded-lg">
        <div className="flex items-start space-x-3">
          <Icon name="Info" size={16} color="var(--color-muted-foreground)" />
          <div className="flex-1">
            <h4 className="text-sm font-medium text-foreground mb-2">Upload Guidelines</h4>
            <ul className="text-xs text-muted-foreground space-y-1">
              <li>• CSV files with company prospect data</li>
              <li>• Required columns: company_name, email, phone (optional)</li>
              <li>• Maximum 10,000 rows per upload</li>
              <li>• UTF-8 encoding recommended</li>
              <li>• First row should contain column headers</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Keyboard Shortcuts */}
      <div className="mt-4 text-center">
        <p className="text-xs text-muted-foreground">
          Keyboard shortcut: <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs font-data">Ctrl+U</kbd> to upload
        </p>
      </div>
    </div>
  );
};

export default FileUploadZone;