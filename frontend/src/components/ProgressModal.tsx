import type { ExportProgress } from '../types';

interface ProgressModalProps {
  progress: ExportProgress;
  onCancel: () => void;
}

export function ProgressModal({ progress, onCancel }: ProgressModalProps) {
  if (!progress.active) return null;

  return (
    <div className="progress-modal-overlay">
      <div className="progress-modal-card">
        <div className="progress-modal-header">
          <h3>⚡ Live Server Batch Export</h3>
          <button className="btn-icon-danger" onClick={onCancel} title="Cancel Export">✕</button>
        </div>

        <div className="progress-bar-container">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progress.percent}%` }}
          />
        </div>

        <div className="progress-modal-stats">
          <span className="progress-percent">{progress.percent}%</span>
          <span className="progress-count">{progress.current} / {progress.total} Pages</span>
        </div>

        <p className="progress-status-text">{progress.statusText}</p>

        {progress.etaSeconds !== null && (
          <p className="progress-eta">
            ⏱️ Estimated time remaining: {progress.etaSeconds} sec
          </p>
        )}

        <div className="progress-modal-actions">
          <button className="btn-danger sm" onClick={onCancel}>
            Stop & Cancel Export
          </button>
        </div>
      </div>
    </div>
  );
}
