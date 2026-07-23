import { useState, useEffect, useRef } from 'react';
import type { Assets, Runner, ExportProgress } from './types';
import {
  BACKEND_URL,
  DEFAULT_RUNNERS,
  DEFAULT_FONTS,
  DEFAULT_HEADERS,
  DEFAULT_FOOTERS,
  PRESETS
} from './assetUtils';
import { Header } from './components/Header';
import { DesignerSidebar } from './components/DesignerSidebar';
import { BatchImportCard } from './components/BatchImportCard';
import { RunnerTable } from './components/RunnerTable';
import { ProgressModal } from './components/ProgressModal';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<'preview' | 'batch'>('preview');
  const [serverOnline, setServerOnline] = useState<boolean>(false);
  const [assets, setAssets] = useState<Assets>({
    fonts: [],
    headers: [],
    footers: [],
    presets: []
  });

  // Designer form state
  const [text, setText] = useState<string>('BOLT');
  const [margin, setMargin] = useState<number>(175);
  const [textColor, setTextColor] = useState<string>('#000000');
  const [strokeColor, setStrokeColor] = useState<string>('#000000');
  const [strokeWidth, setStrokeWidth] = useState<number>(1);
  const [selectedFont, setSelectedFont] = useState<string>('');
  const [selectedHeader, setSelectedHeader] = useState<string>('');
  const [selectedFooter, setSelectedFooter] = useState<string>('');
  const [selectedSize, setSelectedSize] = useState<string>('A5');
  
  // Custom dimensions state
  const [customWidth, setCustomWidth] = useState<string>('');
  const [customHeight, setCustomHeight] = useState<string>('');

  // Batch states
  const [runners, setRunners] = useState<Runner[]>(DEFAULT_RUNNERS);
  const [batchJson, setBatchJson] = useState<string>(JSON.stringify(DEFAULT_RUNNERS, null, 2));
  const [viewMode, setViewMode] = useState<'table' | 'json'>('table');
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  
  // Progress modal & cancellation controller
  const [exportProgress, setExportProgress] = useState<ExportProgress>({
    active: false,
    current: 0,
    total: 0,
    percent: 0,
    statusText: '',
    startTime: 0,
    etaSeconds: null
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  // Fetch discoverable assets on mount
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/assets`);
        if (res.ok) {
          const data: Assets = await res.json();
          setAssets(data);
          setServerOnline(true);
          
          if (data.fonts.length > 0) setSelectedFont(data.fonts[0]);
          if (data.headers.length > 0) setSelectedHeader(data.headers[0]);
          if (data.footers.length > 0) setSelectedFooter(data.footers[0]);
          if (data.presets.length > 0) setSelectedSize(data.presets.includes('A5') ? 'A5' : data.presets[0]);
        }
      } catch (err) {
        console.error('Error contacting kiosk server:', err);
        setServerOnline(false);
      }
    };
    fetchAssets();
  }, []);

  // Poll server health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        setServerOnline(res.ok);
      } catch {
        setServerOnline(false);
      }
    };
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const updateRunners = (newRunners: Runner[]) => {
    setRunners(newRunners);
    setBatchJson(JSON.stringify(newRunners, null, 2));
  };

  const handleJsonChange = (jsonStr: string) => {
    setBatchJson(jsonStr);
    try {
      const parsed = JSON.parse(jsonStr);
      if (Array.isArray(parsed)) {
        setRunners(parsed);
      }
    } catch {
      // Allow temporary unparsed JSON editing without state disruption
    }
  };

  const handleRunnerChange = (index: number, field: keyof Runner, value: string) => {
    const updated = [...runners];
    updated[index] = { ...updated[index], [field]: value };
    updateRunners(updated);
  };

  const handleAddRunner = () => {
    const newRunner: Runner = {
      firstname: '',
      lastname: 'New Runner',
      font: selectedFont || (assets.fonts[0] || DEFAULT_FONTS[0]),
      header: selectedHeader || (assets.headers[0] || DEFAULT_HEADERS[0]),
      footer: selectedFooter || (assets.footers[0] || DEFAULT_FOOTERS[0])
    };
    updateRunners([...runners, newRunner]);
  };

  const handleDeleteRunner = (index: number) => {
    updateRunners(runners.filter((_, i) => i !== index));
  };

  const handleApplyGlobalAssets = () => {
    const updated = runners.map(r => ({
      ...r,
      font: selectedFont || r.font,
      header: selectedHeader || r.header,
      footer: selectedFooter || r.footer
    }));
    updateRunners(updated);
  };

  const getPreviewUrl = () => {
    const params = new URLSearchParams({
      text: text,
      margin: margin.toString(),
      text_color: textColor,
      stroke_color: strokeColor,
      stroke_width: strokeWidth.toString(),
      size: selectedSize
    });

    if (selectedFont) params.append('font', selectedFont);
    if (selectedHeader) params.append('header', selectedHeader);
    if (selectedFooter) params.append('footer', selectedFooter);
    if (customWidth && customHeight) {
      params.append('width', customWidth);
      params.append('height', customHeight);
    }
    
    params.append('_cb', Date.now().toString());
    return `${BACKEND_URL}/generate?${params.toString()}`;
  };

  const handleCancelExport = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setExportProgress({
      active: false,
      current: 0,
      total: 0,
      percent: 0,
      statusText: '',
      startTime: 0,
      etaSeconds: null
    });
  };

  // Trigger POST /generate-batch-stream to receive real-time server rendering events
  const handleBatchSubmit = async () => {
    let parsedRunners: Runner[] = [];
    try {
      parsedRunners = JSON.parse(batchJson);
    } catch {
      alert("Invalid JSON data. Please fix formatting errors.");
      return;
    }

    const totalRunners = parsedRunners.length;
    if (totalRunners === 0) {
      alert("No entrants to compile.");
      return;
    }

    const startTime = Date.now();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setExportProgress({
      active: true,
      current: 0,
      total: totalRunners,
      percent: 0,
      statusText: `Connecting to backend renderer for ${totalRunners} entrant(s)...`,
      startTime: startTime,
      etaSeconds: null
    });

    try {
      const response = await fetch(`${BACKEND_URL}/generate-batch-stream?size=${selectedSize}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(parsedRunners),
        signal: abortController.signal
      });

      if (!response.ok || !response.body) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const jsonStr = trimmed.slice(6);
            try {
              const eventData = JSON.parse(jsonStr);

              if (eventData.event === 'error') {
                throw new Error(eventData.error);
              }

              if (eventData.event === 'progress') {
                const elapsedSec = (Date.now() - startTime) / 1000;
                let etaSec: number | null = null;
                if (eventData.current > 0) {
                  const rate = eventData.current / elapsedSec;
                  etaSec = Math.ceil((eventData.total - eventData.current) / rate);
                }

                setExportProgress({
                  active: true,
                  current: eventData.current,
                  total: eventData.total,
                  percent: eventData.percent,
                  statusText: `Server generated page ${eventData.current} of ${eventData.total} ("${eventData.lastname}, ${eventData.firstname}")...`,
                  startTime: startTime,
                  etaSeconds: etaSec
                });
              }

              if (eventData.event === 'complete') {
                setExportProgress(prev => ({
                  ...prev,
                  percent: 100,
                  current: eventData.total,
                  statusText: `Backend compilation complete! Downloading compressed single PDF...`
                }));

                const binaryStr = atob(eventData.pdf_base64);
                const bytes = new Uint8Array(binaryStr.length);
                for (let i = 0; i < binaryStr.length; i++) {
                  bytes[i] = binaryStr.charCodeAt(i);
                }

                const blob = new Blob([bytes], { type: 'application/pdf' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'combined_bibs.pdf';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);

                setTimeout(() => {
                  setExportProgress(prev => ({ ...prev, active: false }));
                }, 1500);
              }
            } catch (parseErr: any) {
              if (parseErr.message && !parseErr.message.includes('JSON')) {
                throw parseErr;
              }
            }
          }
        }
      }

    } catch (err: any) {
      if (err.name === 'AbortError' || err.message?.includes('cancelled')) {
        console.log("Batch export cancelled.");
      } else {
        alert(`Batch compilation error:\n${err.message}`);
      }
      setExportProgress(prev => ({ ...prev, active: false }));
    }
  };

  return (
    <div className="app-container">
      {/* Header banner component */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        serverOnline={serverOnline} 
      />

      {/* Main viewport */}
      <main className="dashboard-body">
        {activeTab === 'preview' ? (
          <>
            {/* Sidebar Controls Panel */}
            <DesignerSidebar 
              text={text}
              setText={setText}
              selectedSize={selectedSize}
              setSelectedSize={setSelectedSize}
              customWidth={customWidth}
              setCustomWidth={setCustomWidth}
              customHeight={customHeight}
              setCustomHeight={setCustomHeight}
              selectedFont={selectedFont}
              setSelectedFont={setSelectedFont}
              selectedHeader={selectedHeader}
              setSelectedHeader={setSelectedHeader}
              selectedFooter={selectedFooter}
              setSelectedFooter={setSelectedFooter}
              textColor={textColor}
              setTextColor={setTextColor}
              strokeColor={strokeColor}
              setStrokeColor={setStrokeColor}
              margin={margin}
              setMargin={setMargin}
              strokeWidth={strokeWidth}
              setStrokeWidth={setStrokeWidth}
              assets={assets}
            />

            {/* Live Preview Canvas */}
            <section className="preview-container">
              {serverOnline ? (
                <div className="preview-wrapper">
                  {previewLoading && (
                    <div className="spinner-overlay">
                      <div className="spinner" />
                    </div>
                  )}
                  <img 
                    src={getPreviewUrl()} 
                    alt="Live Bib Preview" 
                    className={`bib-img ${previewLoading ? 'loading' : ''}`}
                    onLoad={() => setPreviewLoading(false)}
                    onLoadStart={() => setPreviewLoading(true)}
                  />
                  <div className="preview-stats">
                    <span>Dimension: {customWidth && customHeight ? `${customWidth}x${customHeight}` : PRESETS[selectedSize]?.join('x') || 'Custom'} px</span>
                    <span>Status: Dynamic Feed</span>
                  </div>
                </div>
              ) : (
                <div className="preview-wrapper">
                  <h3 style={{ color: 'var(--danger-primary)', marginBottom: '0.5rem' }}>Server Unreachable</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Please start your python kiosk server to enable the real-time layout canvas:</p>
                  <code style={{ background: 'var(--bg-primary)', padding: '0.5rem 1rem', borderRadius: '4px', margin: '1rem 0', fontFamily: 'monospace' }}>
                    python3 server.py
                  </code>
                </div>
              )}
            </section>
          </>
        ) : (
          /* Batch JSON / CSV / XLSX Compiler Mode */
          <section className="batch-container">
            {/* CSV / XLSX Upload Card */}
            <BatchImportCard 
              defaultFont={selectedFont || (assets.fonts[0] || DEFAULT_FONTS[0])}
              defaultHeader={selectedHeader || (assets.headers[0] || DEFAULT_HEADERS[0])}
              defaultFooter={selectedFooter || (assets.footers[0] || DEFAULT_FOOTERS[0])}
              onImportSuccess={(newRunners) => updateRunners(newRunners)}
            />

            {/* Batch Data Editor & Compiler Card */}
            <div className="batch-card flex-1">
              <div className="batch-toolbar">
                <div className="view-mode-toggle">
                  <button 
                    className={`mode-btn ${viewMode === 'table' ? 'active' : ''}`}
                    onClick={() => setViewMode('table')}
                  >
                    📋 Interactive Table ({runners.length} Entrants)
                  </button>
                  <button 
                    className={`mode-btn ${viewMode === 'json' ? 'active' : ''}`}
                    onClick={() => setViewMode('json')}
                  >
                    {'{ }'} Raw JSON View
                  </button>
                </div>

                {viewMode === 'table' && (
                  <div className="table-actions">
                    <button className="btn-secondary sm" onClick={handleAddRunner}>
                      + Add Entrant
                    </button>
                    <button className="btn-secondary sm" onClick={handleApplyGlobalAssets} title="Set font, header, and footer of all rows to current designer selections">
                      ⚡ Apply Selected Assets to All
                    </button>
                    <button className="btn-danger sm" onClick={() => updateRunners([])}>
                      🗑️ Clear All
                    </button>
                  </div>
                )}
              </div>

              {viewMode === 'table' ? (
                <RunnerTable 
                  runners={runners}
                  assets={assets}
                  onRunnerChange={handleRunnerChange}
                  onDeleteRunner={handleDeleteRunner}
                />
              ) : (
                <textarea 
                  className="batch-editor"
                  value={batchJson}
                  onChange={(e) => handleJsonChange(e.target.value)}
                />
              )}

              <div className="compiler-bottom-bar">
                <div className="compiler-options">
                  <label>Paper Size Preset:</label>
                  <select 
                    className="select-input inline"
                    value={selectedSize}
                    onChange={(e) => setSelectedSize(e.target.value)}
                  >
                    {assets.presets.map((preset) => (
                      <option key={preset} value={preset}>{preset} landscape</option>
                    ))}
                  </select>
                </div>

                <button 
                  className="btn-primary" 
                  onClick={handleBatchSubmit}
                  disabled={exportProgress.active || !serverOnline || runners.length === 0}
                >
                  🚀 Compile Print-Ready Combined PDF ({runners.length} Pages)
                </button>
              </div>
            </div>
          </section>
        )}
      </main>

      {/* SSE Progress Overlay Modal */}
      <ProgressModal 
        progress={exportProgress}
        onCancel={handleCancelExport}
      />
    </div>
  );
}

export default App;
