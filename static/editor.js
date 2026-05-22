let state = null;
let previewBlobUrl = null;
let previewTimer = null;
let previewRequestId = 0;

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function collectData() {
  const info_rows = [...document.querySelectorAll(".info-row")].map((row) => ({
    label: row.querySelector(".info-label").value.trim(),
    value: row.querySelector(".info-value").value.trim(),
  })).filter((r) => r.label || r.value);

  const sections = [...document.querySelectorAll(".section-block")].map((block) => ({
    title: block.querySelector(".sec-title").value.trim(),
    items: block.querySelector(".sec-items").value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean),
  })).filter((s) => s.title || s.items.length);

  const scale = parseInt(document.getElementById("lineSpacing").value, 10) / 100;

  const data = {
    name: document.getElementById("name").value.trim(),
    subtitle: document.getElementById("subtitle").value.trim(),
    photo: state?.photo || "",
    spacing: { scale },
    info_rows,
    sections,
  };
  return data;
}

function updateSpacingLabel() {
  const val = document.getElementById("lineSpacing").value;
  document.getElementById("lineSpacingValue").textContent = `${val}%`;
}

function applySpacingToForm(scale) {
  const pct = Math.round((scale ?? 1) * 100);
  const clamped = Math.min(135, Math.max(75, pct));
  document.getElementById("lineSpacing").value = String(clamped);
  updateSpacingLabel();
}

async function fetchPdfBlob(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("PDF request failed");
  return res.blob();
}

function renderInfoRows(rows) {
  const el = document.getElementById("infoRows");
  el.innerHTML = "";
  rows.forEach((row, idx) => {
    const div = document.createElement("div");
    div.className = "info-row row-2";
    div.innerHTML = `
      <input type="text" class="info-label" placeholder="Label" value="${escapeHtml(row.label || "")}" />
      <input type="text" class="info-value" placeholder="Value" value="${escapeHtml(row.value || "")}" />
      <button type="button" class="btn-danger btn-remove-info">Del</button>`;
    div.querySelector(".btn-remove-info").onclick = () => {
      rows.splice(idx, 1);
      if (!rows.length) rows.push({ label: "", value: "" });
      renderInfoRows(rows);
      updatePreview();
    };
    div.querySelectorAll("input").forEach((inp) => inp.addEventListener("input", updatePreview));
    el.appendChild(div);
  });
}

function renderSections(sections) {
  const el = document.getElementById("sections");
  el.innerHTML = "";
  sections.forEach((sec, idx) => {
    const div = document.createElement("div");
    div.className = "section-block";
    div.innerHTML = `
      <div class="head">
        <input type="text" class="sec-title" placeholder="Section title" value="${escapeHtml(sec.title || "")}" />
        <button type="button" class="btn-danger btn-remove-sec">Del</button>
      </div>
      <textarea class="sec-items" placeholder="One item per line">${escapeHtml((sec.items || []).join("\n"))}</textarea>`;
    div.querySelector(".btn-remove-sec").onclick = () => {
      sections.splice(idx, 1);
      renderSections(sections);
      updatePreview();
    };
    div.querySelectorAll("input, textarea").forEach((inp) => inp.addEventListener("input", updatePreview));
    el.appendChild(div);
  });
}

function fillForm(data) {
  state = data;
  document.getElementById("name").value = data.name || "";
  document.getElementById("subtitle").value = data.subtitle || "";
  const scale = data.spacing?.scale ?? (typeof data.spacing === "number" ? data.spacing : 1);
  applySpacingToForm(scale);
  renderInfoRows(data.info_rows?.length ? data.info_rows : [{ label: "", value: "" }]);
  renderSections(data.sections?.length ? data.sections : [{ title: "", items: [] }]);
  updatePreview();
}

function showPreviewLoading() {
  document.getElementById("preview").innerHTML =
    '<p class="preview-loading">PDF preview updating...</p>';
}

function updatePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(async () => {
    const requestId = ++previewRequestId;
    const data = collectData();
    showPreviewLoading();
    try {
      const blob = await fetchPdfBlob("/api/preview", data);
      if (requestId !== previewRequestId) return;
      if (previewBlobUrl) URL.revokeObjectURL(previewBlobUrl);
      previewBlobUrl = URL.createObjectURL(blob);
      document.getElementById("preview").innerHTML =
        `<iframe class="pdf-frame" src="${previewBlobUrl}#toolbar=0&navpanes=0" title="PDF preview"></iframe>`;
    } catch (e) {
      if (requestId === previewRequestId) {
        document.getElementById("preview").innerHTML =
          `<p class="preview-error">${escapeHtml(e.message)}</p>`;
      }
    }
  }, 450);
}

function setStatus(msg, ok = true) {
  const el = document.getElementById("status");
  el.textContent = msg;
  el.style.color = ok ? "#5c6b7a" : "#c53030";
}

async function loadData() {
  const res = await fetch("/api/data");
  fillForm(await res.json());
  setStatus("Loaded.");
}

async function saveData() {
  const data = collectData();
  const res = await fetch("/api/data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Save failed");
  state = data;
  setStatus("Saved to resume_data.json");
}

async function generatePdf() {
  const data = collectData();
  await fetch("/api/data", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("PDF failed");
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  const disp = res.headers.get("Content-Disposition") || "";
  const match = disp.match(/filename="?([^";]+)"?/);
  a.download = match ? match[1] : "resume.pdf";
  a.click();
  URL.revokeObjectURL(a.href);
  setStatus("PDF downloaded (same as preview).");
  updatePreview();
}

document.getElementById("name").addEventListener("input", updatePreview);
document.getElementById("subtitle").addEventListener("input", updatePreview);
document.getElementById("lineSpacing").addEventListener("input", () => {
  updateSpacingLabel();
  updatePreview();
});
document.getElementById("btnAddInfo").onclick = () => {
  const data = collectData();
  data.info_rows.push({ label: "", value: "" });
  renderInfoRows(data.info_rows);
};
document.getElementById("btnAddSection").onclick = () => {
  const data = collectData();
  data.sections.push({ title: "New section", items: [] });
  renderSections(data.sections);
  updatePreview();
};
document.getElementById("btnReload").onclick = () => loadData().catch((e) => setStatus(e.message, false));
document.getElementById("btnSave").onclick = () => saveData().catch((e) => setStatus(e.message, false));
document.getElementById("btnPdf").onclick = () => generatePdf().catch((e) => setStatus(e.message, false));
document.getElementById("photoInput").addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("photo", file);
  setStatus("Uploading photo...");
  const res = await fetch("/api/photo", { method: "POST", body: fd });
  const json = await res.json();
  if (!res.ok) {
    setStatus(json.error || "Upload failed", false);
    return;
  }
  if (!state) state = {};
  state.photo = json.photo;
  const name = document.getElementById("name").value;
  const subtitle = document.getElementById("subtitle").value;
  state = { ...collectData(), photo: json.photo, name, subtitle };
  updatePreview();
  setStatus("Photo uploaded.");
});

loadData().catch((e) => setStatus(e.message, false));
