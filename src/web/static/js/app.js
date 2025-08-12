// Global state
let currentAnalysisId = null;
let currentGraphData = null;
let currentDepth = 1;
let currentViewMode = 'HIERARCHY';
let currentTopView = 'BSI'; // 'BSI' | 'HLD'
let hldSelectedKinds = new Set();
let selectedNode = null;
let isProcessing = false;
let cy = null;

// Color mapping for modules
const moduleColors = {
    'module_service_layer': '#D0021B',
    'module_utilities': '#00BCD4', 
    'module_other': '#607D8B',
    'module_data_models': '#FFC107',
    'frontend_module': '#4CAF50',
    'backend_module': '#2196F3',
    'database_module': '#FF9800',
    'Service': '#D0021B',
    'Model': '#FFC107',
    'Utility': '#00BCD4',
    'Module': '#607D8B',
    'API': '#4A90E2',
    'Application': '#2196F3',
    'Component': '#9C27B0',
    'Function': '#607D8B',
    'Class': '#795548',
    'Controller': '#8BC34A',
    'Test': '#E91E63'
};

// DOM elements
const elements = {
    // Tabs
    tabBtns: document.querySelectorAll('.tab-btn'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // File input
    fileDropZone: document.getElementById('fileDropZone'),
    fileInput: document.getElementById('fileInput'),
    
    // GitHub input
    githubUrl: document.getElementById('githubUrl'),
    githubBranch: document.getElementById('githubBranch'),
    
    // Analyze button
    analyzeBtn: document.getElementById('analyzeBtn'),
    
    // Status
    statusSection: document.getElementById('statusSection'),
    progressFill: document.getElementById('progressFill'),
    statusMessage: document.getElementById('statusMessage'),
    
    // Export
    exportSection: document.getElementById('exportSection'),
    exportBtns: document.querySelectorAll('.export-btn'),
    
    // Statistics
    statsSection: document.getElementById('statsSection'),
    filesAnalyzed: document.getElementById('filesAnalyzed'),
    coveragePercent: document.getElementById('coveragePercent'),
    hldNodes: document.getElementById('hldNodes'),
    lldNodes: document.getElementById('lldNodes'),
    totalEdges: document.getElementById('totalEdges'),
    
    // Team Progress
    teamProgressSection: document.getElementById('teamProgressSection'),
    backendProgress: document.getElementById('backendProgress'),
    backendProgressFill: document.getElementById('backendProgressFill'),
    dataProgress: document.getElementById('dataProgress'),
    dataProgressFill: document.getElementById('dataProgressFill'),
    
    // Health
    healthSection: document.getElementById('healthSection'),
    codeQuality: document.getElementById('codeQuality'),
    complexity: document.getElementById('complexity'),
    dependencies: document.getElementById('dependencies'),
    
    // Dependencies
    dependenciesSection: document.getElementById('dependenciesSection'),
    
    // Activity
    activitySection: document.getElementById('activitySection'),
    activityContent: document.getElementById('activityContent'),
    
    // PM Info
    pmInfo: document.getElementById('pmInfo'),
    pmStats: document.getElementById('pmStats'),
    
    // Metadata
    metadataSection: document.getElementById('metadataSection'),
    metadataContent: document.getElementById('metadataContent'),
    
    // Logs
    logsContent: document.getElementById('logsContent'),
    
    // Graph
    graphTitle: document.getElementById('graphTitle'),
    nodeCount: document.getElementById('nodeCount'),
    edgeCount: document.getElementById('edgeCount'),
    depthLabel: document.getElementById('depthLabel'),
    graphContainer: document.getElementById('graphContainer'),
    emptyState: document.getElementById('emptyState'),
    cy: document.getElementById('cy'),
    
    // Depth controls
    depthSlider: document.getElementById('depthSlider'),
    
    // Node details
    nodeDetails: document.getElementById('nodeDetails'),
    nodeDetailsTitle: document.getElementById('nodeDetailsTitle'),
    nodeDetailsContent: document.getElementById('nodeDetailsContent'),
    closeNodeDetails: document.getElementById('closeNodeDetails'),
    
    // Toolbar buttons
    fitViewBtn: document.getElementById('fitViewBtn'),
    centerBtn: document.getElementById('centerBtn'),
    exportBtn: document.getElementById('exportBtn')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    initializeCytoscape();
    addLog('Ready to analyze', 'info');
    ['filterContains','filterDepends','filterCalls'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => displayGraph());
    });
    // Top view toggle
    const viewBSI = document.getElementById('viewBSI');
    const viewHLD = document.getElementById('viewHLD');
    if (viewBSI && viewHLD) {
        viewBSI.addEventListener('click', async () => {
            currentTopView = 'BSI';
            const hc = document.getElementById('hldControls');
            if (hc) hc.style.display = 'none';
            await loadGraphData();
        });
        viewHLD.addEventListener('click', async () => {
            currentTopView = 'HLD';
            const hc = document.getElementById('hldControls');
            if (hc) hc.style.display = 'block';
            await loadGraphData();
        });
    }
    // HLD/LLD radio handlers
    ['hldModeHLD','hldModeLLD','hldModeAll'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => displayGraph());
    });
    // HLD kind filter clicks (delegated)
    const kf = document.getElementById('hldKindFilters');
    if (kf) {
        kf.addEventListener('click', (e) => {
            const t = e.target;
            if (t && t.dataset && t.dataset.kind) {
                const kind = t.dataset.kind;
                if (hldSelectedKinds.has(kind)) hldSelectedKinds.delete(kind); else hldSelectedKinds.add(kind);
                // toggle visual state
                t.classList.toggle('active', hldSelectedKinds.has(kind));
                displayGraph();
            }
        });
    }
});

// Initialize Cytoscape
function initializeCytoscape() {
    cy = cytoscape({
        container: elements.cy,
        elements: [],
        style: [
            {
                selector: 'node',
                style: {
                    'content': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'background-color': 'data(color)',
                    'color': '#ffffff',
                    'border-width': 3,
                    'border-color': '#2c3e50',
                    'shape': 'roundrectangle',
                    'width': 'mapData(sizeFactor, 1, 8, 100, 420)',
                    'height': 'mapData(sizeFactor, 1, 8, 50, 220)',
                    'font-size': 'mapData(sizeFactor, 1, 8, 14, 24)',
                    'font-weight': 'bold',
                    'text-wrap': 'wrap',
                    'text-max-width': 'mapData(sizeFactor, 1, 8, 120, 360)',
                    'text-outline-width': 2,
                    'text-outline-color': '#2c3e50',
                    'text-outline-opacity': 0.8,
                    'opacity': 1
                }
            },
            {
                selector: 'node[type = "Cluster"]',
                style: {
                    'shape': 'round-rectangle',
                    'background-color': 'data(clusterColor)',
                    'border-color': '#000000',
                    'border-width': 2,
                    'padding': 24,
                    'compound-sizing-wrt-labels': 'exclude',
                    'opacity': 1
                }
            },
            {
                selector: 'node[level = "HLD"]',
                style: {
                    'border-width': 4,
                    'border-color': '#1a1a1a',
                    'width': 150,
                    'height': 80,
                    'font-size': '14px',
                    'font-weight': 'bold',
                    'text-outline-width': 3,
                    'text-outline-color': '#1a1a1a',
                    'opacity': 1
                }
            },
            {
                selector: 'node[level = "LLD"]',
                style: {
                    'border-width': 2,
                    'border-color': '#34495e',
                    'width': 100,
                    'height': 50,
                    'font-size': '11px',
                    'text-outline-width': 2,
                    'text-outline-color': '#34495e',
                    'opacity': 1
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 4,
                    'line-color': '#95a5a6',
                    'target-arrow-color': '#95a5a6',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'content': 'data(label)',
                    'font-size': '11px',
                    'font-weight': 'bold',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -15,
                    'text-background-color': 'white',
                    'text-background-opacity': 0.9,
                    'text-background-padding': 4,
                    'text-border-color': '#7f8c8d',
                    'text-border-width': 1,
                    'text-border-opacity': 0.5,
                    'text-outline-width': 1,
                    'text-outline-color': 'white',
                    'text-outline-opacity': 0.8,
                    'text-opacity': 0,
                    'opacity': 0.2
                }
            },
            { selector: 'edge[type = "contains"]', style: { 'line-color': '#22C55E', 'target-arrow-color': '#22C55E', 'width': 20 } },
            { selector: 'edge[type = "depends_on"]', style: { 'line-color': '#3B82F6', 'target-arrow-color': '#3B82F6', 'line-style': 'dashed', 'width': 20 } },
            { selector: 'edge[type = "calls"]', style: { 'line-color': '#F59E0B', 'target-arrow-color': '#F59E0B', 'line-style': 'dotted', 'width': 20 } },
            { selector: 'edge[level = "BUSINESS"]', style: { 'width': 40 } },
            { selector: 'edge[level = "SYSTEM"]', style: { 'width': 20 } },
            {
                selector: 'edge:selected',
                style: {
                    'opacity': 1,
                    'line-color': 'data(color)',
                    'target-arrow-color': 'data(color)',
                    'width': 6
                }
            },
            {
                selector: 'edge[bidirectional = "true"]',
                style: {
                    'source-arrow-shape': 'triangle',
                    'source-arrow-color': '#7f8c8d',
                    'opacity': 0.2
                }
            },
            {
                selector: 'edge[type = "data_flow"]',
                style: {
                    'line-color': '#e74c3c',
                    'target-arrow-color': '#e74c3c',
                    'source-arrow-color': '#e74c3c',
                    'width': 6,
                    'line-style': 'solid',
                    'opacity': 0.2
                }
            },
            {
                selector: 'edge:selected',
                style: {
                    'opacity': 1,
                    'width': 5,
                    'text-opacity': 1
                }
            }
        ],
        layout: { name: 'preset' }
    });

    // Add event listeners for Cytoscape
    cy.on('tap', 'node', function(evt) {
        const nodeEle = evt.target;
        selectNode(nodeEle.data());
        highlightEdgesForNode(nodeEle);
    });

    cy.on('tap', 'edge', function(evt) {
        const edgeEle = evt.target;
        showEdgeDetails(edgeEle.data());
        cy.elements('edge').unselect();
        edgeEle.select();
    });

    cy.on('tap', function(evt) {
        if (evt.target === cy) {
            clearEdgeHighlight();
            closeNodeDetails();
        }
    });
}

// Initialize event listeners
function initializeEventListeners() {
    // Tab switching
    elements.tabBtns.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // File drop zone
    elements.fileDropZone.addEventListener('click', () => elements.fileInput.click());
    elements.fileDropZone.addEventListener('dragover', handleDragOver);
    elements.fileDropZone.addEventListener('dragleave', handleDragLeave);
    elements.fileDropZone.addEventListener('drop', handleDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Analyze button
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    
    // Depth slider
    elements.depthSlider.addEventListener('input', function() {
        currentDepth = parseInt(this.value);
        updateDepthLabel();
        if (currentGraphData) {
            displayGraph();
        }
    });
    
    // Export buttons
    elements.exportBtns.forEach(btn => {
        btn.addEventListener('click', () => handleExport(btn.dataset.format));
    });
    
    // Node details close
    elements.closeNodeDetails.addEventListener('click', closeNodeDetails);
    
    // Toolbar buttons
    elements.fitViewBtn.addEventListener('click', () => cy.fit());
    elements.centerBtn.addEventListener('click', () => cy.center());
    elements.exportBtn.addEventListener('click', () => handleExport('json'));
}

// Set view mode
function setViewMode(mode) {
    currentViewMode = mode;
    document.getElementById('hierarchyBtn').classList.toggle('active', mode === 'HIERARCHY');
    document.getElementById('connectionsBtn').classList.toggle('active', mode === 'CONNECTIONS');
    
    if (currentGraphData) {
        displayGraph();
    }
}

// Update depth label
function updateDepthLabel() {
    const labels = ['Business View', 'System View', 'Implementation View'];
    elements.depthLabel.textContent = labels[currentDepth - 1];
}

// Get data flow types between modules
function getDataFlowTypes(sourceNode, targetNode) {
    const sourceType = sourceNode.type || sourceNode.name || '';
    const targetType = targetNode.type || targetNode.name || '';
    
    // Service Layer connections
    if (sourceType.includes('Service') || targetType.includes('Service')) {
        if (sourceType.includes('Model') || targetType.includes('Model')) {
            return 'Calculation Data, History Records';
        }
        if (sourceType.includes('Utility') || targetType.includes('Utility')) {
            return 'Validation Results, Processed Data';
        }
        if (sourceType.includes('Other') || targetType.includes('Other')) {
            return 'User Input, Configuration';
        }
    }
    
    // Data Models connections
    if (sourceType.includes('Model') || targetType.includes('Model')) {
        if (sourceType.includes('Utility') || targetType.includes('Utility')) {
            return 'Formatted Data, Validation Rules';
        }
        if (sourceType.includes('Other') || targetType.includes('Other')) {
            return 'Raw Data, Schema Definitions';
        }
    }
    
    // Utilities connections
    if (sourceType.includes('Utility') || targetType.includes('Utility')) {
        if (sourceType.includes('Other') || targetType.includes('Other')) {
            return 'Processed Input, Error Messages';
        }
    }
    
    // Default data types based on common patterns
    if (sourceType.includes('Service') || targetType.includes('Service')) {
        return 'Business Logic, API Calls';
    }
    if (sourceType.includes('Model') || targetType.includes('Model')) {
        return 'Entity Data, Schema Info';
    }
    if (sourceType.includes('Utility') || targetType.includes('Utility')) {
        return 'Helper Functions, Validation';
    }
    
    return 'Configuration, Metadata';
}

// Get node parent module
function getNodeParentModule(node) {
    // First check if node has parent_module metadata
    if (node.metadata && node.metadata.parent_module) {
        return node.metadata.parent_module;
    }
    
    // Fallback: Map LLD nodes to their parent HLD module based on naming patterns
    const nodeId = node.id;
    if (nodeId.includes('frontend') || nodeId.includes('catalog') || nodeId.includes('cart') || nodeId.includes('auth')) return 'frontend_module';
    if (nodeId.includes('service') || nodeId.includes('order') || nodeId.includes('payment') || nodeId.includes('inventory')) return 'backend_module';
    if (nodeId.includes('database') || nodeId.includes('_db')) return 'database_module';
    
    // Original fallback logic
    if (nodeId.includes('_app') || nodeId.includes('Other')) return 'module_other';
    if (nodeId.includes('Service') || nodeId.includes('History') || nodeId.includes('Calculator')) return 'module_service_layer';
    if (nodeId.includes('Validation') || nodeId.includes('Data Processing')) return 'module_utilities';
    return 'module_other'; // default
}

// Display graph with enhanced visualization
function displayGraph() {
    if (!currentGraphData || !Array.isArray(currentGraphData.nodes) || !Array.isArray(currentGraphData.edges)) {
        return;
    }
    
    const elements = [];
    
    // Determine HLD/LLD preset mode when HLD view is active
    const mode = (currentTopView === 'HLD') ? getHldMode() : 'DEPTH';
    const filteredNodes = currentGraphData.nodes.filter(node => {
        const lvl = (node.level || '').toUpperCase();
        if (mode === 'HLD') {
            // HLD: show only BUSINESS and SYSTEM; apply kind filter if set
            if (lvl === 'IMPLEMENTATION') return false;
            if (hldSelectedKinds.size > 0) {
                const k = String(node.type || 'Module');
                return hldSelectedKinds.has(k);
            }
            return true;
        }
        if (mode === 'LLD') {
            // LLD: show only SYSTEM and IMPLEMENTATION; apply kind filter on SYSTEM only
            if (lvl === 'BUSINESS') return false;
            if (lvl === 'SYSTEM' && hldSelectedKinds.size > 0) {
                const k = String(node.type || 'Module');
                return hldSelectedKinds.has(k);
            }
            return true;
        }
        if (mode === 'ALL') return true;
        const nodeDepth = node.metadata?.technical_depth || (lvl === 'BUSINESS' ? 1 : (lvl === 'SYSTEM' ? 2 : 3));
        return nodeDepth <= currentDepth;
    });
    
    // Single deterministic rendering path: always use server-provided positions
    filteredNodes.forEach(node => {
        const nodeColor = node.metadata?.color || moduleColors[node.id] || '#4b5563';
        const clusterColor = node.type === 'Cluster' ? (node.color || 'rgba(99,102,241,0.08)') : undefined;
        elements.push({
            data: {
                id: node.id,
                label: node.name || node.id,
                type: node.type,
                level: node.level,
                color: nodeColor,
                clusterColor,
                sizeFactor: node.metadata?.size_factor || 1,
                parent: node.parent || undefined
            },
            position: node.position || { x: 0, y: 0 }
        });
    });

    const visible = new Set(filteredNodes.map(n => n.id));
    const showContains = document.getElementById('filterContains')?.checked !== false;
    const showDepends = document.getElementById('filterDepends')?.checked === true;
    const showCalls = document.getElementById('filterCalls')?.checked === true;
    currentGraphData.edges.forEach(edge => {
        if (!visible.has(edge.from_node) || !visible.has(edge.to_node)) return;
        const t = (edge.type || '').toLowerCase();
        if (t === 'contains' && !showContains) return;
        if ((t === 'depends_on' || t === 'depends') && !showDepends) return;
        if (t === 'calls' && !showCalls) return;
        // Filter: no edges involving raw Implementation nodes
        const srcNode = filteredNodes.find(n => n.id === edge.from_node);
        const dstNode = filteredNodes.find(n => n.id === edge.to_node);
        const isImpl = (n) => n && n.level === 'IMPLEMENTATION' && n.type !== 'Cluster';
        if (isImpl(srcNode) || isImpl(dstNode)) return;
        // Also skip Business -> Cluster contains (server prunes, but double-guard in UI)
        if (t === 'contains' && srcNode && dstNode && srcNode.level === 'BUSINESS' && dstNode.type === 'Cluster') return;
        const edgeKey = edge.id || `${edge.from_node}-${edge.to_node}`;
        const levelWidth = (lvl) => (lvl === 'BUSINESS' ? 8 : (lvl === 'SYSTEM' ? 4 : 2));
        const src = srcNode || {};
        elements.push({
            data: {
                id: edgeKey,
                source: edge.from_node,
                target: edge.to_node,
                label: edge.metadata?.relationship_type || edge.type || '',
                type: edge.type,
                color: (t==='contains') ? '#22C55E' : (t==='depends_on' ? '#3B82F6' : '#F59E0B'),
                level: src.level || 'SYSTEM'
            }
        });
    });
    
    // Update graph
    cy.elements().remove();
    cy.add(elements);
    
    // Always use preset layout; positions are computed server-side for determinism
    cy.layout({
        name: 'preset',
        padding: 50
    }).run();
    
    setTimeout(() => cy.fit(), 300);
    
    // Update view label
    if (elements.depthLabel) {
        elements.depthLabel.textContent = getCurrentDepthLabel();
    }

    // Update statistics
    updateGraphStats();
    updatePMDashboard();
}

// Update graph statistics
function updateGraphStats() {
    if (!currentGraphData) return;
    
    const mode = (currentTopView === 'HLD') ? getHldMode() : 'DEPTH';
    const filteredNodes = currentGraphData.nodes.filter(node => {
        const lvl = (node.level || '').toUpperCase();
        if (mode === 'HLD') return lvl !== 'IMPLEMENTATION';
        if (mode === 'LLD') return lvl !== 'BUSINESS';
        if (mode === 'ALL') return true;
        const nodeDepth = node.metadata?.technical_depth || (lvl === 'BUSINESS' ? 1 : (lvl === 'SYSTEM' ? 2 : 3));
        return nodeDepth <= currentDepth;
    });
    
    elements.nodeCount.textContent = `${filteredNodes.length} nodes`;
    elements.edgeCount.textContent = `${currentGraphData.edges.length} connections`;
}

// Update PM dashboard
function updatePMDashboard() {
    if (!currentGraphData || !currentGraphData.metadata) return;
    
    if (currentGraphData.metadata.pm_metrics) {
        const metrics = currentGraphData.metadata.pm_metrics;
        const stats = currentGraphData.metadata.statistics;
        
        elements.pmStats.innerHTML = `
            <div>Completion: ${metrics.completion_percentage || 0}%</div>
            <div>Risk Level: ${metrics.risk_level || 'Unknown'}</div>
            <div>Active Dependencies: ${metrics.active_dependencies || 0}</div>
            <div>Total Components: ${stats.total_nodes || 0}</div>
            <div>Depth Level: ${getCurrentDepthLabel()}</div>
        `;
        elements.pmInfo.style.display = 'block';
    }
}

// Get current depth label
function getCurrentDepthLabel() {
    if (currentTopView === 'HLD') {
        const m = getHldMode();
        if (m === 'HLD') return 'HLD View';
        if (m === 'LLD') return 'LLD View';
        if (m === 'ALL') return 'Complete Architecture';
    }
    switch(currentDepth) {
        case 1: return 'Business View';
        case 2: return 'System View';
        case 3: return 'Implementation View';
        default: return 'Unknown';
    }
}

function getHldMode() {
    const h = document.querySelector('input[name="hldMode"]:checked');
    return h ? h.value : 'HLD';
}

// Tab switching
function switchTab(tabName) {
    elements.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
}

// File handling
function handleDragOver(e) {
    e.preventDefault();
    elements.fileDropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.fileDropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    elements.fileDropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFiles(Array.from(files));
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFiles(Array.from(files));
    }
}

async function handleFiles(files) {
    // If a directory was dropped via webkitdirectory, package it into a zip in-browser is complex.
    // Here we accept either a single zip OR a directory selection and send as FormData with multiple files.
    if (files.length === 1 && (files[0].type === 'application/zip' || files[0].name.endsWith('.zip'))) {
        await uploadZip(files[0]);
        return;
    }
    await uploadDirectory(files);
}

// Analysis handling
async function handleAnalyze() {
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    
    if (activeTab === 'upload') {
        const files = elements.fileInput.files;
        if (files.length === 0) {
            addLog('Please select a file to analyze', 'error');
            return;
        }
        await handleFiles(Array.from(files));
    } else if (activeTab === 'github') {
        const url = elements.githubUrl.value.trim();
        const branch = elements.githubBranch.value.trim() || 'main';
        
        if (!url) {
            addLog('Please enter a GitHub repository URL', 'error');
            return;
        }
        await analyzeGithub(url, branch);
    }
}

async function uploadZip(file) {
    if (isProcessing) return;
    
    isProcessing = true;
    updateAnalyzeButton();
    showStatus('Uploading zip...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/analysis/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentAnalysisId = result.analysisId;
            addLog('File uploaded successfully, starting analysis...', 'success');
            pollAnalysisStatus();
        } else {
            throw new Error(result.error || 'Upload failed');
        }
    } catch (error) {
        addLog(`Upload failed: ${error.message}`, 'error');
        hideStatus();
    } finally {
        isProcessing = false;
        updateAnalyzeButton();
    }
}

async function uploadDirectory(files) {
    if (isProcessing) return;
    isProcessing = true;
    updateAnalyzeButton();
    showStatus('Uploading folder (multiple files)...');

    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file, file.webkitRelativePath || file.name);
    }

    try {
        const response = await fetch('/api/analysis/upload', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        if (result.success) {
            currentAnalysisId = result.analysisId;
            addLog('Folder uploaded successfully, starting analysis...', 'success');
            pollAnalysisStatus();
        } else {
            throw new Error(result.error || 'Upload failed');
        }
    } catch (error) {
        addLog(`Folder upload failed: ${error.message}`, 'error');
        hideStatus();
    } finally {
        isProcessing = false;
        updateAnalyzeButton();
    }
}

async function analyzeGithub(url, branch) {
    if (isProcessing) return;
    
    isProcessing = true;
    updateAnalyzeButton();
    showStatus('Analyzing GitHub repository...');
    
    try {
        const response = await fetch('/api/analysis/github', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, branch })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentAnalysisId = result.analysisId;
            addLog('GitHub analysis started...', 'success');
            pollAnalysisStatus();
        } else {
            throw new Error(result.error || 'GitHub analysis failed');
        }
    } catch (error) {
        addLog(`GitHub analysis failed: ${error.message}`, 'error');
        hideStatus();
    } finally {
        isProcessing = false;
        updateAnalyzeButton();
    }
}

async function pollAnalysisStatus() {
    if (!currentAnalysisId) return;
    
    try {
        const response = await fetch(`/api/analysis/${currentAnalysisId}/status`);
        const result = await response.json();
        
        updateProgress(result.progress);
        updateStatusMessage(result.message);
        
        if (result.status === 'completed') {
            addLog('Analysis completed successfully!', 'success');
            hideStatus();
            await loadGraphData();
            showExportSection();
            updateMetadata();
        } else if (result.status === 'failed') {
            addLog(`Analysis failed: ${result.message}`, 'error');
            hideStatus();
        } else {
            // Continue polling
            setTimeout(pollAnalysisStatus, 1000);
        }
    } catch (error) {
        addLog(`Status check failed: ${error.message}`, 'error');
        hideStatus();
    }
}

async function loadGraphData() {
    if (!currentAnalysisId) return;
    
    try {
        const url = currentTopView === 'HLD' 
            ? `/api/analysis/${currentAnalysisId}/hld_graph`
            : `/api/analysis/${currentAnalysisId}/graph`;
        const response = await fetch(url);
        const data = await response.json();
        if (!data || data.error) {
            throw new Error(data?.error || 'Invalid graph response');
        }
        currentGraphData = data;

        // Populate HLD kind filters if in HLD view
        if (currentTopView === 'HLD') {
            const kinds = (currentGraphData.metadata && currentGraphData.metadata.kinds) || [];
            const kf = document.getElementById('hldKindFilters');
            if (kf) {
                kf.innerHTML = kinds.map(k => `<button type="button" class="toolbar-btn" data-kind="${k}">${k}</button>`).join(' ');
                // default: none selected = show all
                hldSelectedKinds.clear();
            }
        }
        
        // Show graph
        elements.emptyState.style.display = 'none';
        elements.cy.style.display = 'block';
        
        // Display graph with current settings
        displayGraph();
        
        // Update statistics and health
        updateStatistics(currentGraphData);
        updateComponentHealth(currentGraphData);
        
        // Show dashboard sections
        elements.teamProgressSection.style.display = 'block';
        elements.dependenciesSection.style.display = 'block';
        elements.activitySection.style.display = 'block';
        
        addLog('Graph data loaded successfully', 'success');
    } catch (error) {
        addLog(`Failed to load graph data: ${error.message}`, 'error');
    }
}

// Node selection
function selectNode(node) {
    selectedNode = node;
    showNodeDetails(node);
}

function clearEdgeHighlight() {
    if (!cy) return;
    cy.elements('edge').style({'opacity': 0.2, 'text-opacity': 0});
}

function highlightEdgesForNode(nodeEle) {
    clearEdgeHighlight();
    const connected = nodeEle.connectedEdges();
    connected.forEach(e => e.style({'opacity': 1, 'text-opacity': 1}));
}

function showEdgeDetails(edgeData) {
    const src = cy.getElementById(edgeData.source).data();
    const tgt = cy.getElementById(edgeData.target).data();
    elements.nodeDetailsTitle.textContent = 'Connection Details';
    const examples = edgeData.metadata?.examples || [];
    const intent = edgeData.metadata?.intent || [];
    const items = [];
    items.push(`<div class="detail-item"><span class="detail-label">Type:</span> <span class="detail-value">${edgeData.type || ''}</span></div>`);
    items.push(`<div class="detail-item"><span class="detail-label">From:</span> <span class="detail-value">${src.label}</span></div>`);
    items.push(`<div class="detail-item"><span class="detail-label">To:</span> <span class="detail-value">${tgt.label}</span></div>`);
    if (intent.length) {
        items.push(`<div class="detail-item"><span class="detail-label">Actions/Data:</span> <span class="detail-value">${intent.join(', ')}</span></div>`);
    }
    if (examples.length) {
        items.push(`<div class="detail-item"><span class="detail-label">Examples:</span><pre class="detail-value">${examples.map(e => JSON.stringify(e, null, 2)).join('\n\n')}</pre></div>`);
    }
    elements.nodeDetailsContent.innerHTML = items.join('');
    elements.nodeDetails.style.display = 'block';
}

function showNodeDetails(node) {
    elements.nodeDetailsTitle.textContent = node.name || node.id;
    
    const details = [];
    details.push(`<div class="detail-item"><span class="detail-label">Type:</span> <span class="detail-value">${node.type}</span></div>`);
    details.push(`<div class="detail-item"><span class="detail-label">Level:</span> <span class="detail-value">${node.level}</span></div>`);
    
    if (node.metadata?.purpose) {
        details.push(`<div class="detail-item"><span class="detail-label">Purpose:</span> <span class="detail-value">${node.metadata.purpose}</span></div>`);
    }
    // Show routes if present (API nodes)
    if (node.metadata?.routes && node.metadata.routes.length) {
        const rows = node.metadata.routes.map(r => `${r.method} ${r.path} → ${r.handler}`);
        details.push(`<div class="detail-item"><span class="detail-label">Routes:</span> <span class="detail-value">${rows.join('<br>')}</span></div>`);
    }

    // Connections summary (incoming/outgoing by type)
    if (cy) {
        const ele = cy.getElementById(node.id);
        if (ele && ele.length) {
            const incoming = ele.incomers('edge');
            const outgoing = ele.outgoers('edge');
            const sum = (edges) => {
                const m = {};
                edges.forEach(e => { const t = e.data('type') || ''; m[t] = (m[t]||0)+1;});
                return Object.entries(m).map(([k,v]) => `${k}: ${v}`).join(', ');
            };
            details.push(`<div class="detail-item"><span class="detail-label">Incoming:</span> <span class="detail-value">${sum(incoming)}</span></div>`);
            details.push(`<div class="detail-item"><span class="detail-label">Outgoing:</span> <span class="detail-value">${sum(outgoing)}</span></div>`);
        }
    }
    
    if (node.metadata?.complexity) {
        details.push(`<div class="detail-item"><span class="detail-label">Complexity:</span> <span class="detail-value">${node.metadata.complexity}</span></div>`);
    }
    
    if (node.files && node.files.length > 0) {
        details.push(`<div class="detail-item"><span class="detail-label">Files:</span> <span class="detail-value files">${node.files.join('<br>')}</span></div>`);
    }
    
    if (node.functions && node.functions.length > 0) {
        details.push(`<div class="detail-item"><span class="detail-label">Functions:</span> <span class="detail-value">${node.functions.join(', ')}</span></div>`);
    }
    
    if (node.classes && node.classes.length > 0) {
        details.push(`<div class="detail-item"><span class="detail-label">Classes:</span> <span class="detail-value">${node.classes.join(', ')}</span></div>`);
    }
    
    elements.nodeDetailsContent.innerHTML = details.join('');
    elements.nodeDetails.style.display = 'block';
}

function closeNodeDetails() {
    elements.nodeDetails.style.display = 'none';
    selectedNode = null;
}

// Export handling
async function handleExport(format) {
    if (!currentAnalysisId) {
        addLog('No analysis data to export', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/analysis/${currentAnalysisId}/export/${format}`);
        const blob = await response.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `autograph_${format}_${Date.now()}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        addLog(`Exported ${format.toUpperCase()} successfully`, 'success');
    } catch (error) {
        addLog(`Export failed: ${error.message}`, 'error');
    }
}

// Utility functions
function showStatus(message) {
    elements.statusSection.style.display = 'block';
    updateStatusMessage(message);
}

function hideStatus() {
    elements.statusSection.style.display = 'none';
}

function updateProgress(progress) {
    elements.progressFill.style.width = `${progress}%`;
}

function updateStatusMessage(message) {
    elements.statusMessage.textContent = message;
}

function updateAnalyzeButton() {
    elements.analyzeBtn.disabled = isProcessing;
    elements.analyzeBtn.innerHTML = isProcessing 
        ? '<i class="fas fa-spinner fa-spin"></i> Processing...'
        : '<i class="fas fa-play"></i> Start Analysis';
}

function showExportSection() {
    elements.exportSection.style.display = 'block';
}

function updateStatistics(data) {
    if (!data) return;
    const stats = data.statistics || data.metadata?.statistics;
    if (!stats) return;
    elements.filesAnalyzed.textContent = stats.total_files || 0;
    elements.coveragePercent.textContent = `${(stats.coverage_percentage || 0).toFixed(1)}%`;
    elements.hldNodes.textContent = stats.business_nodes || stats.hld_nodes || 0;
    elements.lldNodes.textContent = stats.implementation_nodes || stats.lld_nodes || 0;
    elements.totalEdges.textContent = stats.total_edges || 0;
    
    elements.statsSection.style.display = 'block';
}

function updateComponentHealth(data) {
    if (!data) return;
    const stats = data.statistics || data.metadata?.statistics;
    if (!stats) return;
    
    // Calculate health metrics based on analysis data
    const codeQuality = calculateCodeQuality(stats);
    const complexity = calculateComplexity(stats);
    const dependencies = calculateDependencies(stats);
    
    elements.codeQuality.textContent = `${codeQuality.score}%`;
    elements.complexity.textContent = complexity.label;
    elements.dependencies.textContent = dependencies.label;
    
    // Update health indicators
    updateHealthIndicator('codeQuality', codeQuality.status);
    updateHealthIndicator('complexity', complexity.status);
    updateHealthIndicator('dependencies', dependencies.status);
    
    elements.healthSection.style.display = 'block';
}

function calculateCodeQuality(stats) {
    const coverage = stats.coverage_percentage || 0;
    const validationIssues = stats.validation_issues || 0;
    
    let score = Math.min(100, coverage - (validationIssues * 5));
    let status = 'healthy';
    
    if (score < 70) status = 'critical';
    else if (score < 85) status = 'warning';
    
    return { score: Math.max(0, Math.round(score)), status };
}

function calculateComplexity(stats) {
    const avgComplexity = stats.average_complexity || 1;
    let status = 'healthy';
    let label = 'Low';
    
    if (avgComplexity > 3) {
        status = 'critical';
        label = 'High';
    } else if (avgComplexity > 2) {
        status = 'warning';
        label = 'Medium';
    }
    
    return { status, label };
}

function calculateDependencies(stats) {
    const totalEdges = stats.total_edges || 0;
    const totalNodes = (stats.hld_nodes || 0) + (stats.lld_nodes || 0);
    const avgDeps = totalNodes > 0 ? totalEdges / totalNodes : 0;
    
    let status = 'healthy';
    let label = 'Balanced';
    
    if (avgDeps > 5) {
        status = 'critical';
        label = 'High';
    } else if (avgDeps > 3) {
        status = 'warning';
        label = 'Medium';
    }
    
    return { status, label };
}

function updateHealthIndicator(elementId, status) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const indicator = element.parentElement.querySelector('.health-indicator');
    if (!indicator) return;
    
    // Remove existing status classes
    indicator.classList.remove('healthy', 'warning', 'critical');
    
    // Add new status class
    indicator.classList.add(status);
}

function updateMetadata() {
    if (!currentGraphData?.metadata) return;
    
    const metadata = currentGraphData.metadata;
    elements.metadataContent.innerHTML = `
        <div class="metadata-item">
            <span class="metadata-label">Files</span>
            <span class="metadata-value">${metadata.file_count}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Coverage</span>
            <span class="metadata-value">${metadata.coverage_percentage}%</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Lines</span>
            <span class="metadata-value">${metadata.total_lines}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Languages</span>
            <span class="metadata-value">${metadata.languages.join(', ')}</span>
        </div>
    `;
    
    elements.metadataSection.style.display = 'block';
}

function addLog(message, level = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-message">${message}</span>
    `;
    
    elements.logsContent.appendChild(logEntry);
    elements.logsContent.scrollTop = elements.logsContent.scrollHeight;
} 