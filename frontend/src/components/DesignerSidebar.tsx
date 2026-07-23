import type { Assets } from '../types';
import { getFontOptions, getHeaderOptions, getFooterOptions } from '../assetUtils';

interface DesignerSidebarProps {
  text: string;
  setText: (v: string) => void;
  selectedSize: string;
  setSelectedSize: (v: string) => void;
  customWidth: string;
  setCustomWidth: (v: string) => void;
  customHeight: string;
  setCustomHeight: (v: string) => void;
  selectedFont: string;
  setSelectedFont: (v: string) => void;
  selectedHeader: string;
  setSelectedHeader: (v: string) => void;
  selectedFooter: string;
  setSelectedFooter: (v: string) => void;
  textColor: string;
  setTextColor: (v: string) => void;
  strokeColor: string;
  setStrokeColor: (v: string) => void;
  margin: number;
  setMargin: (v: number) => void;
  strokeWidth: number;
  setStrokeWidth: (v: number) => void;
  assets: Assets;
}

export function DesignerSidebar({
  text,
  setText,
  selectedSize,
  setSelectedSize,
  customWidth,
  setCustomWidth,
  customHeight,
  setCustomHeight,
  selectedFont,
  setSelectedFont,
  selectedHeader,
  setSelectedHeader,
  selectedFooter,
  setSelectedFooter,
  textColor,
  setTextColor,
  strokeColor,
  setStrokeColor,
  margin,
  setMargin,
  strokeWidth,
  setStrokeWidth,
  assets
}: DesignerSidebarProps) {
  return (
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
          {getFontOptions(assets.fonts, selectedFont).map((f) => {
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
          {getHeaderOptions(assets.headers, selectedHeader).map((h) => {
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
          {getFooterOptions(assets.footers, selectedFooter).map((f) => {
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
  );
}
