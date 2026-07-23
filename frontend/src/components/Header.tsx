interface HeaderProps {
  activeTab: 'preview' | 'batch';
  setActiveTab: (tab: 'preview' | 'batch') => void;
  serverOnline: boolean;
}

export function Header({ activeTab, setActiveTab, serverOnline }: HeaderProps) {
  return (
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
  );
}
