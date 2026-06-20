document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const els = {
        fractalImg: document.getElementById('fractal-img'),
        lblPos: document.getElementById('lbl-pos'),
        lblZoom: document.getElementById('lbl-zoom'),
        lblIter: document.getElementById('lbl-iter'),
        stateVal: document.getElementById('cognitive-state'),
        terminal: document.getElementById('terminal-logs'),
        wsStatus: document.getElementById('ws-status'),
        // Overrides
        chkOverride: document.getElementById('chk-override'),
        slidersBox: document.getElementById('sliders-container'),
        slideAtt: document.getElementById('slide-attention'),
        valAttS: document.getElementById('val-attention-slider'),
        slideEng: document.getElementById('slide-engagement'),
        valEngS: document.getElementById('val-engagement-slider'),
        slideWrk: document.getElementById('slide-workload'),
        valWrkS: document.getElementById('val-workload-slider'),
        // Metrics
        valAtt: document.getElementById('val-attention'),
        barAtt: document.getElementById('bar-attention'),
        valEng: document.getElementById('val-engagement'),
        barEng: document.getElementById('bar-engagement'),
        valWork: document.getElementById('val-workload'),
        barWork: document.getElementById('bar-workload'),
        // Fractal Nav
        fractalContainer: document.getElementById('fractal-container'),
        // Coalition
        netContainer: document.getElementById('network-container'),
        btnAdd: document.getElementById('btn-add-agent'),
        btnRem: document.getElementById('btn-rem-agent'),
        // Voice & Narrative
        btnMic: document.getElementById('btn-mic'),
        lblVoice: document.getElementById('voice-status'),
        lblNarrative: document.getElementById('narrative-output'),
        lblPrompt: document.getElementById('prompt-output')
    };

    let ws = null;
    let network = null;
    let fractalState = { x: -0.5, y: 0.0, zoom: 1.0 };
    let fractalUpdateTimer = null;

    function addLog(msg) {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false });
        const div = document.createElement('div');
        div.className = 'log-entry';
        div.innerHTML = `<span class="log-time">[${time}]</span> ${msg}`;
        els.terminal.appendChild(div);
        els.terminal.scrollTop = els.terminal.scrollHeight;
        while (els.terminal.children.length > 50) els.terminal.removeChild(els.terminal.firstChild);
    }

    function initWebSocket() {
        ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = () => {
            els.wsStatus.innerText = "Connected";
            els.wsStatus.style.color = "var(--primary)";
            addLog("WebSocket connection established");
            ws.send(JSON.stringify({ action: "get_coalition" }));
            updateFractalImage(); // Trigger first load
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === "cognitive_state") {
                updateMetricsUI(msg.data);
            } else if (msg.type === "coalition_update") {
                updateNetwork(msg.data);
            }
        };

        ws.onclose = () => {
            els.wsStatus.innerText = "Disconnected";
            els.wsStatus.style.color = "var(--warn)";
            addLog("WebSocket disconnected. Retrying in 2s...");
            setTimeout(initWebSocket, 2000);
        };
    }

    function updateMetricsUI(data) {
        // Progress Bars
        els.valAtt.innerText = data.attention.toFixed(2);
        els.barAtt.style.width = `${data.attention * 100}%`;
        els.valEng.innerText = data.engagement.toFixed(2);
        els.barEng.style.width = `${data.engagement * 100}%`;
        els.valWork.innerText = data.workload.toFixed(2);
        els.barWork.style.width = `${data.workload * 100}%`;

        // State Text
        const stateStr = data.state.replace('_', ' ').toUpperCase();
        if (els.stateVal.innerText !== stateStr) {
            els.stateVal.innerText = stateStr;
            let color = 'var(--primary)';
            if (data.state.includes('focused')) color = 'var(--accent)';
            if (data.state.includes('fatigued') || data.state.includes('stressed')) color = 'var(--warn)';
            els.stateVal.style.color = color;
            els.stateVal.style.textShadow = `0 0 10px ${color}`;
            addLog(`Cognitive shift -> ${stateStr}`);
        }

        // Overlay Stats
        els.lblIter.innerText = data.iterations;

        // Dynamic Narrative & Image Prompts
        if (data.narrative) {
            els.lblNarrative.innerText = data.narrative;
        }
        if (data.image_prompt) {
            els.lblPrompt.innerText = data.image_prompt;
        }

        // If not in manual override, keep sliders synced to simulate feedback
        if (!els.chkOverride.checked) {
            els.slideAtt.value = data.attention;
            els.valAttS.innerText = data.attention.toFixed(2);
            els.slideEng.value = data.engagement;
            els.valEngS.innerText = data.engagement.toFixed(2);
            els.slideWrk.value = data.workload;
            els.valWrkS.innerText = data.workload.toFixed(2);
        }
    }

    function updateNetwork(data) {
        const nodes = new vis.DataSet(data.nodes);
        const edges = new vis.DataSet(data.edges);
        
        if (!network) {
            const options = {
                nodes: { shape: 'dot', size: 16, font: { color: '#ffffff', size: 12, face: 'JetBrains Mono' }, borderWidth: 2 },
                edges: { width: 2, color: { color: 'rgba(255,255,255,0.2)' } },
                groups: {
                    coalition: { color: { background: '#ff0055', border: '#ffffff' } },
                    human: { color: { background: '#00f0ff', border: '#ffffff' } },
                    ai_agent: { color: { background: '#aa00ff', border: '#ffffff' } },
                    edge_node: { color: { background: '#ffb800', border: '#ffffff' } },
                    cloud_node: { color: { background: '#00ffaa', border: '#ffffff' } }
                },
                physics: { stabilization: false, barnesHut: { springLength: 100 } }
            };
            network = new vis.Network(els.netContainer, { nodes, edges }, options);
        } else {
            network.setData({ nodes, edges });
        }
        addLog(`Coalitions mapped: ${nodes.length} nodes, ${edges.length} edges`);
    }

    // --- FRACTAL NAVIGATION ---
    function updateFractalImage() {
        const ts = new Date().getTime();
        els.fractalImg.src = `/api/fractal?x=${fractalState.x}&y=${fractalState.y}&zoom=${fractalState.zoom}&t=${ts}`;
        els.lblPos.innerText = `${fractalState.x.toFixed(2)}, ${fractalState.y.toFixed(2)}`;
        els.lblZoom.innerText = `${fractalState.zoom.toFixed(2)}x`;
    }

    function queueFractalUpdate() {
        if (fractalUpdateTimer) clearTimeout(fractalUpdateTimer);
        // Throttle updates to ~10fps
        fractalUpdateTimer = setTimeout(updateFractalImage, 100);
    }

    // Drag to pan
    let isDragging = false;
    let lastMousePos = { x: 0, y: 0 };
    els.fractalContainer.addEventListener('mousedown', (e) => {
        isDragging = true;
        lastMousePos = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener('mouseup', () => { isDragging = false; });
    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - lastMousePos.x;
        const dy = e.clientY - lastMousePos.y;
        lastMousePos = { x: e.clientX, y: e.clientY };
        
        // Pan sensitivity inversely proportional to zoom
        const sensitivity = 0.005 / fractalState.zoom;
        fractalState.x -= dx * sensitivity;
        fractalState.y -= dy * sensitivity; // canvas y is down, complex plane y is up (depends on renderer)
        queueFractalUpdate();
    });

    // Scroll to zoom
    els.fractalContainer.addEventListener('wheel', (e) => {
        e.preventDefault();
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
        fractalState.zoom *= zoomFactor;
        queueFractalUpdate();
    });

    // --- CONTROLS ---
    els.chkOverride.addEventListener('change', (e) => {
        const isOverride = e.target.checked;
        els.slidersBox.style.opacity = isOverride ? 1 : 0.5;
        els.slidersBox.style.pointerEvents = isOverride ? 'auto' : 'none';
        ws.send(JSON.stringify({ action: "toggle_override", value: isOverride }));
        addLog(`Manual Override: ${isOverride ? 'ENABLED' : 'DISABLED'}`);
    });

    function bindSlider(slider, lbl, metricName) {
        slider.addEventListener('input', (e) => {
            lbl.innerText = parseFloat(e.target.value).toFixed(2);
            ws.send(JSON.stringify({ action: "set_metric", metric: metricName, value: e.target.value }));
        });
    }
    bindSlider(els.slideAtt, els.valAttS, 'attention');
    bindSlider(els.slideEng, els.valEngS, 'engagement');
    bindSlider(els.slideWrk, els.valWrkS, 'workload');

    els.btnAdd.addEventListener('click', () => {
        ws.send(JSON.stringify({ action: "add_agent", type: "ai_agent" }));
    });
    els.btnRem.addEventListener('click', () => {
        ws.send(JSON.stringify({ action: "remove_agent" }));
    });

    // --- BROWSER VOICE RECOGNITION ---
    let recognition = null;
    let isListening = false;
    let speechStartTime = 0;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-MX'; // Native Spanish support for ESCOM

        recognition.onstart = () => {
            isListening = true;
            speechStartTime = Date.now();
            els.btnMic.classList.add('listening');
            els.lblVoice.innerText = "Listening to voice waves... Speak now!";
            els.lblVoice.classList.add('active');
            addLog("Speech recognition session started");
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            const elapsedSeconds = (Date.now() - speechStartTime) / 1000.0;
            els.lblVoice.innerText = `Heard: "${transcript}"`;
            addLog(`Speech captured: "${transcript}" in ${elapsedSeconds.toFixed(1)}s`);
            
            // Send voice input command to backend
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    action: "voice_input",
                    text: transcript,
                    time_taken: elapsedSeconds
                }));
                // Auto toggle manual override to show feedback
                if (!els.chkOverride.checked) {
                    els.chkOverride.checked = true;
                    // Trigger visual change for manual override box
                    els.slidersBox.style.opacity = 1;
                    els.slidersBox.style.pointerEvents = 'auto';
                }
            }
        };

        recognition.onerror = (event) => {
            console.error(event.error);
            els.lblVoice.innerText = `Voice Error: ${event.error}`;
            addLog(`Speech recognition error: ${event.error}`);
            resetMicState();
        };

        recognition.onend = () => {
            resetMicState();
        };
    } else {
        els.lblVoice.innerText = "Web Speech API is not supported in this browser.";
        els.btnMic.disabled = true;
        els.btnMic.style.opacity = 0.5;
    }

    function resetMicState() {
        isListening = false;
        els.btnMic.classList.remove('listening');
        els.lblVoice.classList.remove('active');
        if (els.lblVoice.innerText.startsWith("Listening")) {
            els.lblVoice.innerText = "Click mic to start voice tracking...";
        }
    }

    els.btnMic.addEventListener('click', () => {
        if (!recognition) return;
        if (isListening) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    // Loop
    // The server is pushing state updates, but we need a heartbeat for the fractal image
    setInterval(updateFractalImage, 1000); 

    // Init
    addLog("FCSTN Interactive Control Center Initializing...");
    initWebSocket();
});
