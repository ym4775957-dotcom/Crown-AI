document.addEventListener("DOMContentLoaded", () => {
    // API and WS endpoints
    const API_URL = window.location.origin;
    const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/logs`;

    // UI Elements
    const backendStatus = document.getElementById("backend-status");
    const wsIndicator = document.getElementById("ws-indicator");
    const wsStatus = document.getElementById("ws-status");
    const logsConsole = document.getElementById("logs-console");
    const clearLogsBtn = document.getElementById("clear-logs");
    const taskForm = document.getElementById("task-form");
    const taskInput = document.getElementById("task-input");
    const submitBtn = document.getElementById("submit-task");
    const outputContainer = document.getElementById("output-report-container");
    const calendarItemsList = document.getElementById("calendar-items-list");
    const mcpToolsGrid = document.getElementById("mcp-tools-grid");

    // Presets
    const mlPreset = document.getElementById("ml-preset");
    const algoPreset = document.getElementById("algo-preset");

    // Tab buttons
    const tabs = {
        report: { btn: document.getElementById("tab-report"), content: document.getElementById("content-report") },
        calendar: { btn: document.getElementById("tab-calendar"), content: document.getElementById("content-calendar") },
        mcp: { btn: document.getElementById("tab-mcp"), content: document.getElementById("content-mcp") },
        security: { btn: document.getElementById("tab-security"), content: document.getElementById("content-security") }
    };

    let ws = null;
    let reconnectInterval = 3000;

    // Initialize UI and check services
    checkBackendHealth();
    setupWebSocket();
    loadMCPTools();
    loadCalendar();

    // Tab Switching Logic
    Object.keys(tabs).forEach(key => {
        tabs[key].btn.addEventListener("click", () => {
            // Remove active classes
            Object.keys(tabs).forEach(k => {
                tabs[k].btn.classList.remove("active");
                tabs[k].content.classList.remove("active");
            });
            // Set current active
            tabs[key].btn.classList.add("active");
            tabs[key].content.classList.add("active");
        });
    });

    // Preset button event listeners
    mlPreset.addEventListener("click", () => {
        taskInput.value = "Create a daily study block schedule for my Machine Learning exam on Friday. Search for core ML topics like supervised learning and neural networks, optimize the study plan, and schedule times.";
    });

    algoPreset.addEventListener("click", () => {
        taskInput.value = "Design a time-blocked schedule for sorting algorithms study, search concepts in the knowledge base, optimize the steps, and register the events.";
    });

    // Clear logs console
    clearLogsBtn.addEventListener("click", () => {
        logsConsole.innerHTML = `<div class="log-row sys"><span class="log-timestamp">[System]</span> Log terminal cleared. Ready for next run.</div>`;
    });

    // Health Check Backend
    async function checkBackendHealth() {
        try {
            const res = await fetch(`${API_URL}/api/health`);
            if (res.ok) {
                backendStatus.textContent = "ONLINE";
                backendStatus.closest(".status-item").querySelector(".status-indicator").className = "status-indicator online";
            } else {
                throw new Error();
            }
        } catch (e) {
            backendStatus.textContent = "OFFLINE";
            backendStatus.closest(".status-item").querySelector(".status-indicator").className = "status-indicator offline";
        }
    }

    // Set up WebSocket log listener
    function setupWebSocket() {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            wsStatus.textContent = "CONNECTED";
            wsIndicator.className = "status-indicator online";
            appendLog("SYSTEM", "Real-time activity logs stream established successfully.", "SUCCESS");
        };

        ws.onmessage = (event) => {
            try {
                const log = JSON.parse(event.data);
                
                // Track agent active statuses
                if (log.level === "STATUS") {
                    updateAgentStatusUI(log.agent, log.message);
                } else {
                    appendLog(log.agent, log.message, log.level);
                }
            } catch (e) {
                console.error("Failed to parse socket message", e);
            }
        };

        ws.onclose = () => {
            wsStatus.textContent = "DISCONNECTED";
            wsIndicator.className = "status-indicator offline";
            appendLog("SYSTEM", "WebSocket disconnected. Reconnecting in 3s...", "WARNING");
            setTimeout(setupWebSocket, reconnectInterval);
        };

        ws.onerror = (e) => {
            console.error("WS connection error", e);
        };
    }

    // Append logs to terminal
    function appendLog(agent, message, level) {
        const time = new Date().toLocaleTimeString();
        const row = document.createElement("div");
        row.className = `log-row ${agent.toLowerCase().replace('_', '')} ${level.toLowerCase()}`;
        
        let prefix = `[${agent}]`;
        if (agent === "SecurityGuard") {
            prefix = `🛡️ [SecurityGuard]`;
        } else if (agent === "SYSTEM") {
            prefix = `⚙️ [System]`;
        }

        row.innerHTML = `<span class="log-timestamp">[${time}]</span> <strong style="color: inherit;">${prefix}</strong>: ${message}`;
        logsConsole.appendChild(row);
        logsConsole.scrollTop = logsConsole.scrollHeight;
    }

    // Update Agent Badges and glows in the UI
    function updateAgentStatusUI(agentName, statusMessage) {
        // Strip suffixes if Orchestrator_Start/End
        const cleanName = agentName.startsWith("Orchestrator") ? "Orchestrator" : agentName;
        const node = document.getElementById(`node-${cleanName}`);
        const badge = document.getElementById(`badge-${cleanName}`);
        
        if (!node || !badge) return;

        // Reset
        node.classList.remove("active-thinking");
        badge.className = "agent-badge";

        if (statusMessage.includes("RUNNING")) {
            node.classList.add("active-thinking");
            badge.classList.add("thinking");
            badge.textContent = "THINKING";
        } else if (statusMessage.includes("IDLE")) {
            badge.classList.add("idle");
            badge.textContent = "IDLE";
        } else if (statusMessage.includes("ERROR")) {
            badge.classList.add("idle");
            badge.textContent = "FAILED";
        }
    }

    // Fetch MCP tools
    async function loadMCPTools() {
        try {
            const res = await fetch(`${API_URL}/api/mcp-tools`);
            const data = await res.json();
            
            mcpToolsGrid.innerHTML = "";
            data.tools.forEach(tool => {
                const card = document.createElement("div");
                card.className = "tool-card";
                card.innerHTML = `
                    <div class="tool-header">
                        <h4>${tool.name}</h4>
                        <span class="tool-badge">MCP Tool</span>
                    </div>
                    <p>${tool.description}</p>
                    <div class="tool-args">
                        <span>Schema Expected Input</span>
                        <code>${JSON.stringify(tool.inputSchema.properties, null, 2)}</code>
                    </div>
                `;
                mcpToolsGrid.appendChild(card);
            });
        } catch (e) {
            mcpToolsGrid.innerHTML = `<p style="color: var(--error)">Failed to retrieve MCP tools schemas from backend.</p>`;
        }
    }

    // Fetch calendar events
    async function loadCalendar() {
        try {
            const res = await fetch(`${API_URL}/api/calendar`);
            if (res.ok) {
                const data = await res.json();
                calendarItemsList.innerHTML = "";
                if (data.length === 0) {
                    calendarItemsList.innerHTML = `
                        <div class="empty-state">
                            <div class="empty-icon"><i class="fa-solid fa-calendar-xmark"></i></div>
                            <h3>No Events Scheduled</h3>
                            <p>No study blocks or schedules have been booked yet.</p>
                        </div>
                    `;
                    return;
                }
                data.forEach(evt => {
                    const card = document.createElement("div");
                    card.className = "calendar-card";
                    card.innerHTML = `
                        <div class="calendar-details">
                            <h4>${evt.event}</h4>
                            <div class="calendar-time">
                                <i class="fa-solid fa-clock"></i>
                                <span>${evt.date} | ${evt.time}</span>
                            </div>
                        </div>
                        <span class="badge" style="background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3)">Registered</span>
                    `;
                    calendarItemsList.appendChild(card);
                });
            }
        } catch (e) {
            console.error("Failed to load calendar data", e);
        }
    }

    // Submit task form
    taskForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const prompt = taskInput.value.trim();
        if (!prompt) return;

        // Toggle UI loading state
        submitBtn.disabled = true;
        submitBtn.querySelector("span").textContent = "Executing Team...";
        submitBtn.querySelector("i").className = "fa-solid fa-spinner fa-spin";
        outputContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon"><i class="fa-solid fa-spinner fa-spin" style="color: var(--primary)"></i></div>
                <h3>Agents Collaborating...</h3>
                <p>Orchestration workflow active. Follow real-time activity updates in the log console.</p>
            </div>
        `;

        // Switch to report tab
        tabs.report.btn.click();

        try {
            const res = await fetch(`${API_URL}/api/execute`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt })
            });

            const data = await res.json();
            
            if (res.ok) {
                // Parse simple markdown returned into HTML tags
                outputContainer.innerHTML = parseMarkdownToHTML(data.final_report);
                appendLog("SYSTEM", "Workflow execution finished. Report successfully compiled.", "SUCCESS");
                
                // Refresh calendar items
                await loadCalendar();
            } else {
                throw new Error(data.detail || "Server returned an error");
            }

        } catch (err) {
            appendLog("SYSTEM", `Workflow failed: ${err.message}`, "ERROR");
            outputContainer.innerHTML = `
                <div class="empty-state" style="color: var(--error)">
                    <div class="empty-icon"><i class="fa-solid fa-circle-exclamation"></i></div>
                    <h3>Execution Failed</h3>
                    <p>${err.message}</p>
                </div>
            `;
        } finally {
            // Restore UI state
            submitBtn.disabled = false;
            submitBtn.querySelector("span").textContent = "Dispatch Agents";
            submitBtn.querySelector("i").className = "fa-solid fa-paper-plane";
            
            // Set all agent badges to idle
            ["Orchestrator", "Planner", "TaskOptimization", "Research", "ExamStudy", "LifeScheduler"].forEach(name => {
                updateAgentStatusUI(name, "IDLE");
            });
        }
    });

    // Helper Markdown parser
    function parseMarkdownToHTML(md) {
        if (!md) return "";
        let html = md;
        
        // Escape HTML tags to prevent XSS
        html = html
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Headers
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        
        // Horizontal Rules
        html = html.replace(/^---$/gim, '<hr>');

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

        // Bullet lists (simple replacement)
        html = html.replace(/^\s*-\s*(.*$)/gim, '<li>$1</li>');
        
        // Wrapping <li> tags in <ul>
        // This is a simple regex that wraps adjacent <li> items
        html = html.replace(/(<li>.*<\/li>)/gms, '<ul>$1</ul>');

        // Code backticks
        html = html.replace(/`(.*?)`/gim, '<code>$1</code>');

        // Line breaks
        html = html.replace(/\n$/gim, '<br>');

        return html;
    }
});
