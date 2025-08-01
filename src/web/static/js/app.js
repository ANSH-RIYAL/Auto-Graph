// Global state
let currentAnalysisId = null;
let currentGraphData = null;
let currentDepth = 1;
let currentViewMode = 'HIERARCHY';
let selectedNode = null;
let isProcessing = false;
let cy = null;

// Color mapping for HLD modules
const moduleColors = {
    'module_service_layer': '#9013FE',
    'module_utilities': '#D0021B', 
    'module_other': '#4A90E2',
    'frontend_module': '#4CAF50',
    'backend_module': '#2196F3',
    'database_module': '#FF9800'
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
                    'color': '#000000',
                    'border-width': 2,
                    'border-color': '#333333',
                    'shape': 'roundrectangle',
                    'width': 120,
                    'height': 60,
                    'font-size': '11px',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px'
                }
            },
            {
                selector: 'node[level = "HLD"]',
                style: {
                    'border-width': 4,
                    'border-color': '#000000',
                    'width': 150,
                    'height': 80,
                    'font-size': '13px',
                    'font-weight': 'bold'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 3,
                    'line-color': '#666666',
                    'target-arrow-color': '#666666',
                    'target-arrow-shape': 'triangle',
                    'source-arrow-color': 'data(sourceArrowColor)',
                    'source-arrow-shape': 'data(sourceArrowShape)',
                    'curve-style': 'bezier',
                    'content': 'data(label)',
                    'font-size': '10px',
                    'text-rotation': 'autorotate',
                    'text-margin-y': -12,
                    'text-background-color': 'white',
                    'text-background-opacity': 0.8,
                    'text-background-padding': 2
                }
            },
            {
                selector: 'edge[bidirectional = "true"]',
                style: {
                    'source-arrow-shape': 'triangle',
                    'source-arrow-color': '#666666'
                }
            }
        ],
        layout: { name: 'preset' }
    });

    // Add event listeners for Cytoscape
    cy.on('tap', 'node', function(evt) {
        const node = evt.target;
        selectNode(node.data());
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
    if (!currentGraphData) return;
    
    const elements = [];
    
    // Filter nodes by technical depth
    const filteredNodes = currentGraphData.nodes.filter(node => {
        const nodeDepth = node.metadata?.technical_depth || (node.level === 'HLD' ? 1 : 3);
        return nodeDepth <= currentDepth;
    });
    
    if (currentViewMode === 'HIERARCHY') {
        // Show hierarchical view based on depth
        if (currentDepth === 1) {
            // Business level - show only HLD nodes
            const hldNodes = filteredNodes.filter(node => node.level === 'HLD');
            hldNodes.forEach((node, index) => {
                elements.push({
                    data: {
                        id: node.id,
                        label: node.name || node.id,
                        type: node.type,
                        level: node.level,
                        color: node.metadata?.color || moduleColors[node.id] || '#f0f0f0'
                    },
                    position: {
                        x: 200 + (index * 350),
                        y: 200
                    }
                });
            });
        } else {
            // System/Implementation levels - show hierarchy
            const hldNodes = filteredNodes.filter(node => node.level === 'HLD');
            const lldNodes = filteredNodes.filter(node => node.level === 'LLD');
        
            // Add HLD nodes at top level
            hldNodes.forEach((node, index) => {
                elements.push({
                    data: {
                        id: node.id,
                        label: node.name || node.id,
                        type: node.type,
                        level: node.level,
                        color: node.metadata?.color || moduleColors[node.id] || '#f0f0f0'
                    },
                    position: {
                        x: 200 + (index * 400),
                        y: 100
                    }
                });
            });
        
            // Group LLD nodes by parent module and position them below
            const moduleGroups = {};
            
            lldNodes.forEach(node => {
                const parentModule = getNodeParentModule(node);
                const parentColor = node.metadata?.color || moduleColors[parentModule] || '#f0f0f0';
                
                if (!moduleGroups[parentModule]) {
                    moduleGroups[parentModule] = [];
                }
                
                moduleGroups[parentModule].push({
                    data: {
                        id: node.id,
                        label: node.name || node.id,
                        type: node.type,
                        level: node.level,
                        color: parentColor,
                        parent: parentModule
                    }
                });
            });
            
            // Position LLD nodes in columns under their parent modules
            Object.keys(moduleGroups).forEach((moduleId, moduleIndex) => {
                const group = moduleGroups[moduleId];
                group.forEach((node, nodeIndex) => {
                    node.position = {
                        x: 150 + (moduleIndex * 400) + ((nodeIndex % 2) * 100),
                        y: 250 + (Math.floor(nodeIndex / 2) * 120)
                    };
                    elements.push(node);
                });
            });
            
            // Add hierarchy edges from HLD to LLD (only at depth 2+)
            if (currentDepth >= 2) {
                lldNodes.forEach(lldNode => {
                    const parentModule = getNodeParentModule(lldNode);
                    elements.push({
                        data: {
                            id: `hierarchy-${parentModule}-${lldNode.id}`,
                            source: parentModule,
                            target: lldNode.id
                        }
                    });
                });
            }
        }
    } else if (currentViewMode === 'CONNECTIONS') {
        // Show all filtered nodes with full connection view
        filteredNodes.forEach(node => {
            const parentModule = getNodeParentModule(node);
            const nodeColor = node.metadata?.color || moduleColors[node.id] || moduleColors[parentModule] || '#f0f0f0';
            
            elements.push({
                data: {
                    id: node.id,
                    label: node.name || node.id,
                    type: node.type,
                    level: node.level,
                    color: nodeColor
                }
            });
        });
        
        // Add edges with bidirectional arrows and communication labels
        const addedEdges = new Set();
        const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
        
        currentGraphData.edges.forEach(edge => {
            // Only show edges between filtered nodes
            if (!filteredNodeIds.has(edge.from_node) || !filteredNodeIds.has(edge.to_node)) {
                return;
            }
            
            const edgeKey = `${edge.from_node}-${edge.to_node}`;
            const reverseKey = `${edge.to_node}-${edge.from_node}`;
            
            if (!addedEdges.has(edgeKey) && !addedEdges.has(reverseKey)) {
                const isBidirectional = edge.metadata?.bidirectional === true;
                const commType = edge.metadata?.communication_type || edge.metadata?.relationship_type || edge.type || '';
                
                elements.push({
                    data: {
                        id: edge.id || edgeKey,
                        source: edge.from_node,
                        target: edge.to_node,
                        label: commType,
                        bidirectional: isBidirectional,
                        sourceArrowColor: isBidirectional ? '#666666' : 'transparent',
                        sourceArrowShape: isBidirectional ? 'triangle' : 'none'
                    }
                });
                addedEdges.add(edgeKey);
            }
        });
    }
    
    // Update graph
    cy.elements().remove();
    cy.add(elements);
    
    // Choose layout based on view mode
    if (currentViewMode === 'HIERARCHY') {
        // Use preset layout since we're setting positions manually
        cy.layout({
            name: 'preset',
            padding: 50
        }).run();
    } else {
        // Use force-directed layout for connections view
        cy.layout({
            name: 'cose',
            idealEdgeLength: 120,
            nodeOverlap: 30,
            refresh: 20,
            fit: true,
            padding: 50,
            randomize: false,
            componentSpacing: 150,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000
        }).run();
    }
    
    setTimeout(() => cy.fit(), 300);
    
    // Update statistics
    updateGraphStats();
    updatePMDashboard();
}

// Update graph statistics
function updateGraphStats() {
    if (!currentGraphData) return;
    
    const filteredNodes = currentGraphData.nodes.filter(node => {
        const nodeDepth = node.metadata?.technical_depth || (node.level === 'HLD' ? 1 : 3);
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
    switch(currentDepth) {
        case 1: return 'Business View';
        case 2: return 'System View';
        case 3: return 'Implementation View';
        default: return 'Unknown';
    }
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
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFile(file) {
    if (file.type === 'application/zip' || file.name.endsWith('.zip')) {
        uploadFile(file);
    } else {
        addLog('Please select a ZIP file', 'error');
    }
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
        await uploadFile(files[0]);
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

async function uploadFile(file) {
    if (isProcessing) return;
    
    isProcessing = true;
    updateAnalyzeButton();
    showStatus('Uploading file...');
    
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
        const response = await fetch(`/api/analysis/${currentAnalysisId}/graph`);
        currentGraphData = await response.json();
        
        // Show graph
        elements.emptyState.style.display = 'none';
        elements.cy.style.display = 'block';
        
        // Display graph with current settings
        displayGraph();
        
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

function showNodeDetails(node) {
    elements.nodeDetailsTitle.textContent = node.name || node.id;
    
    const details = [];
    details.push(`<div class="detail-item"><span class="detail-label">Type:</span> <span class="detail-value">${node.type}</span></div>`);
    details.push(`<div class="detail-item"><span class="detail-label">Level:</span> <span class="detail-value">${node.level}</span></div>`);
    
    if (node.metadata?.purpose) {
        details.push(`<div class="detail-item"><span class="detail-label">Purpose:</span> <span class="detail-value">${node.metadata.purpose}</span></div>`);
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