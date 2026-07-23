import { useState, useRef, type ChangeEvent, type DragEvent } from 'react';
import type { Runner, ImportStatus } from '../types';
import { downloadSampleCSV, downloadSampleXLSX, parseFileToRunners } from '../assetUtils';

interface BatchImportCardProps {
  defaultFont: string;
  defaultHeader: string;
  defaultFooter: string;
  onImportSuccess: (runners: Runner[], filename: string) => void;
}

export function BatchImportCard({
  defaultFont,
  defaultHeader,
  defaultFooter,
  onImportSuccess
}: BatchImportCardProps) {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [importStatus, setImportStatus] = useState<ImportStatus | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (file: File) => {
    parseFileToRunners(
      file,
      defaultFont,
      defaultHeader,
      defaultFooter,
      (runners, filename) => {
        onImportSuccess(runners, filename);
        setImportStatus({
          type: 'success',
          message: `Successfully imported ${runners.length} entrant(s) from "${filename}".`
        });
      },
      (errMsg) => {
        setImportStatus({ type: 'error', message: errMsg });
      }
    );
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="batch-card import-card">
      <div className="batch-card-header">
        <div>
          <h2>Batch Data Import (CSV / XLSX)</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Upload a CSV or Excel spreadsheet containing pre-defined columns: <code>firstname</code>, <code>lastname</code>, <code>font</code>, <code>footer</code>, <code>header</code>.
          </p>
        </div>
        <div className="template-actions">
          <button className="btn-secondary" onClick={downloadSampleCSV}>
            📥 Download CSV Template
          </button>
          <button className="btn-secondary" onClick={downloadSampleXLSX}>
            📊 Download XLSX Template
          </button>
        </div>
      </div>

      {/* Drag and Drop Zone */}
      <div 
        className={`dropzone ${dragActive ? 'active' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept=".csv,.tsv,.xlsx,.xls" 
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            if (e.target.files && e.target.files[0]) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />
        <div className="dropzone-content">
          <span className="dropzone-icon">📁</span>
          <div>
            <p className="dropzone-title">Click to browse or drag & drop CSV / Excel file here</p>
            <p className="dropzone-subtitle">Supported formats: .csv, .tsv, .xlsx, .xls</p>
          </div>
        </div>
      </div>

      {/* Import Feedback Toast */}
      {importStatus && (
        <div className={`import-alert ${importStatus.type}`}>
          <span>{importStatus.message}</span>
          <button onClick={() => setImportStatus(null)} className="alert-close">×</button>
        </div>
      )}
    </div>
  );
}
