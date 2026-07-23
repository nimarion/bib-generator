import type { Runner, Assets } from '../types';
import { getFontOptions, getHeaderOptions, getFooterOptions, DEFAULT_FONTS, DEFAULT_HEADERS, DEFAULT_FOOTERS } from '../assetUtils';

interface RunnerTableProps {
  runners: Runner[];
  assets: Assets;
  onRunnerChange: (index: number, field: keyof Runner, value: string) => void;
  onDeleteRunner: (index: number) => void;
}

export function RunnerTable({
  runners,
  assets,
  onRunnerChange,
  onDeleteRunner
}: RunnerTableProps) {
  if (runners.length === 0) {
    return (
      <div className="table-wrapper">
        <table className="runner-table">
          <tbody>
            <tr>
              <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                No entrants loaded. Upload a CSV/XLSX file or click "+ Add Entrant" above.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="runner-table">
        <thead>
          <tr>
            <th style={{ width: '40px' }}>#</th>
            <th>First Name (firstname)</th>
            <th>Last Name (lastname)</th>
            <th>Font Path (font)</th>
            <th>Header Logo (header)</th>
            <th>Footer Logo (footer)</th>
            <th style={{ width: '60px' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {runners.map((r, idx) => {
            const fontOpts = getFontOptions(assets.fonts, r.font);
            const headerOpts = getHeaderOptions(assets.headers, r.header);
            const footerOpts = getFooterOptions(assets.footers, r.footer);

            return (
              <tr key={idx}>
                <td className="row-num">{idx + 1}</td>
                <td>
                  <input 
                    type="text" 
                    className="table-input" 
                    value={r.firstname} 
                    onChange={(e) => onRunnerChange(idx, 'firstname', e.target.value)} 
                    placeholder="First Name"
                  />
                </td>
                <td>
                  <input 
                    type="text" 
                    className="table-input bold" 
                    value={r.lastname} 
                    onChange={(e) => onRunnerChange(idx, 'lastname', e.target.value)} 
                    placeholder="Last Name (Required)"
                  />
                </td>
                {/* Font Selector Dropdown */}
                <td>
                  <select 
                    className="table-select" 
                    value={fontOpts.includes(r.font) ? r.font : '__custom__'} 
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '__custom__') {
                        const input = prompt('Enter custom font file path:', r.font || DEFAULT_FONTS[0]);
                        if (input !== null && input.trim() !== '') {
                          onRunnerChange(idx, 'font', input.trim());
                        }
                      } else {
                        onRunnerChange(idx, 'font', val);
                      }
                    }}
                  >
                    <optgroup label="Select Font Path">
                      {fontOpts.map(f => (
                        <option key={f} value={f}>
                          {f.split('/').pop()} ({f})
                        </option>
                      ))}
                    </optgroup>
                    <option value="__custom__">✏️ Enter Custom Path...</option>
                  </select>
                </td>
                {/* Header Selector Dropdown */}
                <td>
                  <select 
                    className="table-select" 
                    value={headerOpts.includes(r.header) ? r.header : '__custom__'} 
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '__custom__') {
                        const input = prompt('Enter custom header image path:', r.header || DEFAULT_HEADERS[0]);
                        if (input !== null && input.trim() !== '') {
                          onRunnerChange(idx, 'header', input.trim());
                        }
                      } else {
                        onRunnerChange(idx, 'header', val);
                      }
                    }}
                  >
                    <optgroup label="Select Header Logo">
                      {headerOpts.map(h => (
                        <option key={h} value={h}>
                          {h.split('/').pop()} ({h})
                        </option>
                      ))}
                    </optgroup>
                    <option value="__custom__">✏️ Enter Custom Path...</option>
                  </select>
                </td>
                {/* Footer Selector Dropdown */}
                <td>
                  <select 
                    className="table-select" 
                    value={footerOpts.includes(r.footer) ? r.footer : '__custom__'} 
                    onChange={(e) => {
                      const val = e.target.value;
                      if (val === '__custom__') {
                        const input = prompt('Enter custom footer image path:', r.footer || DEFAULT_FOOTERS[0]);
                        if (input !== null && input.trim() !== '') {
                          onRunnerChange(idx, 'footer', input.trim());
                        }
                      } else {
                        onRunnerChange(idx, 'footer', val);
                      }
                    }}
                  >
                    <optgroup label="Select Footer Logo">
                      {footerOpts.map(f => (
                        <option key={f} value={f}>
                          {f.split('/').pop()} ({f})
                        </option>
                      ))}
                    </optgroup>
                    <option value="__custom__">✏️ Enter Custom Path...</option>
                  </select>
                </td>
                <td>
                  <button 
                    className="btn-icon-danger" 
                    onClick={() => onDeleteRunner(idx)}
                    title="Delete row"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
