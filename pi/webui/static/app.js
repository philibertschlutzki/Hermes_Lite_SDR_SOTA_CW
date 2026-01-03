async function apiFetch(base, path, options = {}) {
  const url = base.replace(/\/$/, "") + path;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let data = null;
  try { data = await res.json(); } catch (_) {}
  if (!res.ok) {
    throw new Error((data && JSON.stringify(data)) || ("HTTP " + res.status));
  }
  return data;
}

function $(id) { return document.getElementById(id); }

function apiBase() { return $("apiBase").value.trim() || "/api"; }

$("btnHealth").addEventListener("click", async () => {
  const out = $("healthOut");
  out.textContent = "...";
  try {
    const data = await apiFetch(apiBase(), "/health");
    out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = String(e);
  }
});

$("btnSetFreq").addEventListener("click", async () => {
  const hz = Number($("freqHz").value);
  try {
    await apiFetch(apiBase(), "/hl2/frequency", { method: "POST", body: JSON.stringify({ hz }) });
    alert("OK");
  } catch (e) {
    alert(String(e));
  }
});

$("btnSetMode").addEventListener("click", async () => {
  const mode = $("mode").value;
  try {
    await apiFetch(apiBase(), "/hl2/mode", { method: "POST", body: JSON.stringify({ mode }) });
    alert("OK");
  } catch (e) {
    alert(String(e));
  }
});

$("btnCwSend").addEventListener("click", async () => {
  const payload = {
    text: $("cwText").value,
    wpm: Number($("cwWpm").value),
    ptt_lead_ms: Number($("cwLead").value),
    ptt_tail_ms: Number($("cwTail").value),
  };
  const out = $("cwOut");
  out.textContent = "...";
  try {
    const data = await apiFetch(apiBase(), "/cw/send", { method: "POST", body: JSON.stringify(payload) });
    out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = String(e);
  }
});

$("btnCwAbort").addEventListener("click", async () => {
  const out = $("cwOut");
  out.textContent = "...";
  try {
    const data = await apiFetch(apiBase(), "/cw/abort", { method: "POST" });
    out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = String(e);
  }
});

$("btnCwStatus").addEventListener("click", async () => {
  const out = $("cwOut");
  out.textContent = "...";
  try {
    const data = await apiFetch(apiBase(), "/cw/status");
    out.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    out.textContent = String(e);
  }
});
