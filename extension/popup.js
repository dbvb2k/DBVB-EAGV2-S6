// Law Case Finder - Chrome Extension Popup JavaScript

class LawCaseFinder {
    constructor() {
        this.currentState = 'upload';
        this.extractedData = null;
        this.briefData = null;
        this.config = {
            primaryModel: 'gemini',
            fallbackModel: 'ollama',
            citationFormat: 'bluebook',
            consoleDetail: 'summary',
            autoGenerateBrief: false,
            serverUrl: 'http://localhost:3002'
        };
        
        // Agent tracking
        this.agents = {
            1: { name: 'Document Analysis', color: 'agent-1', status: 'idle' },
            2: { name: 'Brief Generator', color: 'agent-2', status: 'idle' },
            3: { name: 'Citation Normalizer', color: 'agent-3', status: 'idle' },
            4: { name: 'Legal Extractor', color: 'agent-4', status: 'idle' },
            5: { name: 'Case Retriever', color: 'agent-5', status: 'idle' }
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadConfig();
        this.showSection('upload');
    }

    consoleLog(message, type = 'info', agentId = null) {
        // Simple console logging for debugging
        const timestamp = new Date().toLocaleTimeString();
        const prefix = agentId ? `[Agent ${agentId}]` : '[LawCaseFinder]';
        console.log(`${timestamp} ${prefix} ${message}`);
        
        // Also log to the popup console if it exists
        if (typeof this.logToConsole === 'function') {
            this.logToConsole(message, type, agentId);
        }
    }

    setupEventListeners() {
        // Preference management
        const savePrefsBtn = document.getElementById('save-preferences-btn');
        const resetPrefsBtn = document.getElementById('reset-preferences-btn');
        
        if (savePrefsBtn) {
            savePrefsBtn.addEventListener('click', () => this.savePreferencesToServer());
        }
        
        if (resetPrefsBtn) {
            resetPrefsBtn.addEventListener('click', () => this.resetPreferences());
        }
        
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                if (tab) {
                    this.switchTab(tab);
                }
            });
        });

        // Brief tabs
        document.querySelectorAll('[data-brief-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.briefTab;
                if (tab) {
                    this.switchBriefTab(tab);
                }
            });
        });

        // File upload
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        dropZone.addEventListener('drop', this.handleDrop.bind(this));
        
        fileInput.addEventListener('change', this.handleFileSelect.bind(this));

        // Text analysis
        const textInput = document.getElementById('legal-text');
        const analyzeBtn = document.getElementById('analyze-text-btn');
        const clearBtn = document.getElementById('clear-text-btn');
        
        textInput.addEventListener('input', this.handleTextInput.bind(this));
        analyzeBtn.addEventListener('click', this.handleTextAnalysis.bind(this));
        clearBtn.addEventListener('click', this.clearTextInput.bind(this));

        // Action buttons
        document.getElementById('generate-brief-btn').addEventListener('click', () => this.generateBrief());
        document.getElementById('generate-brief-action-btn').addEventListener('click', () => this.generateBrief());
        document.getElementById('back-btn').addEventListener('click', () => this.showSection('upload'));
        document.getElementById('new-analysis-btn').addEventListener('click', () => this.showSection('upload'));
        document.getElementById('new-analysis-from-brief-btn').addEventListener('click', () => this.showSection('upload'));
        document.getElementById('new-analysis-action-btn').addEventListener('click', () => this.showSection('upload'));
        document.getElementById('back-to-results-btn').addEventListener('click', () => this.showSection('results'));
        document.getElementById('back-to-results-action-btn').addEventListener('click', () => this.showSection('results'));

        // Error handling
        document.getElementById('retry-btn').addEventListener('click', () => this.showSection('upload'));

        // Console functionality
        const consoleHeader = document.getElementById('console-header');
        const consoleExpandIcon = document.getElementById('console-expand-icon');
        const consoleClearBtn = document.getElementById('console-clear-btn');
        
        if (consoleHeader) {
            consoleHeader.addEventListener('click', () => this.toggleConsole());
        }
        
        if (consoleClearBtn) {
            consoleClearBtn.addEventListener('click', () => this.clearConsole());
        }

        // Console detail level setting
        document.querySelectorAll('input[name="consoleDetail"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.config.consoleDetail = e.target.value;
                this.saveConfig();
            });
        });

        // Config panel
        document.getElementById('config-header').addEventListener('click', this.toggleConfig.bind(this));
        
        // Config changes
        document.querySelectorAll('input[name="primaryModel"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.config.primaryModel = e.target.value;
                this.saveConfig();
            });
        });
        
        document.querySelectorAll('input[name="citationFormat"]').forEach(input => {
            input.addEventListener('change', (e) => {
                this.config.citationFormat = e.target.value;
                this.saveConfig();
            });
        });
        
        // Auto-generate brief checkbox - update config in real-time
        const autoGenerateCheckbox = document.querySelector('input[name="autoGenerateBrief"]');
        if (autoGenerateCheckbox) {
            autoGenerateCheckbox.addEventListener('change', (e) => {
                this.config.autoGenerateBrief = e.target.checked;
                this.saveConfig();
                this.consoleLog(`Auto-generate brief ${e.target.checked ? 'enabled' : 'disabled'}`, 'info');
            });
        }
    }

    // Tab Management
    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tab}-tab`).classList.add('active');
    }

    switchBriefTab(tab) {
        // Update brief tab buttons
        document.querySelectorAll('[data-brief-tab]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-brief-tab="${tab}"]`).classList.add('active');

        // Update brief content
        this.updateBriefContent(tab);
    }

    // Section Management
    showSection(sectionName) {
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${sectionName}-section`).classList.add('active');
        this.currentState = sectionName;
    }

    // File Upload Handling
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files && files.length > 0) {
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        if (!this.isValidFile(file)) {
            this.showError('Please upload a PDF or TXT file.');
            return;
        }

        this.analyzeDocument(file);
    }

    isValidFile(file) {
        const validTypes = ['application/pdf', 'text/plain'];
        const validExtensions = ['.pdf', '.txt'];
        
        return validTypes.includes(file.type) || 
               validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }

    // Text Input Handling
    handleTextInput(e) {
        const textValue = e.target.value;
        if (typeof textValue !== 'string') {
            console.error('Invalid text input value:', textValue);
            return;
        }
        
        const text = textValue;
        const charCount = text.length;
        const charCountEl = document.getElementById('char-count');
        const analyzeBtn = document.getElementById('analyze-text-btn');

        if (charCount < 100) {
            charCountEl.textContent = `${charCount} characters (${100 - charCount} more needed)`;
            charCountEl.className = 'char-count insufficient';
            analyzeBtn.disabled = true;
        } else {
            charCountEl.textContent = `${charCount} characters ✓`;
            charCountEl.className = 'char-count sufficient';
            analyzeBtn.disabled = false;
        }
    }

    handleTextAnalysis() {
        const textInput = document.getElementById('legal-text');
        if (!textInput) {
            this.showError('Text input element not found.');
            return;
        }
        
        const textValue = textInput.value;
        if (typeof textValue !== 'string') {
            this.showError('Invalid text input. Please try again.');
            return;
        }
        
        const text = textValue.trim();
        if (text.length < 100) {
            this.showError('Please enter at least 100 characters of legal text.');
            return;
        }

        this.analyzeText(text);
    }

    clearTextInput() {
        const textInput = document.getElementById('legal-text');
        const charCountEl = document.getElementById('char-count');
        const analyzeBtn = document.getElementById('analyze-text-btn');
        
        // Clear the textarea
        textInput.value = '';
        
        // Reset character count display
        charCountEl.textContent = '0 characters (100 more needed)';
        charCountEl.className = 'char-count insufficient';
        
        // Disable analyze button
        analyzeBtn.disabled = true;
        
        // Log to console
        this.logToConsole('🗑️ Text input cleared for new analysis', 'info');
        
        // Focus back to textarea for immediate input
        textInput.focus();
    }

    // API Communication
    async analyzeDocument(file) {
        this.showLoading('extracting');
        
        // Log to console
        this.logToConsole('🚀 Master Orchestrator starting analysis...', 'info');
        this.updateAgentStatus(1, 'running', 'Starting document analysis');
        
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:3002/api/analyze-document', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.handleAnalysisResult(result);
            
        } catch (error) {
            this.updateAgentStatus(1, 'error', error.message);
            this.logToConsole(`❌ Agent 1 failed: ${error.message}`, 'error', 1);
            this.showError(`Document analysis failed: ${error.message}`);
        }
    }

    async analyzeText(text) {
        // Validate input
        if (!text || typeof text !== 'string') {
            this.showError('Invalid text input provided.');
            return;
        }
        
        if (text.trim().length < 100) {
            this.showError('Text must be at least 100 characters long.');
            return;
        }
        
        this.showLoading('extracting');
        
        // Log to console
        this.logToConsole('🚀 Master Orchestrator starting analysis...', 'info');
        
        // First, get orchestration plan
        try {
            const orchestrationPlan = await this.getOrchestrationPlan(text);
            if (orchestrationPlan) {
                this.logToConsole(`📋 Orchestration Plan: ${orchestrationPlan.execution_sequence.join(' → ')}`, 'info');
                this.logToConsole(`🎯 Confidence: ${orchestrationPlan.confidence}`, 'info');
            }
        } catch (error) {
            this.logToConsole(`⚠️ Orchestration failed, using default sequence: ${error.message}`, 'warning');
        }
        
        this.updateAgentStatus(1, 'running', 'Starting document analysis');
        
        try {
            const response = await fetch('http://localhost:3002/api/analyze-document', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.handleAnalysisResult(result);
            
        } catch (error) {
            this.updateAgentStatus(1, 'error', error.message);
            this.logToConsole(`❌ Agent 1 failed: ${error.message}`, 'error', 1);
            this.showError(`Text analysis failed: ${error.message}`);
        }
    }

    async generateBrief() {
        if (!this.extractedData) {
            this.showError('No extracted data available for brief generation.');
            return;
        }

        this.showLoading('generating');
        
        // Log to console
        this.updateAgentStatus(2, 'running', 'Starting brief generation');
        
        try {
            const response = await fetch('http://localhost:3002/api/generate-brief', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ extracted_data: this.extractedData }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.handleBriefResult(result);
            
        } catch (error) {
            this.updateAgentStatus(2, 'error', error.message);
            this.logToConsole(`❌ Agent 2 failed: ${error.message}`, 'error', 2);
            this.showError(`Brief generation failed: ${error.message}`);
        }
    }

    // Result Handling
    async handleAnalysisResult(result) {
        if (result.success) {
            this.extractedData = result.data.extracted_fields;
            this.displayExtractionResults(result.data);
            this.showSection('results');
            
            // Log success to console
            this.updateAgentStatus(1, 'completed', 'Document analysis completed');
            this.logAgentResult(1, this.extractedData, this.config.consoleDetail);
            
            // Check if auto-generate brief is enabled
            await this.checkAutoGenerateBrief();
        } else {
            this.updateAgentStatus(1, 'error', result.error || 'Analysis failed');
            this.logToConsole(`❌ Agent 1 failed: ${result.error || 'Analysis failed'}`, 'error', 1);
            this.showError(result.error || 'Analysis failed');
        }
    }
    
    async checkAutoGenerateBrief() {
        try {
            console.log('🔍 checkAutoGenerateBrief() called');
            
            // Check preference from multiple sources (preference order)
            // 1. Check local config cache
            let isAutoGenerateEnabled = this.config.autoGenerateBrief;
            console.log('  Config value:', isAutoGenerateEnabled);
            
            // 2. Check UI checkbox state (most current)
            const autoGenerateCheckbox = document.querySelector('input[name="autoGenerateBrief"]');
            console.log('  Checkbox found:', !!autoGenerateCheckbox);
            
            if (autoGenerateCheckbox) {
                isAutoGenerateEnabled = autoGenerateCheckbox.checked;
                console.log('  Checkbox checked:', isAutoGenerateEnabled);
            }
            
            console.log('  Final decision - Auto-generate:', isAutoGenerateEnabled);
            
            if (isAutoGenerateEnabled) {
                this.consoleLog('✓ Auto-generate brief enabled - generating brief automatically...', 'info');
                
                // Small delay to let user see extraction results
                setTimeout(() => {
                    console.log('🚀 Triggering automatic brief generation...');
                    this.generateBrief();
                }, 800);
            } else {
                this.consoleLog('Auto-generate brief disabled - user can manually generate brief', 'info');
            }
        } catch (error) {
            console.error('Error checking auto-generate preference:', error);
        }
    }

    handleBriefResult(result) {
        if (result.success) {
            this.briefData = result.data.brief;
            this.displayBriefResults(result.data);
            this.showSection('brief');
            
            // Log success to console
            this.updateAgentStatus(2, 'completed', 'Brief generation completed');
            this.logAgentResult(2, this.briefData, this.config.consoleDetail);
        } else {
            this.updateAgentStatus(2, 'error', result.error || 'Brief generation failed');
            this.logToConsole(`❌ Agent 2 failed: ${result.error || 'Brief generation failed'}`, 'error', 2);
            this.showError(result.error || 'Brief generation failed');
        }
    }

    // UI Updates
    showLoading(step) {
        this.showSection('loading');
        
        const icon = document.getElementById('loading-icon');
        const title = document.getElementById('loading-title');
        const message = document.getElementById('loading-message');
        
        if (step === 'extracting') {
            icon.textContent = '🔍';
            title.textContent = 'Analyzing Document';
            message.textContent = 'Extracting legal information from your document...';
        } else if (step === 'generating') {
            icon.textContent = '📝';
            title.textContent = 'Generating Brief';
            message.textContent = 'Creating your comprehensive legal brief...';
        }
    }

    displayExtractionResults(data) {
        const resultsContent = document.getElementById('results-content');
        const confidenceIndicator = document.getElementById('confidence-indicator');
        const confidenceFill = document.getElementById('confidence-fill');
        const confidenceText = document.getElementById('confidence-text');

        // Update confidence indicator
        if (data.confidence_score !== undefined) {
            const confidence = data.confidence_score;
            const percentage = Math.round(confidence * 100);
            
            confidenceFill.style.width = `${percentage}%`;
            confidenceFill.style.backgroundColor = this.getConfidenceColor(confidence);
            confidenceText.textContent = `${this.getConfidenceLabel(confidence)} (${percentage}%)`;
            confidenceText.style.color = this.getConfidenceColor(confidence);
            confidenceIndicator.style.display = 'flex';
        }

        // Generate results HTML
        resultsContent.innerHTML = this.generateResultsHTML(data.extracted_fields);
        
        // Setup collapsible sections
        this.setupCollapsibleSections();
    }

    generateResultsHTML(data) {
        return `
            <div class="result-section">
                <div class="section-header" data-section="overview">
                    <h3>📖 Case Overview</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="section-content" id="overview-content">
                    <div class="field-group">
                        <div class="field">
                            <label>Case Name:</label>
                            <span class="field-text">${this.formatField(data.case_name)}</span>
                        </div>
                        <div class="field">
                            <label>Court:</label>
                            <span class="field-text">${this.formatField(data.court)}</span>
                        </div>
                        <div class="field">
                            <label>Date:</label>
                            <span class="field-text">${this.formatField(data.date)}</span>
                        </div>
                        <div class="field">
                            <label>Case Number:</label>
                            <span class="field-text">${this.formatField(data.case_number)}</span>
                        </div>
                        <div class="field">
                            <label>Judges:</label>
                            ${this.formatArrayField(data.judges, 'Not specified')}
                        </div>
                        <div class="field">
                            <label>Disposition:</label>
                            <span class="field-text">${this.formatField(data.disposition)}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="result-section">
                <div class="section-header" data-section="facts">
                    <h3>📋 Facts</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="section-content" id="facts-content">
                    <div class="field">
                        <span class="field-text">${this.formatField(data.facts, 'No factual background extracted')}</span>
                    </div>
                </div>
            </div>

            <div class="result-section">
                <div class="section-header" data-section="issues">
                    <h3>❓ Legal Issues</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="section-content" id="issues-content">
                    ${this.formatArrayField(data.legal_issues, 'No legal issues identified')}
                </div>
            </div>

            <div class="result-section">
                <div class="section-header" data-section="holdings">
                    <h3>⚖️ Holdings</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="section-content" id="holdings-content">
                    ${this.formatArrayField(data.holdings, 'No holdings extracted')}
                </div>
            </div>

            <div class="result-section">
                <div class="section-header" data-section="reasoning">
                    <h3>💭 Reasoning</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="section-content" id="reasoning-content">
                    ${this.formatArrayField(data.reasoning, 'No reasoning extracted')}
                </div>
            </div>

            <div class="result-section">
                <div class="section-header" data-section="citations">
                    <h3>📚 Citations</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="section-content" id="citations-content">
                    ${this.formatArrayField(data.citations, 'No citations found')}
                </div>
            </div>
        `;
    }

    displayBriefResults(data) {
        const briefContent = document.getElementById('brief-content');
        const briefConfidence = document.getElementById('brief-confidence');
        const briefWordCount = document.getElementById('brief-word-count');
        const briefCitationsCount = document.getElementById('brief-citations-count');

        // Update metrics
        briefConfidence.textContent = `${this.getConfidenceLabel(data.brief.confidence_score / 100)} (${data.brief.confidence_score}%)`;
        briefConfidence.style.color = this.getConfidenceColor(data.brief.confidence_score / 100);
        briefWordCount.textContent = data.brief.word_count || 0;
        briefCitationsCount.textContent = data.brief.key_citations ? data.brief.key_citations.length : 0;

        // Generate brief HTML
        briefContent.innerHTML = this.generateBriefHTML(data.brief);
    }

    generateBriefHTML(brief) {
        return `
            <div class="brief-section">
                <h3 class="section-title">📋 Issue</h3>
                <div class="section-content">
                    ${this.formatField(brief.issue, 'No issue statement generated')}
                </div>
            </div>

            <div class="brief-section">
                <h3 class="section-title">📖 Facts</h3>
                <div class="section-content">
                    ${this.formatField(brief.facts, 'No factual summary generated')}
                </div>
            </div>

            <div class="brief-section">
                <h3 class="section-title">⚖️ Holding</h3>
                <div class="section-content">
                    ${this.formatField(brief.holding, 'No holding statement generated')}
                </div>
            </div>

            <div class="brief-section">
                <h3 class="section-title">💭 Reasoning</h3>
                <div class="section-content">
                    ${this.formatArrayField(brief.reasoning, 'No reasoning points generated')}
                </div>
            </div>
        `;
    }

    updateBriefContent(tab) {
        const briefContent = document.getElementById('brief-content');
        
        if (tab === 'brief') {
            briefContent.innerHTML = this.generateBriefHTML(this.briefData);
        } else if (tab === 'citations') {
            briefContent.innerHTML = this.generateCitationsHTML();
            
            // Add event listener for copy all citations button
            const copyAllBtn = document.getElementById('copy-all-citations-btn');
            if (copyAllBtn) {
                copyAllBtn.addEventListener('click', () => this.copyAllCitations());
            }
            
            // Add event listeners for individual citation copy buttons
            const copyCitationBtns = document.querySelectorAll('.copy-citation-btn');
            copyCitationBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const citation = btn.getAttribute('data-citation');
                    navigator.clipboard.writeText(citation).then(() => {
                        // Visual feedback - briefly change button text
                        const originalText = btn.textContent;
                        btn.textContent = '✓';
                        setTimeout(() => {
                            btn.textContent = originalText;
                        }, 1000);
                    }).catch(err => {
                        console.error('Failed to copy citation:', err);
                        alert('Failed to copy citation');
                    });
                });
            });
        } else if (tab === 'export') {
            briefContent.innerHTML = this.generateExportHTML();
            
            // Add event listener for copy brief button
            const copyBriefBtn = document.getElementById('copy-brief-btn');
            if (copyBriefBtn) {
                copyBriefBtn.addEventListener('click', () => this.copyBrief());
            }
            
            // Add event listener for export TXT button
            const exportTxtBtn = document.getElementById('export-txt-btn');
            if (exportTxtBtn) {
                exportTxtBtn.addEventListener('click', () => this.exportBrief('txt'));
            }
        }
    }

    generateCitationsHTML() {
        if (!this.briefData || !this.briefData.key_citations) {
            return '<div class="empty-content">No citations were generated for this brief</div>';
        }

        const citations = this.briefData.key_citations.map((citation, index) => `
            <div class="citation-item">
                <div class="citation-number">${index + 1}</div>
                <div class="citation-text">${citation}</div>
                <button class="copy-citation-btn" data-citation="${this.escapeHtml(citation)}" title="Copy citation">📋</button>
            </div>
        `).join('');

        return `
            <div class="citations-header">
                <h3>📚 Key Citations</h3>
                <div class="citation-format-info">
                    Format: <strong>${this.config.citationFormat.toUpperCase()}</strong>
                </div>
            </div>
            <div class="citations-list">
                ${citations}
            </div>
            <div class="citations-actions">
                <button id="copy-all-citations-btn" class="action-btn secondary">
                    📋 Copy All Citations
                </button>
            </div>
        `;
    }

    generateExportHTML() {
        return `
            <h3>📤 Export Options</h3>
            <div class="export-formats">
                <div class="export-format">
                    <h4>📄 Text Format</h4>
                    <p>Export as plain text file with all sections</p>
                    <button id="export-txt-btn" class="export-btn">Download TXT</button>
                </div>
            </div>
            <div class="export-actions">
                <button id="copy-brief-btn" class="action-btn primary">📋 Copy Brief to Clipboard</button>
            </div>
        `;
    }

    // Utility Functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatField(value, emptyMessage = 'Not found') {
        if (!value || value === 'Not found' || (typeof value === 'string' && value.trim() === '')) {
            return `<span class="empty-field">${emptyMessage}</span>`;
        }
        return `<span class="field-text">${value}</span>`;
    }

    formatArrayField(items, emptyMessage = 'Not found') {
        if (!items || items.length === 0) {
            return `<span class="empty-field">${emptyMessage}</span>`;
        }
        
        const listItems = items.map(item => `<li>${item}</li>`).join('');
        return `<ul class="field-list">${listItems}</ul>`;
    }

    getConfidenceColor(score) {
        if (score >= 0.8) return '#28a745';
        if (score >= 0.6) return '#ffc107';
        return '#dc3545';
    }

    getConfidenceLabel(score) {
        if (score >= 0.8) return 'High';
        if (score >= 0.6) return 'Medium';
        return 'Low';
    }

    setupCollapsibleSections() {
        document.querySelectorAll('.section-header').forEach(header => {
            header.addEventListener('click', () => {
                const section = header.dataset.section;
                const content = document.getElementById(`${section}-content`);
                const icon = header.querySelector('.expand-icon');
                
                if (content.style.display === 'none') {
                    content.style.display = 'block';
                    icon.classList.add('expanded');
                } else {
                    content.style.display = 'none';
                    icon.classList.remove('expanded');
                }
            });
        });
    }

    showError(message) {
        document.getElementById('error-title').textContent = 'An Error Occurred';
        document.getElementById('error-message').textContent = message;
        this.showSection('error');
    }

    toggleConfig() {
        const content = document.getElementById('config-content');
        const icon = document.getElementById('config-expand-icon');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.textContent = '▼'; // Down arrow when expanded
        } else {
            content.style.display = 'none';
            icon.textContent = '▶'; // Right arrow when collapsed
        }
    }

    toggleConsole() {
        const content = document.getElementById('console-content');
        const icon = document.getElementById('console-expand-icon');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.textContent = '▼'; // Down arrow when expanded
        } else {
            content.style.display = 'none';
            icon.textContent = '▶'; // Right arrow when collapsed
        }
    }

    // Configuration Management
    async loadConfig() {
        // Load preferences from server
        try {
            const response = await fetch(`${this.config.serverUrl || 'http://localhost:3002'}/api/preferences`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.preferences) {
                    this.applyPreferencesToUI(data.preferences);
                    this.consoleLog('Preferences loaded from server', 'success');
                    return;
                }
            }
        } catch (error) {
            console.error('Failed to load preferences from server:', error);
        }
        
        // Fallback to local storage
        const saved = localStorage.getItem('lawCaseFinderConfig');
        if (saved) {
            this.config = { ...this.config, ...JSON.parse(saved) };
        }
        
        // Update UI
        const primaryModel = document.querySelector(`input[name="primaryModel"][value="${this.config.primaryModel}"]`);
        if (primaryModel) primaryModel.checked = true;
        
        const citationFormat = document.querySelector(`input[name="citationFormat"][value="${this.config.citationFormat}"]`);
        if (citationFormat) citationFormat.checked = true;
    }

    applyPreferencesToUI(preferences) {
        // General settings
        if (preferences.general) {
            const outputFormat = document.querySelector('select[name="outputFormat"]');
            if (outputFormat) outputFormat.value = preferences.general.output_format || 'plain_text';
            
            const language = document.querySelector('select[name="language"]');
            if (language) language.value = preferences.general.language || 'en';
            
            const verbosity = document.querySelector('select[name="verbosityLevel"]');
            if (verbosity) verbosity.value = preferences.general.verbosity_level || 'standard';
            
            const autoGenerate = document.querySelector('input[name="autoGenerateBrief"]');
            if (autoGenerate) autoGenerate.checked = preferences.general.auto_generate_brief || false;
        }
        
        // LLM settings
        if (preferences.llm) {
            const primaryModel = document.querySelector(`input[name="primaryModel"][value="${preferences.llm.primary_model}"]`);
            if (primaryModel) primaryModel.checked = true;
            
            const fallbackModel = document.querySelector('select[name="fallbackModel"]');
            if (fallbackModel) fallbackModel.value = preferences.llm.fallback_model || 'ollama';
            
            const enableFallback = document.querySelector('input[name="enableFallback"]');
            if (enableFallback) enableFallback.checked = preferences.llm.enable_fallback !== false;
        }
        
        // Citation settings
        if (preferences.citation) {
            const citationFormat = document.querySelector(`input[name="citationFormat"][value="${preferences.citation.format}"]`);
            if (citationFormat) citationFormat.checked = true;
            
            const includeCitations = document.querySelector('input[name="includeCitationsInBrief"]');
            if (includeCitations) includeCitations.checked = preferences.citation.include_citations_in_brief !== false;
            
            const normalizeCitations = document.querySelector('input[name="normalizeCitations"]');
            if (normalizeCitations) normalizeCitations.checked = preferences.citation.normalize_citations !== false;
        }
        
        // Privacy settings
        if (preferences.privacy) {
            const storeResults = document.querySelector('input[name="storeAnalysisResults"]');
            if (storeResults) storeResults.checked = preferences.privacy.store_analysis_results !== false;
            
            const storeDocuments = document.querySelector('input[name="storeDocuments"]');
            if (storeDocuments) storeDocuments.checked = preferences.privacy.store_documents || false;
        }
        
        // Update local config
        if (preferences.llm) this.config.primaryModel = preferences.llm.primary_model;
        if (preferences.citation) this.config.citationFormat = preferences.citation.format;
        if (preferences.general) this.config.autoGenerateBrief = preferences.general.auto_generate_brief || false;
    }

    async savePreferencesToServer() {
        this.consoleLog('Saving preferences to server...', 'info');
        
        try {
            // Collect all preferences from UI
            const preferences = {
                general: {
                    output_format: document.querySelector('select[name="outputFormat"]').value,
                    language: document.querySelector('select[name="language"]').value,
                    verbosity_level: document.querySelector('select[name="verbosityLevel"]').value,
                    auto_generate_brief: document.querySelector('input[name="autoGenerateBrief"]').checked
                },
                llm: {
                    primary_model: document.querySelector('input[name="primaryModel"]:checked').value,
                    fallback_model: document.querySelector('select[name="fallbackModel"]').value,
                    enable_fallback: document.querySelector('input[name="enableFallback"]').checked
                },
                citation: {
                    format: document.querySelector('input[name="citationFormat"]:checked').value,
                    include_citations_in_brief: document.querySelector('input[name="includeCitationsInBrief"]').checked,
                    normalize_citations: document.querySelector('input[name="normalizeCitations"]').checked
                },
                privacy: {
                    store_analysis_results: document.querySelector('input[name="storeAnalysisResults"]').checked,
                    store_documents: document.querySelector('input[name="storeDocuments"]').checked
                }
            };
            
            // Save to server for each category
            for (const [category, updates] of Object.entries(preferences)) {
                const response = await fetch(`${this.config.serverUrl || 'http://localhost:3002'}/api/preferences`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ category, updates })
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to save ${category} preferences`);
                }
            }
            
            // Also save to local storage as backup
            this.config.primaryModel = preferences.llm.primary_model;
            this.config.citationFormat = preferences.citation.format;
            localStorage.setItem('lawCaseFinderConfig', JSON.stringify(this.config));
            
            this.consoleLog('✓ Preferences saved successfully', 'success');
            alert('Preferences saved successfully!');
        } catch (error) {
            console.error('Failed to save preferences:', error);
            this.consoleLog('✗ Failed to save preferences: ' + error.message, 'error');
            alert('Failed to save preferences. Please try again.');
        }
    }

    async resetPreferences() {
        if (!confirm('Are you sure you want to reset all preferences to defaults?')) {
            return;
        }
        
        this.consoleLog('Resetting preferences to defaults...', 'info');
        
        try {
            const response = await fetch(`${this.config.serverUrl || 'http://localhost:3002'}/api/preferences`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.applyPreferencesToUI(data.preferences);
                    this.consoleLog('✓ Preferences reset to defaults', 'success');
                    alert('Preferences reset to defaults!');
                    return;
                }
            }
            
            throw new Error('Failed to reset preferences');
        } catch (error) {
            console.error('Failed to reset preferences:', error);
            this.consoleLog('✗ Failed to reset preferences: ' + error.message, 'error');
            alert('Failed to reset preferences. Please try again.');
        }
    }

    saveConfig() {
        localStorage.setItem('lawCaseFinderConfig', JSON.stringify(this.config));
    }

    // Export Functions
    exportBrief(format) {
        const briefText = this.formatBriefForExport();
        
        if (format === 'txt') {
            const blob = new Blob([briefText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `legal-brief-${Date.now()}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }

    copyBrief() {
        if (!this.briefData) {
            alert('No brief available to copy');
            return;
        }
        
        const briefText = this.formatBriefForExport();
        navigator.clipboard.writeText(briefText).then(() => {
            alert('Brief copied to clipboard!');
            this.consoleLog('Brief copied to clipboard', 'success');
        }).catch(err => {
            console.error('Failed to copy brief:', err);
            alert('Failed to copy brief. Please try again.');
            this.consoleLog('Failed to copy brief: ' + err.message, 'error');
        });
    }

    copyAllCitations() {
        if (!this.briefData || !this.briefData.key_citations) {
            alert('No citations available to copy');
            return;
        }
        
        // Format all citations as a numbered list
        const citationsText = this.briefData.key_citations
            .map((citation, index) => `${index + 1}. ${citation}`)
            .join('\n');
        
        navigator.clipboard.writeText(citationsText).then(() => {
            alert(`${this.briefData.key_citations.length} citations copied to clipboard!`);
        }).catch(err => {
            console.error('Failed to copy citations:', err);
            alert('Failed to copy citations. Please try again.');
        });
    }

    formatBriefForExport() {
        const sections = [
            `LEGAL BRIEF - ${this.briefData.metadata?.source_case || 'Case Analysis'}`,
            `Generated on: ${new Date().toLocaleDateString()}`,
            `Citation Format: ${this.config.citationFormat.toUpperCase()}`,
            '',
            '=' .repeat(60),
            '',
            'ISSUE:',
            this.briefData.issue || 'Not specified',
            '',
            'FACTS:',
            this.briefData.facts || 'Not specified',
            '',
            'HOLDING:',
            this.briefData.holding || 'Not specified',
            '',
            'REASONING:',
            ...(this.briefData.reasoning || []).map((reason, index) => `${index + 1}. ${reason}`),
            '',
            'KEY CITATIONS:',
            ...(this.briefData.key_citations || []).map((citation, index) => `${index + 1}. ${citation}`),
            '',
            '=' .repeat(60),
            `Word Count: ${this.briefData.word_count || 0}`,
            `Confidence Score: ${this.briefData.confidence_score || 0}%`,
            '',
            'DISCLAIMER: This brief is generated by AI for educational purposes only and does not constitute legal advice.'
        ];

        return sections.join('\n');
    }

    // Orchestration Methods
    async getOrchestrationPlan(text) {
        try {
            const userRequest = `Analyze this legal document and generate a comprehensive brief with citations: ${text.substring(0, 200)}...`;
            const currentContext = {
                has_document: true,
                document_type: 'legal_case',
                user_preferences: {
                    citation_format: this.config.citationFormat
                }
            };
            
            const response = await fetch('http://localhost:3002/api/orchestrate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_request: userRequest,
                    current_context: currentContext
                }),
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success && result.data && result.data.orchestration_plan) {
                return result.data.orchestration_plan;
            } else {
                throw new Error(result.error || 'Orchestration failed');
            }
        } catch (error) {
            console.error('Orchestration error:', error);
            throw error;
        }
    }

    // Console Methods
    logToConsole(message, type = 'info', agentId = null) {
        const consoleOutput = document.getElementById('console-output');
        if (!consoleOutput) return;

        const timestamp = new Date().toLocaleTimeString();
        const line = document.createElement('div');
        line.className = `console-line ${type}`;
        
        if (agentId && this.agents[agentId]) {
            line.classList.add(this.agents[agentId].color);
        }

        const timestampSpan = document.createElement('span');
        timestampSpan.className = 'console-timestamp';
        timestampSpan.textContent = `[${timestamp}]`;

        const textSpan = document.createElement('span');
        textSpan.className = 'console-text';
        textSpan.textContent = message;

        line.appendChild(timestampSpan);
        line.appendChild(textSpan);
        consoleOutput.appendChild(line);

        // Auto-scroll to bottom
        consoleOutput.scrollTop = consoleOutput.scrollHeight;
    }

    clearConsole() {
        const consoleOutput = document.getElementById('console-output');
        if (!consoleOutput) return;

        consoleOutput.innerHTML = `
            <div class="console-line console-info">
                <span class="console-timestamp">[${new Date().toLocaleTimeString()}]</span>
                <span class="console-text">🚀 Master Orchestrator initialized</span>
            </div>
            <div class="console-line console-info">
                <span class="console-timestamp">[${new Date().toLocaleTimeString()}]</span>
                <span class="console-text">Ready to process legal documents...</span>
            </div>
        `;
    }

    updateAgentStatus(agentId, status, message = '') {
        if (!this.agents[agentId]) return;

        this.agents[agentId].status = status;
        
        const statusEmoji = {
            'idle': '⏸️',
            'running': '🔄',
            'completed': '✅',
            'error': '❌'
        };

        const agentName = this.agents[agentId].name;
        const emoji = statusEmoji[status] || '❓';
        
        if (message) {
            this.logToConsole(`${emoji} Agent ${agentId}: ${agentName} - ${message}`, 'info', agentId);
        } else {
            this.logToConsole(`${emoji} Agent ${agentId}: ${agentName} - ${status}`, 'info', agentId);
        }
    }

    logAgentResult(agentId, result, detailLevel = 'summary') {
        if (!this.agents[agentId] || !result) return;

        const agentName = this.agents[agentId].name;
        this.logToConsole(`📊 Agent ${agentId}: ${agentName} Results:`, 'success', agentId);

        if (detailLevel === 'detailed') {
            // Log detailed results
            if (result.case_name) {
                this.logToConsole(`   📄 Case Name: ${result.case_name}`, 'info', agentId);
            }
            if (result.court) {
                this.logToConsole(`   🏛️ Court: ${result.court}`, 'info', agentId);
            }
            if (result.date) {
                this.logToConsole(`   📅 Date: ${result.date}`, 'info', agentId);
            }
            if (result.holdings) {
                this.logToConsole(`   ⚖️ Holdings: ${result.holdings.length} found`, 'info', agentId);
            }
            if (result.reasoning) {
                this.logToConsole(`   💭 Reasoning: ${result.reasoning.length} points`, 'info', agentId);
            }
            if (result.citations) {
                this.logToConsole(`   📚 Citations: ${result.citations.length} found`, 'info', agentId);
            }
            if (result.confidence_score) {
                this.logToConsole(`   🎯 Confidence: ${result.confidence_score}`, 'info', agentId);
            }
        } else {
            // Log summary results
            const summary = [];
            if (result.case_name) summary.push(`Case: ${result.case_name}`);
            if (result.confidence_score) summary.push(`Confidence: ${result.confidence_score}%`);
            if (result.word_count) summary.push(`Words: ${result.word_count}`);
            
            if (summary.length > 0) {
                this.logToConsole(`   📋 ${summary.join(' | ')}`, 'info', agentId);
            }
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LawCaseFinder();
});
