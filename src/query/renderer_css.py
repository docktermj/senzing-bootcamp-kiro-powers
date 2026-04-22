"""CSS styles for the Senzing entity graph visualization."""

RENDERER_CSS = """\
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
    Roboto, Helvetica, Arial, sans-serif;
  background: #0f172a;
  color: #e2e8f0;
  overflow: hidden;
  height: 100vh;
  width: 100vw;
}

#graph-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

#graph-svg svg {
  width: 100%;
  height: 100%;
  display: block;
}

.node circle {
  stroke: #334155;
  stroke-width: 1.5px;
  fill: #3b82f6;
  cursor: grab;
  transition: stroke 0.15s, stroke-width 0.15s;
}

.node circle:hover {
  stroke: #f8fafc;
  stroke-width: 2.5px;
}

.node.selected circle {
  stroke: #facc15;
  stroke-width: 3px;
}

.node.dimmed circle {
  opacity: 0.15;
}

.link {
  stroke-width: 1.5px;
  opacity: 0.6;
}

.link.dimmed {
  opacity: 0.08;
}

.link.highlighted {
  opacity: 1;
  stroke-width: 2.5px;
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: #1e293b;
  color: #f1f5f9;
  border: 1px solid #475569;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 13px;
  white-space: nowrap;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* ---- Detail Panel ---- */

#detail-panel {
  position: fixed;
  top: 0;
  right: -360px;
  width: 340px;
  height: 100vh;
  background: #1e293b;
  border-left: 1px solid #334155;
  color: #e2e8f0;
  overflow-y: auto;
  padding: 20px 16px;
  z-index: 900;
  transition: right 0.25s ease;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.5);
  font-size: 14px;
}

#detail-panel.open {
  right: 0;
}

#detail-panel h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-right: 28px;
  word-break: break-word;
}

.detail-close {
  position: absolute;
  top: 14px;
  right: 14px;
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 4px;
}

.detail-close:hover {
  color: #f1f5f9;
  background: #334155;
}

.detail-section {
  margin-bottom: 14px;
}

.detail-label {
  display: block;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
  margin-bottom: 4px;
}

.detail-value {
  display: block;
  font-size: 14px;
  color: #f1f5f9;
}

.detail-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.detail-list li {
  padding: 3px 0;
  font-size: 13px;
  color: #cbd5e1;
  border-bottom: 1px solid #1e293b;
}

.detail-tag {
  display: inline-block;
  background: #334155;
  color: #94a3b8;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  margin-left: 4px;
}

.detail-feature {
  margin-bottom: 8px;
}

.detail-feature-key {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
  margin-bottom: 2px;
}

.detail-feature-val {
  display: block;
  font-size: 13px;
  color: #cbd5e1;
  padding-left: 8px;
}

/* ---- Clustering Controls ---- */

#clustering-controls {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 800;
  display: flex;
  align-items: flex-start;
  flex-direction: column;
  gap: 8px;
  background: #1e293bee;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 10px 14px;
  backdrop-filter: blur(6px);
}

.cluster-label {
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 6px;
}

.cluster-select {
  background: #0f172a;
  color: #e2e8f0;
  border: 1px solid #475569;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 13px;
  cursor: pointer;
  outline: none;
}

.cluster-select:focus {
  border-color: #3b82f6;
}

.cluster-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #cbd5e1;
  white-space: nowrap;
}

.legend-swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* ---- Search Filter ---- */

#search-container {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 800;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

#search-input {
  background: #0f172a;
  color: #e2e8f0;
  border: 1px solid #475569;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 13px;
  width: 220px;
  outline: none;
  font-family: inherit;
}

#search-input::placeholder {
  color: #64748b;
}

#search-input:focus {
  border-color: #3b82f6;
}

.search-no-matches {
  font-size: 12px;
  color: #f87171;
  padding: 2px 4px;
}

.node.search-match circle {
  stroke: #facc15;
  stroke-width: 2.5px;
}

/* ---- Stats Bar ---- */

#stats-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 800;
  background: #1e293bee;
  border-top: 1px solid #334155;
  padding: 8px 16px;
  backdrop-filter: blur(6px);
}

.stats-bar-items {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.stats-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stats-value {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.stats-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
}

.stats-divider {
  width: 1px;
  height: 28px;
  background: #475569;
  flex-shrink: 0;
}

.stats-breakdown .stats-value {
  font-size: 14px;
  color: #cbd5e1;
}

.stats-breakdown .stats-label {
  font-size: 9px;
}
"""
