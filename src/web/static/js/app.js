// Global state
let currentAnalysisId = null;
let currentGraphData = null;
let currentViewMode = 'HLD';
let selectedNode = null;
let isProcessing = false;

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
    
    // Metadata
    metadataSection: document.getElementById('metadataSection'),
    metadataContent: document.getElementById('metadataContent'),
    
    // Logs
    logsContent: document.getElementById('logsContent'),
    
    // Graph
    graphTitle: document.getElementById('graphTitle'),
    nodeCount: document.getElementById('nodeCount'),
    edgeCount: document.getElementById('edgeCount'),
    graphContainer: document.getElementById('graphContainer'),
    emptyState: document.getElementById('emptyState'),
    
    // View toggle
    viewBtns: document.querySelectorAll('.view-btn'),
    
    // Node details
    nodeDetails: document.getElementById('nodeDetails'),
    nodeDetailsTitle: document.getElementById('nodeDetailsTitle'),
    nodeDetailsContent: document.getElementById('nodeDetailsContent'),
    closeNodeDetails: document.getElementById('closeNodeDetails'),
    
    // Toolbar buttons
    zoomOutBtn: document.getElementById('zoomOutBtn'),
    zoomInBtn: document.getElementById('zoomInBtn'),
    fitViewBtn: document.getElementById('fitViewBtn'),
    exportBtn: document.getElementById('exportBtn')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    addLog('Ready to analyze', 'info');
});

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
    
    // View toggle
    elements.viewBtns.forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
    
    // Export buttons
    elements.exportBtns.forEach(btn => {
        btn.addEventListener('click', () => handleExport(btn.dataset.format));
    });
    
    // Node details close
    elements.closeNodeDetails.addEventListener('click', closeNodeDetails);
    
    // Toolbar buttons
    elements.zoomOutBtn.addEventListener('click', () => zoomGraph(-0.1));
    elements.zoomInBtn.addEventListener('click', () => zoomGraph(0.1));
    elements.fitViewBtn.addEventListener('click', fitView);
    elements.exportBtn.addEventListener('click', () => handleExport('json'));
    
    // Graph container click to deselect
    elements.graphContainer.addEventListener('click', (e) => {
        if (e.target === elements.graphContainer) {
            closeNodeDetails();
        }
    });
}

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    elements.tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
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
    handleFileSelect({ target: { files: e.dataTransfer.files } });
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        addLog(`Selected file: ${files[0].name}`, 'info');
    }
}

// Analysis handling
async function handleAnalyze() {
    if (isProcessing) return;
    
    const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
    
    if (activeTab === 'upload') {
        const files = elements.fileInput.files;
        if (files.length === 0) {
            alert('Please select a file to upload');
            return;
        }
        await uploadFile(files[0]);
    } else if (activeTab === 'github') {
        const url = elements.githubUrl.value.trim();
        if (!url) {
            alert('Please enter a GitHub URL');
            return;
        }
        const branch = elements.githubBranch.value.trim() || 'main';
        await analyzeGithub(url, branch);
    }
}

async function uploadFile(file) {
    isProcessing = true;
    updateAnalyzeButton();
    showStatus('Uploading file...');
    addLog(`Uploading file: ${file.name}`, 'info');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/analysis/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAnalysisId = data.analysisId;
            addLog('File uploaded successfully', 'info');
            await pollAnalysisStatus();
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Upload error:', error);
        addLog(`Upload failed: ${error.message}`, 'error');
        hideStatus();
    } finally {
        isProcessing = false;
        updateAnalyzeButton();
    }
}

async function analyzeGithub(url, branch) {
    isProcessing = true;
    updateAnalyzeButton();
    showStatus('Analyzing GitHub repository...');
    addLog(`Analyzing GitHub repository: ${url} (branch: ${branch})`, 'info');
    
    try {
        const response = await fetch('/api/analysis/github', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url, branch })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentAnalysisId = data.analysisId;
            addLog('GitHub analysis started', 'info');
            await pollAnalysisStatus();
        } else {
            throw new Error(data.error || 'GitHub analysis failed');
        }
    } catch (error) {
        console.error('GitHub analysis error:', error);
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
        const status = await response.json();
        
        updateProgress(status.progress);
        updateStatusMessage(status.message);
        
        if (status.status === 'completed') {
            addLog('Analysis completed successfully', 'info');
            await loadGraphData();
            await loadAnalysisResponse();
            hideStatus();
        } else {
            // Poll again in 1 second
            setTimeout(pollAnalysisStatus, 1000);
        }
        
        // Update logs
        await updateLogs();
        
    } catch (error) {
        console.error('Status polling error:', error);
        addLog(`Status check failed: ${error.message}`, 'error');
        hideStatus();
    }
}

async function loadGraphData() {
    try {
        const response = await fetch(`/api/analysis/${currentAnalysisId}/graph`);
        currentGraphData = await response.json();
        renderGraph();
        updateMetadata();
    } catch (error) {
        console.error('Graph data loading error:', error);
        addLog(`Failed to load graph data: ${error.message}`, 'error');
    }
}

async function loadAnalysisResponse() {
    try {
        const response = await fetch(`/api/analysis/${currentAnalysisId}/response`);
        const data = await response.json();
        
        if (data.success) {
            showExportSection();
            addLog('Analysis response loaded', 'info');
        }
    } catch (error) {
        console.error('Analysis response loading error:', error);
        addLog(`Failed to load analysis response: ${error.message}`, 'error');
    }
}

async function updateLogs() {
    try {
        const response = await fetch(`/api/analysis/${currentAnalysisId}/logs`);
        const logs = await response.json();
        
        // Clear existing logs and add new ones
        elements.logsContent.innerHTML = '';
        logs.forEach(log => {
            addLogEntry(log.message, log.level, log.timestamp);
        });
    } catch (error) {
        console.error('Logs update error:', error);
    }
}

// Graph rendering
function renderGraph() {
    if (!currentGraphData) {
        showEmptyState();
        return;
    }
    
    hideEmptyState();
    
    // Filter nodes by current view mode
    const nodes = currentGraphData.nodes.filter(node => node.level === currentViewMode);
    const edges = currentGraphData.edges.filter(edge => {
        const sourceId = edge.from_node || edge.from;
        const targetId = edge.to_node || edge.to;
        const sourceExists = nodes.some(n => n.id === sourceId);
        const targetExists = nodes.some(n => n.id === targetId);
        return sourceExists && targetExists;
    });
    
    // Update stats
    elements.nodeCount.textContent = `${nodes.length} nodes`;
    elements.edgeCount.textContent = `${edges.length} connections`;
    
    // Clear existing nodes
    const existingNodes = elements.graphContainer.querySelectorAll('.graph-node');
    existingNodes.forEach(node => node.remove());
    
    // Simple grid layout for spacing
    const gridCols = Math.ceil(Math.sqrt(nodes.length));
    const gridSpacingX = 180;
    const gridSpacingY = 120;
    nodes.forEach((node, i) => {
        const col = i % gridCols;
        const row = Math.floor(i / gridCols);
        node.position = {
            x: 60 + col * gridSpacingX,
            y: 60 + row * gridSpacingY
        };
        const nodeElement = createNodeElement(node);
        elements.graphContainer.appendChild(nodeElement);
    });
    
    // Create edges (simple lines for now)
    createEdges(edges);
}

function createNodeElement(node) {
    const nodeElement = document.createElement('div');
    nodeElement.className = `graph-node ${node.level.toLowerCase()}`;
    nodeElement.dataset.nodeId = node.id;
    
    // Position the node
    const position = node.position || { x: Math.random() * 400 + 50, y: Math.random() * 300 + 50 };
    nodeElement.style.left = `${position.x}px`;
    nodeElement.style.top = `${position.y}px`;
    
    nodeElement.innerHTML = `
        <div class="graph-node-title">${node.name}</div>
        <div class="graph-node-type">${node.type}</div>
    `;
    
    nodeElement.addEventListener('click', () => selectNode(node));
    
    return nodeElement;
}

function createEdges(edges) {
    // For simplicity, we'll just create simple SVG lines
    // In a real implementation, you might want to use a proper graph library
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = '1';
    
    edges.forEach(edge => {
        const sourceNode = document.querySelector(`[data-node-id="${edge.from_node || edge.from}"]`);
        const targetNode = document.querySelector(`[data-node-id="${edge.to_node || edge.to}"]`);
        
        if (sourceNode && targetNode) {
            const sourceRect = sourceNode.getBoundingClientRect();
            const targetRect = targetNode.getBoundingClientRect();
            const containerRect = elements.graphContainer.getBoundingClientRect();
            
            const x1 = sourceRect.left + sourceRect.width / 2 - containerRect.left;
            const y1 = sourceRect.top + sourceRect.height / 2 - containerRect.top;
            const x2 = targetRect.left + targetRect.width / 2 - containerRect.left;
            const y2 = targetRect.top + targetRect.height / 2 - containerRect.top;
            
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', x1);
            line.setAttribute('y1', y1);
            line.setAttribute('x2', x2);
            line.setAttribute('y2', y2);
            line.setAttribute('stroke', '#e5e7eb');
            line.setAttribute('stroke-width', '2');
            
            svg.appendChild(line);
        }
    });
    
    // Remove existing SVG and add new one
    const existingSvg = elements.graphContainer.querySelector('svg');
    if (existingSvg) {
        existingSvg.remove();
    }
    elements.graphContainer.appendChild(svg);
}

// Node selection
function selectNode(node) {
    selectedNode = node;
    
    // Update node selection visual
    document.querySelectorAll('.graph-node').forEach(el => {
        el.classList.remove('selected');
    });
    
    const nodeElement = document.querySelector(`[data-node-id="${node.id}"]`);
    if (nodeElement) {
        nodeElement.classList.add('selected');
    }
    
    showNodeDetails(node);
}

function showNodeDetails(node) {
    elements.nodeDetailsTitle.textContent = node.name;
    
    const content = `
        <div class="detail-item">
            <div class="detail-label">Type</div>
            <div class="detail-value">${node.type}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Level</div>
            <div class="detail-value">${node.level}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Purpose</div>
            <div class="detail-value">${node.metadata?.purpose || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Complexity</div>
            <div class="detail-value">${node.metadata?.complexity || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Language</div>
            <div class="detail-value">${node.metadata?.language || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Line Count</div>
            <div class="detail-value">${node.metadata?.line_count || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Files</div>
            <div class="detail-value files">${(node.files || []).join('\n')}</div>
        </div>
    `;
    
    elements.nodeDetailsContent.innerHTML = content;
    elements.nodeDetails.style.display = 'flex';
}

function closeNodeDetails() {
    selectedNode = null;
    elements.nodeDetails.style.display = 'none';
    
    // Remove node selection visual
    document.querySelectorAll('.graph-node').forEach(el => {
        el.classList.remove('selected');
    });
}

// View switching
function switchView(view) {
    currentViewMode = view;
    
    // Update view buttons
    elements.viewBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // Update graph title
    elements.graphTitle.textContent = view === 'HLD' ? 'High-Level Design Graph' : 'Low-Level Design Graph';
    
    // Re-render graph
    if (currentGraphData) {
        renderGraph();
    }
    
    // Clear node selection
    closeNodeDetails();
}

// Export handling
async function handleExport(format) {
    try {
        const response = await fetch(`/api/download/${format}`);
        const data = await response.json();
        
        // For demo purposes, just show the download URL
        // In a real implementation, this would trigger an actual download
        alert(`Download ready: ${data.download_url}`);
        addLog(`Export requested: ${format.toUpperCase()}`, 'info');
        
    } catch (error) {
        console.error('Export error:', error);
        addLog(`Export failed: ${error.message}`, 'error');
    }
}

// Utility functions
function showStatus(message) {
    elements.statusSection.style.display = 'block';
    elements.statusMessage.textContent = message;
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

function showEmptyState() {
    elements.emptyState.style.display = 'block';
    elements.nodeCount.textContent = '0 nodes';
    elements.edgeCount.textContent = '0 connections';
}

function hideEmptyState() {
    elements.emptyState.style.display = 'none';
}

function addLog(message, level = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    addLogEntry(message, level, timestamp);
}

function addLogEntry(message, level, timestamp) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-message">${message}</span>
    `;
    
    elements.logsContent.appendChild(logEntry);
    elements.logsContent.scrollTop = elements.logsContent.scrollHeight;
}

// Graph controls (simplified)
function zoomGraph(delta) {
    // In a real implementation, this would zoom the graph
    console.log('Zoom:', delta);
}

function fitView() {
    // In a real implementation, this would fit the graph to view
    console.log('Fit view');
} 