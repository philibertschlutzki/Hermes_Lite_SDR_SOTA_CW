/**
 * Hermes-Lite 2 SDR SOTA & Digital Modes Web Cockpit
 * Touch-optimized for Android Tablet remote operation.
 */

// Helper selector
const $ = (id) => document.getElementById(id);

// System State
const state = {
  frequencyHz: 7030000,
  mode: "CWU",
  band: "40m",
  isTransmitting: false,
  isTuning: false,
  swr: 1.0,
  fwdPowerW: 0.0,
  audioContext: null,
  audioSocket: null,
  telemetrySocket: null,
  audioPlaying: false,
  wpm: 20,
};

// --- Initialization ---
window.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initBandSelector();
  initStepButtons();
  initPttAndTune();
  initCwControls();
  initWsjtxControls();
  initFldigiControls();
  initAudioStream();
  initThemeToggle();
  initTelemetryWebSocket();
  fetchInitialState();
});

// --- Tab Switching ---
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      tab.classList.add("active");
      const targetId = tab.dataset.tab;
      if ($(targetId)) $(targetId).classList.add("active");

      if (targetId === "tabLog") fetchLog();
      if (targetId === "tabHardware") fetchHardwareStatus();
    });
  });
}

// --- VFO Frequency & Band Controls ---
function formatFrequency(hz) {
  const s = hz.toString().padStart(7, "0");
  const mhz = s.slice(0, -6) || "0";
  const khz = s.slice(-6, -3);
  const hertz = s.slice(-3);
  return `${mhz}.${khz}.${hertz} <span class="unit">Hz</span>`;
}

function updateVfoDisplay() {
  $("vfoFrequency").innerHTML = formatFrequency(state.frequencyHz);
  $("vfoBand").textContent = state.band;
  $("vfoMode").textContent = state.mode;

  // Update active band button
  document.querySelectorAll(".btn-band").forEach((btn) => {
    btn.classList.toggle("active", btn.textContent.trim().toLowerCase() === state.band.toLowerCase());
  });
}

async function setFrequency(hz) {
  state.frequencyHz = Math.max(100000, Math.min(60000000, hz));
  updateVfoDisplay();
  try {
    const res = await fetch("/hl2/frequency", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hz: state.frequencyHz }),
    });
    const data = await res.json();
    if (data.band) state.band = data.band;
    updateVfoDisplay();
  } catch (e) {
    console.error("Set frequency error:", e);
  }
}

function initBandSelector() {
  document.querySelectorAll(".btn-band").forEach((btn) => {
    btn.addEventListener("click", () => {
      const freq = Number(btn.dataset.freq);
      if (freq) setFrequency(freq);
    });
  });
}

function initStepButtons() {
  $("btnStepDown1k").addEventListener("click", () => setFrequency(state.frequencyHz - 1000));
  $("btnStepDown100").addEventListener("click", () => setFrequency(state.frequencyHz - 100));
  $("btnStepUp100").addEventListener("click", () => setFrequency(state.frequencyHz + 100));
  $("btnStepUp1k").addEventListener("click", () => setFrequency(state.frequencyHz + 1000));
}

// --- PTT and ATU Tune ---
function initPttAndTune() {
  const btnPtt = $("btnPtt");
  btnPtt.addEventListener("click", async () => {
    const nextPtt = !state.isTransmitting;
    try {
      await fetch("/hl2/ptt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ptt: nextPtt }),
      });
      setPttState(nextPtt);
    } catch (e) {
      alert("PTT Fehler: " + e);
    }
  });

  const btnTune = $("btnAtuTune");
  btnTune.addEventListener("click", async () => {
    try {
      btnTune.classList.add("tuning");
      btnTune.textContent = "TUNING...";
      await fetch("/hardware/ioboard/atu/tune", { method: "POST" });
      setTimeout(() => {
        btnTune.classList.remove("tuning");
        btnTune.textContent = "TUNE ATU";
      }, 4000);
    } catch (e) {
      btnTune.classList.remove("tuning");
      btnTune.textContent = "TUNE ATU";
      alert("ATU Fehler: " + e);
    }
  });

  if ($("btnAtuBypass")) {
    $("btnAtuBypass").addEventListener("click", async () => {
      await fetch("/hardware/ioboard/atu/bypass", { method: "POST" });
      alert("ATU im Bypass-Modus.");
    });
  }
}

function setPttState(isTx) {
  state.isTransmitting = isTx;
  const btnPtt = $("btnPtt");
  btnPtt.classList.toggle("transmitting", isTx);
  btnPtt.textContent = isTx ? "TX ACTIVE" : "PTT (RX)";
}

// --- CW Cockpit ---
function initCwControls() {
  const wpmSlider = $("cwWpmSlider");
  wpmSlider.addEventListener("input", () => {
    state.wpm = Number(wpmSlider.value);
    $("wpmDisplay").textContent = state.wpm;
  });

  $("btnCwSendText").addEventListener("click", sendCwText);
  $("cwInputText").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendCwText();
    }
  });

  $("btnCwAbortText").addEventListener("click", async () => {
    await fetch("/cw/abort", { method: "POST" });
  });

  $("btnCwRxClear").addEventListener("click", async () => {
    await fetch("/cw/rx/clear", { method: "POST" });
    $("cwRxWindow").innerHTML = '<div class="terminal-placeholder">Puffer geleert...</div>';
  });

  // Macros
  document.querySelectorAll(".btn-macro[data-macro]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const macro = btn.dataset.macro;
      const inp = $("cwInputText");
      inp.value = inp.value ? `${inp.value} ${macro}` : macro;
      inp.focus();
    });
  });

  // Bot Controls
  $("btnBotToggle").addEventListener("click", async () => {
    const isRunning = $("botStateBadge").textContent !== "IDLE";
    const endpoint = isRunning ? "/bot/stop" : "/bot/start";
    await fetch(endpoint, { method: "POST" });
  });

  $("btnBotCq").addEventListener("click", async () => {
    await fetch("/bot/cq", { method: "POST" });
  });
}

async function sendCwText() {
  const text = $("cwInputText").value.trim();
  if (!text) return;

  const payload = {
    text: text,
    wpm: state.wpm,
    farnsworth_wpm: Number($("cwFarnsworth").value) || 0,
    ptt_lead_ms: Number($("cwPttLead").value) || 80,
    ptt_tail_ms: Number($("cwPttTail").value) || 120,
  };

  try {
    await fetch("/cw/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("cwInputText").value = "";
  } catch (e) {
    alert("CW Sendefehler: " + e);
  }
}

// --- WSJT-X (Weak Signal) ---
function initWsjtxControls() {
  $("btnWsjtxClear").addEventListener("click", async () => {
    await fetch("/wsjtx/clear", { method: "POST" });
    $("wsjtxDecodeBody").innerHTML = '<tr><td colspan="6" class="text-center muted">Liste geleert.</td></tr>';
  });

  $("btnWsjtxHalt").addEventListener("click", async () => {
    await fetch("/wsjtx/halt", { method: "POST" });
  });

  $("btnWsjtxCq").addEventListener("click", async () => {
    await fetch("/wsjtx/freetext", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "CQ", send: true }),
    });
  });
}

function renderWsjtxDecodes(decodes) {
  if (!decodes || decodes.length === 0) return;
  const tbody = $("wsjtxDecodeBody");
  tbody.innerHTML = "";

  decodes.forEach((d) => {
    const tr = document.createElement("tr");
    const isCq = d.is_cq || d.message.includes("CQ ");
    if (isCq) tr.classList.add("cq-highlight");

    tr.innerHTML = `
      <td>${d.time_str}</td>
      <td>${d.snr_db > 0 ? "+" + d.snr_db : d.snr_db}</td>
      <td>${d.delta_time_s}s</td>
      <td>${d.delta_freq_hz} Hz</td>
      <td><strong>${d.message}</strong></td>
      <td>
        <button class="btn-small btn-primary btn-reply">Antworten</button>
      </td>
    `;

    tr.querySelector(".btn-reply").addEventListener("click", async () => {
      await fetch("/wsjtx/reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(d),
      });
    });

    tbody.appendChild(tr);
  });
}

// --- PSK31 / RTTY Controls ---
function initFldigiControls() {
  const modemSelect = $("fldigiModemSelect");
  modemSelect.addEventListener("change", async () => {
    await fetch("/fldigi/modem", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modem: modemSelect.value }),
    });
  });

  $("btnPskSend").addEventListener("click", async () => {
    const text = $("pskTxInput").value;
    if (!text) return;
    await fetch("/fldigi/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    $("pskTxInput").value = "";
  });

  $("btnPskAbort").addEventListener("click", async () => {
    await fetch("/fldigi/abort", { method: "POST" });
  });

  $("btnPskClear").addEventListener("click", async () => {
    await fetch("/fldigi/clear", { method: "POST" });
    $("pskRxWindow").textContent = "";
  });

  document.querySelectorAll(".btn-macro[data-psk]").forEach((btn) => {
    btn.addEventListener("click", () => {
      $("pskTxInput").value = btn.dataset.psk;
    });
  });
}

// --- Live Audio Streaming to Tablet Speakers ---
function initAudioStream() {
  const btnToggle = $("btnAudioToggle");
  const volumeSlider = $("audioVolume");

  btnToggle.addEventListener("click", () => {
    if (state.audioPlaying) {
      stopAudio();
      btnToggle.textContent = "🔇 Audio Aus";
      btnToggle.classList.remove("btn-active");
    } else {
      startAudio();
      btnToggle.textContent = "🔊 RX Audio";
      btnToggle.classList.add("btn-active");
    }
  });

  volumeSlider.addEventListener("input", () => {
    const vol = volumeSlider.value / 100.0;
    fetch("/audio/volume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ volume: vol }),
    });
  });
}

function startAudio() {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  state.audioContext = new AudioCtx({ sampleRate: 48000 });
  state.audioPlaying = true;

  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${proto}//${window.location.host}/ws/audio`;
  state.audioSocket = new WebSocket(wsUrl);
  state.audioSocket.binaryType = "arraybuffer";

  let nextStartTime = state.audioContext.currentTime;

  state.audioSocket.onmessage = (event) => {
    if (!state.audioPlaying || !state.audioContext) return;
    const arrayBuffer = event.data;
    const int16Array = new Int16Array(arrayBuffer);
    const float32Array = new Float32Array(int16Array.length);

    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0;
    }

    const audioBuffer = state.audioContext.createBuffer(1, float32Array.length, 48000);
    audioBuffer.getChannelData(0).set(float32Array);

    const source = state.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(state.audioContext.destination);

    const now = state.audioContext.currentTime;
    if (nextStartTime < now) nextStartTime = now + 0.02;
    source.start(nextStartTime);
    nextStartTime += audioBuffer.duration;
  };

  state.audioSocket.onclose = () => {
    state.audioPlaying = false;
    $("btnAudioToggle").textContent = "🔇 Audio Aus";
  };
}

function stopAudio() {
  state.audioPlaying = false;
  if (state.audioSocket) state.audioSocket.close();
  if (state.audioContext) state.audioContext.close();
  state.audioSocket = null;
  state.audioContext = null;
}

// --- Outdoor Theme Toggle ---
function initThemeToggle() {
  const btn = $("btnThemeToggle");
  btn.addEventListener("click", () => {
    document.body.classList.toggle("outdoor-theme");
    const isOutdoor = document.body.classList.contains("outdoor-theme");
    btn.textContent = isOutdoor ? "🌙 Dunkel" : "☀️ Kontrast";
  });
}

// --- Real-Time Telemetry WebSocket ---
function initTelemetryWebSocket() {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${proto}//${window.location.host}/ws/telemetry`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "telemetry") {
        handleTelemetryUpdate(data);
      }
    } catch (e) {
      console.error("Telemetry parse error:", e);
    }
  };

  ws.onclose = () => {
    setTimeout(initTelemetryWebSocket, 2000);
  };
}

function handleTelemetryUpdate(data) {
  // Update SWR & Power
  state.swr = data.swr || 1.0;
  state.fwdPowerW = data.fwd_power_w || 0.0;
  $("fwdPowerVal").textContent = `${state.fwdPowerW.toFixed(1)} W`;
  const vswrEl = $("vswrVal");
  vswrEl.textContent = state.swr.toFixed(1);
  vswrEl.className = "meter-val " + (state.swr <= 1.5 ? "swr-safe" : state.swr <= 2.5 ? "swr-warn" : "swr-danger");

  // PTT State
  setPttState(data.transmitting);

  // CW RX text
  if (data.cw && data.cw.recent_text) {
    const rxBox = $("cwRxWindow");
    if (data.cw.recent_text.length > 0) {
      rxBox.textContent = data.cw.recent_text.join("\n");
      rxBox.scrollTop = rxBox.scrollHeight;
    }
  }

  // WSJT-X Status
  if (data.wsjtx) {
    $("wsjtxConnectedDot").classList.toggle("connected", data.wsjtx.connected);
    $("wsjtxStatusText").textContent = data.wsjtx.connected ? `WSJT-X: Verbunden (${data.wsjtx.mode})` : "WSJT-X: Getrennt";
    if (data.wsjtx.mode) $("wsjtxSubmode").textContent = data.wsjtx.mode;
  }

  // fldigi RX text
  if (data.fldigi && data.fldigi.recent_text) {
    $("pskRxWindow").textContent = data.fldigi.recent_text;
    $("fldigiTxState").textContent = data.fldigi.transmitting ? "TX" : "RX";
    $("fldigiTxState").style.background = data.fldigi.transmitting ? "var(--danger)" : "var(--bg-tertiary)";
  }
}

// --- Initial State Fetch ---
async function fetchInitialState() {
  try {
    const res = await fetch("/diag");
    const data = await res.json();
    if (data.hl2) {
      state.frequencyHz = data.hl2.freq_hz;
      state.mode = data.hl2.mode;
      state.band = data.hl2.band;
      updateVfoDisplay();
    }
    const logRes = await fetch("/log/count");
    const logData = await logRes.json();
    $("logCount").textContent = logData.count || 0;
  } catch (e) {
    console.debug("Initial state fetch:", e);
  }
}

async function fetchLog() {
  try {
    const res = await fetch("/log/export/csv");
    if (res.ok) {
      const text = await res.text();
      $("logContent").textContent = text;
    } else {
      $("logContent").textContent = "Keine QSOs im Logbuch gefunden.";
    }
  } catch (e) {
    $("logContent").textContent = "Fehler beim Laden des Logs.";
  }
}

async function fetchHardwareStatus() {
  try {
    const res = await fetch("/hardware/n2adr/status");
    const data = await res.json();
    $("hwBandName").textContent = data.band;
    $("hwLpfBit").textContent = `Relais-Bit ${data.lpf_relay_bit}`;
    $("hwHpfState").textContent = data.hpf_enabled ? "Aktiviert (Dämpft MW)" : "Bypass";
    $("hwRelayWord").textContent = data.relay_word;
  } catch (e) {
    console.error("Hardware fetch error:", e);
  }
}
