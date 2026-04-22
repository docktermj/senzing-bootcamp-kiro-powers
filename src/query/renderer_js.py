"""JavaScript source for the Senzing entity graph D3.js renderer.

This module is embedded inline in the generated HTML file via the
``{{RENDERER_JS}}`` placeholder.  The code reads from the global
``GRAPH_DATA`` variable set by the HTML template.
"""

RENDERER_JS = """\
(function () {
  "use strict";

  // ---------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------
  var EDGE_COLORS = {
    strong: "#22c55e",
    moderate: "#f59e0b",
    weak: "#ef4444"
  };

  var DEFAULT_NODE_FILL = "#3b82f6";

  // ---------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------

  /** Compute node radius: base 5 + 4 * sqrt(recordCount). */
  function computeNodeRadius(recordCount) {
    return 5 + 4 * Math.sqrt(recordCount);
  }

  // ---------------------------------------------------------------
  // GraphRenderer
  // ---------------------------------------------------------------

  function GraphRenderer(container, graphData) {
    this.container = container;
    this.graphData = graphData;
    this.nodes = graphData.nodes || [];
    this.edges = graphData.edges || [];
    this.selectedNodeId = null;

    // Build lookup maps
    this.nodeById = {};
    var i;
    for (i = 0; i < this.nodes.length; i++) {
      this.nodeById[this.nodes[i].entityId] = this.nodes[i];
    }

    // Prepare link data with object references for D3
    this.links = [];
    for (i = 0; i < this.edges.length; i++) {
      var e = this.edges[i];
      var src = this.nodeById[e.sourceEntityId];
      var tgt = this.nodeById[e.targetEntityId];
      if (src && tgt) {
        this.links.push({
          source: src,
          target: tgt,
          matchStrength: e.matchStrength,
          matchLevel: e.matchLevel,
          sharedFeatures: e.sharedFeatures
        });
      }
    }

    this._initSVG();
    this._initSimulation();
    this._renderEdges();
    this._renderNodes();
    this._initZoomPan();
    this._initTooltip();
  }

  // --- SVG setup ------------------------------------------------

  GraphRenderer.prototype._initSVG = function () {
    var rect = this.container.getBoundingClientRect();
    this.width = rect.width || window.innerWidth;
    this.height = rect.height || window.innerHeight;

    this.svg = d3.select(this.container)
      .append("svg")
      .attr("width", this.width)
      .attr("height", this.height);

    // Group that receives zoom/pan transforms
    this.g = this.svg.append("g");
  };

  // --- Force simulation -----------------------------------------

  GraphRenderer.prototype._initSimulation = function () {
    var self = this;

    this.simulation = d3.forceSimulation(this.nodes)
      .force("charge", d3.forceManyBody()
        .strength(-120))
      .force("link", d3.forceLink(this.links)
        .id(function (d) { return d.entityId; })
        .distance(80))
      .force("center", d3.forceCenter(
        this.width / 2, this.height / 2))
      .force("collide", d3.forceCollide()
        .radius(function (d) {
          return computeNodeRadius(d.recordCount) + 2;
        }))
      .on("tick", function () { self._tick(); });
  };

  // --- Render edges (links) -------------------------------------

  GraphRenderer.prototype._renderEdges = function () {
    this.linkSelection = this.g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(this.links)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", function (d) {
        return EDGE_COLORS[d.matchStrength] || EDGE_COLORS.weak;
      });
  };

  // --- Render nodes ---------------------------------------------

  GraphRenderer.prototype._renderNodes = function () {
    var self = this;

    this.nodeSelection = this.g.append("g")
      .attr("class", "nodes")
      .selectAll("g")
      .data(this.nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(this._dragBehavior());

    this.nodeSelection.append("circle")
      .attr("r", function (d) {
        return computeNodeRadius(d.recordCount);
      })
      .attr("fill", DEFAULT_NODE_FILL);

    // Click handler for node selection
    this.nodeSelection.on("click", function (event, d) {
      event.stopPropagation();
      self._selectNode(d);
    });
  };

  // --- Drag behavior --------------------------------------------

  GraphRenderer.prototype._dragBehavior = function () {
    var self = this;

    function dragStarted(event, d) {
      if (!event.active) {
        self.simulation.alphaTarget(0.3).restart();
      }
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event, d) {
      if (!event.active) {
        self.simulation.alphaTarget(0);
      }
      d.fx = null;
      d.fy = null;
    }

    return d3.drag()
      .on("start", dragStarted)
      .on("drag", dragged)
      .on("end", dragEnded);
  };

  // --- Zoom & pan -----------------------------------------------

  GraphRenderer.prototype._initZoomPan = function () {
    var self = this;

    this.zoom = d3.zoom()
      .scaleExtent([0.1, 8])
      .on("zoom", function (event) {
        self.g.attr("transform", event.transform);
      });

    this.svg.call(this.zoom);

    // Click on empty space to deselect
    this.svg.on("click", function () {
      self._deselectNode();
    });
  };

  // --- Tooltip on hover -----------------------------------------

  GraphRenderer.prototype._initTooltip = function () {
    // Create tooltip element
    this.tooltipEl = document.createElement("div");
    this.tooltipEl.className = "tooltip";
    this.tooltipEl.style.display = "none";
    document.body.appendChild(this.tooltipEl);

    var self = this;

    this.nodeSelection
      .on("mouseenter", function (event, d) {
        var name = d.primaryName || "Entity " + d.entityId;
        self.tooltipEl.textContent = name;
        self.tooltipEl.style.display = "block";
      })
      .on("mousemove", function (event) {
        self.tooltipEl.style.left =
          (event.pageX + 12) + "px";
        self.tooltipEl.style.top =
          (event.pageY - 28) + "px";
      })
      .on("mouseleave", function () {
        self.tooltipEl.style.display = "none";
      });
  };

  // --- Simulation tick ------------------------------------------

  GraphRenderer.prototype._tick = function () {
    this.linkSelection
      .attr("x1", function (d) { return d.source.x; })
      .attr("y1", function (d) { return d.source.y; })
      .attr("x2", function (d) { return d.target.x; })
      .attr("y2", function (d) { return d.target.y; });

    this.nodeSelection
      .attr("transform", function (d) {
        return "translate(" + d.x + "," + d.y + ")";
      });
  };

  // --- Node selection / highlighting ----------------------------

  GraphRenderer.prototype._selectNode = function (d) {
    this.selectedNodeId = d.entityId;
    var selectedId = d.entityId;

    // Build set of connected entity IDs
    var connectedIds = {};
    connectedIds[selectedId] = true;
    for (var i = 0; i < this.links.length; i++) {
      var lnk = this.links[i];
      if (lnk.source.entityId === selectedId) {
        connectedIds[lnk.target.entityId] = true;
      }
      if (lnk.target.entityId === selectedId) {
        connectedIds[lnk.source.entityId] = true;
      }
    }

    // Highlight / dim nodes
    this.nodeSelection
      .classed("selected", function (n) {
        return n.entityId === selectedId;
      })
      .classed("dimmed", function (n) {
        return !connectedIds[n.entityId];
      });

    // Highlight / dim edges
    this.linkSelection
      .classed("highlighted", function (l) {
        return l.source.entityId === selectedId ||
          l.target.entityId === selectedId;
      })
      .classed("dimmed", function (l) {
        return l.source.entityId !== selectedId &&
          l.target.entityId !== selectedId;
      });

    // Show detail panel
    if (this.detailPanel) {
      this.detailPanel.show(d);
    }
  };

  GraphRenderer.prototype._deselectNode = function () {
    this.selectedNodeId = null;
    this.nodeSelection
      .classed("selected", false)
      .classed("dimmed", false);
    this.linkSelection
      .classed("highlighted", false)
      .classed("dimmed", false);

    // Hide detail panel
    if (this.detailPanel) {
      this.detailPanel.hide();
    }
  };

  // ---------------------------------------------------------------
  // DetailPanel
  // ---------------------------------------------------------------

  function DetailPanel(panelEl) {
    this.el = panelEl;
  }

  /** Build and display entity detail content. */
  DetailPanel.prototype.show = function (node) {
    var html = '<button class="detail-close" ' +
      'aria-label="Close">&times;</button>';
    html += '<h2>' + _esc(node.primaryName ||
      "Entity " + node.entityId) + '</h2>';
    html += '<div class="detail-section">';
    html += '<span class="detail-label">Entity ID</span>';
    html += '<span class="detail-value">' + node.entityId + '</span>';
    html += '</div>';
    html += '<div class="detail-section">';
    html += '<span class="detail-label">Records</span>';
    html += '<span class="detail-value">' + node.recordCount + '</span>';
    html += '</div>';

    // Data sources
    var sources = node.dataSources || [];
    html += '<div class="detail-section">';
    html += '<span class="detail-label">Data Sources</span>';
    html += '<ul class="detail-list">';
    for (var s = 0; s < sources.length; s++) {
      html += '<li>' + _esc(sources[s]) + '</li>';
    }
    html += '</ul></div>';

    // Records list
    var records = node.records || [];
    if (records.length) {
      html += '<div class="detail-section">';
      html += '<span class="detail-label">Record Details</span>';
      html += '<ul class="detail-list">';
      for (var r = 0; r < records.length; r++) {
        var rec = records[r];
        html += '<li>' + _esc(rec.recordId) +
          ' <span class="detail-tag">' +
          _esc(rec.dataSource) + '</span></li>';
      }
      html += '</ul></div>';
    }

    // Shared features
    var features = node.features || {};
    var featureKeys = Object.keys(features);
    if (featureKeys.length) {
      html += '<div class="detail-section">';
      html += '<span class="detail-label">Shared Features</span>';
      for (var f = 0; f < featureKeys.length; f++) {
        var key = featureKeys[f];
        var vals = features[key];
        html += '<div class="detail-feature">';
        html += '<span class="detail-feature-key">' +
          _esc(key) + '</span>';
        if (Array.isArray(vals)) {
          for (var v = 0; v < vals.length; v++) {
            html += '<span class="detail-feature-val">' +
              _esc(vals[v]) + '</span>';
          }
        }
        html += '</div>';
      }
      html += '</div>';
    }

    this.el.innerHTML = html;
    this.el.classList.add("open");

    // Wire close button
    var self = this;
    var closeBtn = this.el.querySelector(".detail-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", function (evt) {
        evt.stopPropagation();
        self.hide();
        // Also deselect in the graph
        if (window.__graphRenderer) {
          window.__graphRenderer._deselectNode();
        }
      });
    }
  };

  /** Hide the detail panel. */
  DetailPanel.prototype.hide = function () {
    this.el.classList.remove("open");
    this.el.innerHTML = "";
  };

  /** Escape HTML entities. */
  function _esc(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ---------------------------------------------------------------
  // Public API (exposed on window for other modules)
  // ---------------------------------------------------------------

  GraphRenderer.prototype.getSimulation = function () {
    return this.simulation;
  };

  GraphRenderer.prototype.getNodeSelection = function () {
    return this.nodeSelection;
  };

  GraphRenderer.prototype.getLinkSelection = function () {
    return this.linkSelection;
  };

  GraphRenderer.prototype.getNodeById = function () {
    return this.nodeById;
  };

  GraphRenderer.prototype.getLinks = function () {
    return this.links;
  };

  /** Recolor all node circles using a color function. */
  GraphRenderer.prototype.setNodeColors = function (colorFn) {
    this.nodeSelection.select("circle")
      .attr("fill", function (d) { return colorFn(d); });
  };

  // ---------------------------------------------------------------
  // ClusterController
  // ---------------------------------------------------------------

  function ClusterController(controlsEl, graphRenderer) {
    this.el = controlsEl;
    this.renderer = graphRenderer;
    this.mode = "none";

    // Collect distinct data sources from nodes
    var srcSet = {};
    var nodes = graphRenderer.nodes;
    for (var i = 0; i < nodes.length; i++) {
      var ps = nodes[i].primaryDataSource;
      if (ps) { srcSet[ps] = true; }
    }
    this.dataSources = Object.keys(srcSet).sort();

    // Build data-source color scale using D3 schemeCategory10
    this.dsColorScale = d3.scaleOrdinal()
      .domain(this.dataSources)
      .range(d3.schemeCategory10);

    // Pre-compute per-node average match level for match-strength mode
    this._computeAvgMatchLevels();

    this._renderControls();
    this._renderLegend();
  }

  /** Compute average match level for each node from connected links. */
  ClusterController.prototype._computeAvgMatchLevels = function () {
    this.avgMatchLevel = {};
    var sums = {};
    var counts = {};
    var links = this.renderer.links;
    for (var i = 0; i < links.length; i++) {
      var lnk = links[i];
      var ml = lnk.matchLevel || 3;
      var sId = lnk.source.entityId;
      var tId = lnk.target.entityId;
      sums[sId] = (sums[sId] || 0) + ml;
      counts[sId] = (counts[sId] || 0) + 1;
      sums[tId] = (sums[tId] || 0) + ml;
      counts[tId] = (counts[tId] || 0) + 1;
    }
    var nodes = this.renderer.nodes;
    for (var n = 0; n < nodes.length; n++) {
      var eid = nodes[n].entityId;
      if (counts[eid]) {
        this.avgMatchLevel[eid] = sums[eid] / counts[eid];
      } else {
        this.avgMatchLevel[eid] = null; // no relationships
      }
    }
  };

  /** Return match-strength color for a node based on avg match level. */
  ClusterController.prototype._matchStrengthColor = function (node) {
    var avg = this.avgMatchLevel[node.entityId];
    if (avg === null || avg === undefined) { return "#9ca3af"; }
    if (avg <= 1.5) { return "#22c55e"; }
    if (avg <= 2.5) { return "#f59e0b"; }
    return "#ef4444";
  };

  /** Render the dropdown control inside the controls div. */
  ClusterController.prototype._renderControls = function () {
    var self = this;
    var html = '<label class="cluster-label" for="cluster-select">' +
      'Color by:</label>' +
      '<select id="cluster-select" class="cluster-select">' +
      '<option value="none">No clustering</option>' +
      '<option value="dataSource">Data Source</option>' +
      '<option value="matchStrength">Match Strength</option>' +
      '</select>';
    this.el.innerHTML = html;

    // Legend container
    this.legendEl = document.createElement("div");
    this.legendEl.className = "cluster-legend";
    this.el.appendChild(this.legendEl);

    var select = this.el.querySelector("#cluster-select");
    select.addEventListener("change", function () {
      self.setMode(this.value);
    });
  };

  /** Switch clustering mode and recolor nodes. */
  ClusterController.prototype.setMode = function (mode) {
    this.mode = mode;
    var self = this;

    if (mode === "dataSource") {
      this.renderer.setNodeColors(function (d) {
        return self.dsColorScale(d.primaryDataSource || "Unknown");
      });
    } else if (mode === "matchStrength") {
      this.renderer.setNodeColors(function (d) {
        return self._matchStrengthColor(d);
      });
    } else {
      // "none" — uniform default color
      this.renderer.setNodeColors(function () {
        return DEFAULT_NODE_FILL;
      });
    }

    this._renderLegend();
  };

  /** Render the legend for the active clustering mode. */
  ClusterController.prototype._renderLegend = function () {
    if (!this.legendEl) { return; }
    var html = "";

    if (this.mode === "dataSource") {
      for (var i = 0; i < this.dataSources.length; i++) {
        var ds = this.dataSources[i];
        html += '<span class="legend-item">' +
          '<span class="legend-swatch" style="background:' +
          this.dsColorScale(ds) + '"></span>' +
          _esc(ds) + '</span>';
      }
    } else if (this.mode === "matchStrength") {
      var items = [
        { color: "#22c55e", label: "Strong (avg \\u2264 1.5)" },
        { color: "#f59e0b", label: "Moderate (avg \\u2264 2.5)" },
        { color: "#ef4444", label: "Weak (avg > 2.5)" },
        { color: "#9ca3af", label: "No relationships" }
      ];
      for (var j = 0; j < items.length; j++) {
        html += '<span class="legend-item">' +
          '<span class="legend-swatch" style="background:' +
          items[j].color + '"></span>' +
          items[j].label + '</span>';
      }
    }

    this.legendEl.innerHTML = html;
  };

  /** Return the current clustering mode. */
  ClusterController.prototype.getMode = function () {
    return this.mode;
  };

  /** Return the data-source color scale. */
  ClusterController.prototype.getDataSourceColorScale = function () {
    return this.dsColorScale;
  };

  /** Return the avg match levels map. */
  ClusterController.prototype.getAvgMatchLevels = function () {
    return this.avgMatchLevel;
  };

  // ---------------------------------------------------------------
  // SearchFilter
  // ---------------------------------------------------------------

  function SearchFilter(inputEl, graphRenderer) {
    this.inputEl = inputEl;
    this.renderer = graphRenderer;
    this.msgEl = null;

    this._createMessageEl();
    this._bindEvents();
  }

  /** Create the "no matches found" message element. */
  SearchFilter.prototype._createMessageEl = function () {
    this.msgEl = document.createElement("div");
    this.msgEl.className = "search-no-matches";
    this.msgEl.textContent = "No matches found";
    this.msgEl.style.display = "none";
    this.inputEl.parentNode.appendChild(this.msgEl);
  };

  /** Bind the input event to trigger search. */
  SearchFilter.prototype._bindEvents = function () {
    var self = this;
    this.inputEl.addEventListener("input", function () {
      self.apply(self.inputEl.value);
    });
  };

  /** Apply search: highlight matches, dim non-matches. */
  SearchFilter.prototype.apply = function (term) {
    var nodes = this.renderer.nodes;
    var nodeSelection = this.renderer.getNodeSelection();
    var linkSelection = this.renderer.getLinkSelection();

    // Empty search — restore everything
    if (!term || !term.trim()) {
      nodeSelection.classed("search-match", false)
        .classed("dimmed", false);
      linkSelection.classed("dimmed", false);
      this.msgEl.style.display = "none";
      return;
    }

    var lower = term.toLowerCase();
    var matchedIds = {};

    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      var nameMatch = n.primaryName &&
        n.primaryName.toLowerCase().indexOf(lower) !== -1;
      var recordMatch = false;
      var records = n.records || [];
      for (var r = 0; r < records.length; r++) {
        if (records[r].recordId &&
          records[r].recordId.toLowerCase().indexOf(lower) !== -1) {
          recordMatch = true;
          break;
        }
      }
      if (nameMatch || recordMatch) {
        matchedIds[n.entityId] = true;
      }
    }

    var matchCount = Object.keys(matchedIds).length;

    // Show / hide no-matches message
    this.msgEl.style.display = matchCount === 0 ? "block" : "none";

    // Highlight / dim nodes
    nodeSelection
      .classed("search-match", function (d) {
        return !!matchedIds[d.entityId];
      })
      .classed("dimmed", function (d) {
        return !matchedIds[d.entityId];
      });

    // Dim links not connected to any matched node
    linkSelection
      .classed("dimmed", function (l) {
        return !matchedIds[l.source.entityId] &&
          !matchedIds[l.target.entityId];
      });
  };

  /** Return the current search term. */
  SearchFilter.prototype.getTerm = function () {
    return this.inputEl.value;
  };

  // ---------------------------------------------------------------
  // StatsBar
  // ---------------------------------------------------------------

  function StatsBar(barEl, graphData, clusterController) {
    this.el = barEl;
    this.graphData = graphData;
    this.nodes = graphData.nodes || [];
    this.edges = graphData.edges || [];
    this.metadata = graphData.metadata || {};
    this.clusterController = clusterController || null;

    this._computeBaseStats();
    this.render();
  }

  /** Compute base statistics from graph data. */
  StatsBar.prototype._computeBaseStats = function () {
    this.entityCount = this.metadata.entityCount != null
      ? this.metadata.entityCount : this.nodes.length;
    this.recordCount = this.metadata.recordCount != null
      ? this.metadata.recordCount : 0;
    this.relationshipCount = this.metadata.relationshipCount != null
      ? this.metadata.relationshipCount : this.edges.length;

    // Data source count
    var dsSet = {};
    var dsList = this.metadata.dataSources || [];
    for (var i = 0; i < dsList.length; i++) {
      dsSet[dsList[i]] = true;
    }
    // Also gather from nodes if metadata is missing
    if (dsList.length === 0) {
      for (var n = 0; n < this.nodes.length; n++) {
        var sources = this.nodes[n].dataSources || [];
        for (var s = 0; s < sources.length; s++) {
          dsSet[sources[s]] = true;
        }
      }
    }
    this.dataSourceCount = Object.keys(dsSet).length;

    // Cross-source match rate: entities with records from >1 source
    var crossCount = 0;
    for (var j = 0; j < this.nodes.length; j++) {
      var nodeSources = this.nodes[j].dataSources || [];
      if (nodeSources.length > 1) { crossCount++; }
    }
    var total = this.nodes.length || 1;
    this.crossSourceRate = ((crossCount / total) * 100).toFixed(1);
  };

  /** Render the stats bar content. */
  StatsBar.prototype.render = function () {
    var html = '<div class="stats-bar-items">';
    html += '<span class="stats-item">' +
      '<span class="stats-value">' + this.entityCount + '</span>' +
      '<span class="stats-label">Entities</span></span>';
    html += '<span class="stats-item">' +
      '<span class="stats-value">' + this.recordCount + '</span>' +
      '<span class="stats-label">Records</span></span>';
    html += '<span class="stats-item">' +
      '<span class="stats-value">' + this.relationshipCount + '</span>' +
      '<span class="stats-label">Relationships</span></span>';
    html += '<span class="stats-item">' +
      '<span class="stats-value">' + this.dataSourceCount + '</span>' +
      '<span class="stats-label">Data Sources</span></span>';
    html += '<span class="stats-item">' +
      '<span class="stats-value">' + this.crossSourceRate + '%</span>' +
      '<span class="stats-label">Cross-Source</span></span>';

    // Clustering breakdown
    var breakdown = this._getClusterBreakdown();
    if (breakdown) {
      html += '<span class="stats-divider"></span>';
      html += breakdown;
    }

    html += '</div>';
    this.el.innerHTML = html;
  };

  /** Compute clustering breakdown based on current cluster mode. */
  StatsBar.prototype._getClusterBreakdown = function () {
    if (!this.clusterController) { return ""; }
    var mode = this.clusterController.getMode();
    if (mode === "none") { return ""; }

    var groups = {};
    var i;

    if (mode === "dataSource") {
      for (i = 0; i < this.nodes.length; i++) {
        var ds = this.nodes[i].primaryDataSource || "Unknown";
        groups[ds] = (groups[ds] || 0) + 1;
      }
    } else if (mode === "matchStrength") {
      var avgLevels = this.clusterController.getAvgMatchLevels();
      for (i = 0; i < this.nodes.length; i++) {
        var avg = avgLevels[this.nodes[i].entityId];
        var cat;
        if (avg === null || avg === undefined) { cat = "No relationships"; }
        else if (avg <= 1.5) { cat = "Strong"; }
        else if (avg <= 2.5) { cat = "Moderate"; }
        else { cat = "Weak"; }
        groups[cat] = (groups[cat] || 0) + 1;
      }
    }

    var keys = Object.keys(groups);
    if (keys.length === 0) { return ""; }

    var html = "";
    for (i = 0; i < keys.length; i++) {
      html += '<span class="stats-item stats-breakdown">' +
        '<span class="stats-value">' + groups[keys[i]] + '</span>' +
        '<span class="stats-label">' + _esc(keys[i]) + '</span></span>';
    }
    return html;
  };

  /** Update stats when clustering mode changes. */
  StatsBar.prototype.update = function () {
    this.render();
  };

  // ---------------------------------------------------------------
  // Bootstrap on DOMContentLoaded
  // ---------------------------------------------------------------

  function init() {
    var container = document.getElementById("graph-svg");
    if (!container) {
      throw new Error("Missing #graph-svg container element.");
    }
    if (typeof GRAPH_DATA === "undefined" || !GRAPH_DATA) {
      throw new Error("GRAPH_DATA is not defined.");
    }

    window.__graphRenderer = new GraphRenderer(
      container, GRAPH_DATA
    );

    // Initialize detail panel
    var panelEl = document.getElementById("detail-panel");
    if (panelEl) {
      window.__graphRenderer.detailPanel = new DetailPanel(panelEl);
    }

    // Initialize cluster controller
    var clusterEl = document.getElementById("clustering-controls");
    if (clusterEl) {
      window.__clusterController = new ClusterController(
        clusterEl, window.__graphRenderer
      );
    }

    // Initialize search filter
    var searchInput = document.getElementById("search-input");
    if (searchInput) {
      window.__searchFilter = new SearchFilter(
        searchInput, window.__graphRenderer
      );
    }

    // Initialize stats bar
    var statsBarEl = document.getElementById("stats-bar");
    if (statsBarEl) {
      window.__statsBar = new StatsBar(
        statsBarEl, GRAPH_DATA,
        window.__clusterController || null
      );

      // Hook into ClusterController so stats update on mode change
      if (window.__clusterController) {
        var origSetMode = window.__clusterController.setMode.bind(
          window.__clusterController
        );
        window.__clusterController.setMode = function (mode) {
          origSetMode(mode);
          window.__statsBar.update();
        };
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
"""
