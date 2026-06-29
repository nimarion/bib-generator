import { useState, useEffect } from 'react';
import './App.css';

interface Assets {
  fonts: string[];
  headers: string[];
  footers: string[];
  presets: string[];
}

interface Runner {
  firstname: string;
  lastname: string;
  header: string;
  footer: string;
}

const BACKEND_URL = 'http://localhost:8080';

const DEFAULT_RUNNERS: Runner[] = [
  {
    firstname: "Usain",
    lastname: "Bolt",
    header: "example/globus.png",
    footer: "example/footer.png"
  },
  {
    firstname: "Shelly-Ann",
    lastname: "Fraser",
    header: "example/bitburger.png",
    footer: "example/footer.png"
  }
];

const PRESETS: Record<string, [number, number]> = {
  A4: [4960, 3508],
  A5: [3508, 2480],
  A6: [2480, 1748],
  letter: [3300, 2550]
};

function App() {
  const [activeTab, setActiveTab] = useState<'preview' | 'batch'>('preview');
  const [serverOnline, setServerOnline] = useState<boolean>(false);
  const [assets, setAssets] = useState<Assets>({
    fonts: [],
    headers: [],
    footers: [],
    presets: []
  });

  // Preview form options
  const [text, setText] = useState<string>('BOLT');
  const [margin, setMargin] = useState<number>(175);
  const [textColor, setTextColor] = useState<string>('#000000');
  const [strokeColor, setStrokeColor] = useState<string>('#000000');
  const [strokeWidth, setStrokeWidth] = useState<number>(1);
  const [selectedFont, setSelectedFont] = useState<string>('');
  const [selectedHeader, setSelectedHeader] = useState<string>('');
  const [selectedFooter, setSelectedFooter] = useState<string>('');
  const [selectedSize, setSelectedSize] = useState<string>('A5');
  
  // Custom sizing states
  const [customWidth, setCustomWidth] = useState<string>('');
  const [customHeight, setCustomHeight] = useState<string>('');

  // Batch states
  const [batchJson, setBatchJson] = useState<string>(JSON.stringify(DEFAULT_RUNNERS, null, 2));
  const [batchGenerating, setBatchGenerating] = useState<boolean>(false);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);

  // Fetch discoverable assets and verify server status on mount
  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/assets`);
        if (res.ok) {
          const data: Assets = await res.json();
          setAssets(data);
          setServerOnline(true);
          
          // Set initial option selections
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

  // Poll server health status periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/health`);
        if (res.ok) {
          setServerOnline(true);
        } else {
          setServerOnline(false);
        }
      } catch {
        setServerOnline(false);
      }
    };
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Construct the real-time dynamic GET preview image URL
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
    
    // Cache-buster query param ensures instant redraw updates
    params.append('_cb', Date.now().toString());

    return `${BACKEND_URL}/generate?${params.toString()}`;
  };

  // Trigger POST /generate-batch and handle blob download of combined PDF
  const handleBatchSubmit = async () => {
    try {
      setBatchGenerating(true);
      const parsedRunners = JSON.parse(batchJson);
      
      const res = await fetch(`${BACKEND_URL}/generate-batch?size=${selectedSize}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(parsedRunners)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Failed to generate batch PDF');
      }

      // Convert response into file download
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'combined_bibs.pdf';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(`Batch PDF compilation error:\n${err.message}`);
    } finally {
      setBatchGenerating(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header bar */}
      <header className="app-header">
        <div className="brand-section">
          <h1>Bib Kiosk Dashboard</h1>
          <p>Real-time event bib and badge layout engine</p>
        </div>
        
        {/* Navigation Mode Tabs */}
        <div className="nav-tabs">
          <button 
            className={`tab-btn ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
          >
            Real-Time Designer
          </button>
          <button 
            className={`tab-btn ${activeTab === 'batch' ? 'active' : ''}`}
            onClick={() => setActiveTab('batch')}
          >
            Batch PDF Compiler
          </button>
        </div>

        {/* Server Status Indicator */}
        <div className="status-indicator">
          <span className={`status-dot ${serverOnline ? 'online' : 'offline'}`} />
          {serverOnline ? 'Kiosk Server Online' : 'Kiosk Server Offline'}
        </div>
      </header>

      {/* Main dashboard viewport */}
      <main className="dashboard-body">
        {activeTab === 'preview' ? (
          <>
            {/* Sidebar Controls Panel */}
            <aside className="sidebar">
              {/* Text Input */}
              <div className="control-group">
                <label>Runner Text (Number / Name)</label>
                <input 
                  type="text" 
                  className="input-text" 
                  value={text} 
                  onChange={(e) => setText(e.target.value)} 
                  placeholder="Enter text..."
                />
              </div>

              {/* Layout Size Selector */}
              <div className="control-group">
                <label>Canvas Size Template</label>
                <select 
                  className="select-input"
                  value={selectedSize}
                  onChange={(e) => setSelectedSize(e.target.value)}
                >
                  {assets.presets.map((preset) => (
                    <option key={preset} value={preset}>{preset} landscape (300 DPI)</option>
                  ))}
                </select>
              </div>

              {/* Custom Canvas Sizing Option */}
              <div className="control-row">
                <div className="control-group">
                  <label>Custom Width (px)</label>
                  <input 
                    type="number" 
                    className="input-text" 
                    value={customWidth} 
                    onChange={(e) => setCustomWidth(e.target.value)} 
                    placeholder="Width"
                  />
                </div>
                <div className="control-group">
                  <label>Custom Height (px)</label>
                  <input 
                    type="number" 
                    className="input-text" 
                    value={customHeight} 
                    onChange={(e) => setCustomHeight(e.target.value)} 
                    placeholder="Height"
                  />
                </div>
              </div>

              {/* Font Selector */}
              <div className="control-group">
                <label>Typography Font</label>
                <select 
                  className="select-input"
                  value={selectedFont}
                  onChange={(e) => setSelectedFont(e.target.value)}
                >
                  {assets.fonts.map((f) => {
                    const basename = f.split('/').pop() || f;
                    return <option key={f} value={f}>{basename}</option>;
                  })}
                </select>
              </div>

              {/* Header Selector */}
              <div className="control-group">
                <label>Header Sponsor Logo</label>
                <select 
                  className="select-input"
                  value={selectedHeader}
                  onChange={(e) => setSelectedHeader(e.target.value)}
                >
                  {assets.headers.map((h) => {
                    const basename = h.split('/').pop() || h;
                    return <option key={h} value={h}>{basename}</option>;
                  })}
                </select>
              </div>

              {/* Footer Selector */}
              <div className="control-group">
                <label>Footer Event Template</label>
                <select 
                  className="select-input"
                  value={selectedFooter}
                  onChange={(e) => setSelectedFooter(e.target.value)}
                >
                  {assets.footers.map((f) => {
                    const basename = f.split('/').pop() || f;
                    return <option key={f} value={f}>{basename}</option>;
                  })}
                </select>
              </div>

              {/* Color Styling Customizations */}
              <div className="control-row">
                <div className="control-group">
                  <label>Text Color</label>
                  <div className="color-picker-wrapper">
                    <input 
                      type="color" 
                      className="input-color" 
                      value={textColor} 
                      onChange={(e) => setTextColor(e.target.value)}
                    />
                    <span className="color-hex">{textColor}</span>
                  </div>
                </div>
                <div className="control-group">
                  <label>Outline Color</label>
                  <div className="color-picker-wrapper">
                    <input 
                      type="color" 
                      className="input-color" 
                      value={strokeColor} 
                      onChange={(e) => setStrokeColor(e.target.value)}
                    />
                    <span className="color-hex">{strokeColor}</span>
                  </div>
                </div>
              </div>

              {/* Layout Spacing Sliders */}
              <div className="control-row">
                <div className="control-group">
                  <label>Text Margin: {margin}px</label>
                  <input 
                    type="range" 
                    min="25" 
                    max="500" 
                    step="5"
                    className="input-range"
                    value={margin}
                    onChange={(e) => setMargin(parseInt(e.target.value))}
                  />
                </div>
                <div className="control-group">
                  <label>Outline Width: {strokeWidth}px</label>
                  <input 
                    type="range" 
                    min="1" 
                    max="15" 
                    step="1"
                    className="input-range"
                    value={strokeWidth}
                    onChange={(e) => setStrokeWidth(parseInt(e.target.value))}
                  />
                </div>
              </div>
            </aside>

            {/* Right-Side Live Preview Canvas */}
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
                    bib-generator --server
                  </code>
                </div>
              )}
            </section>
          </>
        ) : (
          /* Batch JSON Compiler Mode */
          <section className="batch-container">
            <div className="batch-card">
              <h2>Dynamic Batch JSON Compiler</h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                Define a JSON array of event entrants. Clicking generate compiles high-quality, lossless optimized bibs for all runners in parallel on your multi-core CPU, packing the results into a single download-ready PDF document.
              </p>
              
              <textarea 
                className="batch-editor"
                value={batchJson}
                onChange={(e) => setBatchJson(e.target.value)}
              />

              <button 
                className="btn-primary" 
                onClick={handleBatchSubmit}
                disabled={batchGenerating || !serverOnline}
              >
                {batchGenerating ? (
                  <>
                    <div className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                    Generating Batch PDF...
                  </>
                ) : 'Compile Print-Ready Combined PDF'}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
