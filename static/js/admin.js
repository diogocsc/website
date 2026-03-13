const uploadZone  = document.getElementById('uploadZone');
const browseBtn   = document.getElementById('browseBtn');
const cvFile      = document.getElementById('cvFile');
const uploadStatus = document.getElementById('uploadStatus');
const statusFill  = document.getElementById('statusFill');
const statusMsg   = document.getElementById('statusMsg');
const uploadResult = document.getElementById('uploadResult');

/* ─── Browse / Drag ──────────────────────────────────────────── */
browseBtn.addEventListener('click', () => cvFile.click());
uploadZone.addEventListener('click', (e) => { if (e.target !== browseBtn) cvFile.click(); });

cvFile.addEventListener('change', () => {
  if (cvFile.files[0]) handleUpload(cvFile.files[0]);
});

uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleUpload(file);
});

/* ─── Upload handler ─────────────────────────────────────────── */
async function handleUpload(file) {
  if (!file.name.endsWith('.docx')) {
    showResult('Please upload a .docx file.', 'error');
    return;
  }

  // Show progress UI
  uploadResult.hidden = true;
  uploadStatus.hidden = false;
  statusFill.style.width = '0%';
  statusMsg.textContent = 'Uploading…';

  // Animate to 30% during upload
  animateFill(30, 800);

  const formData = new FormData();
  formData.append('cv_file', file);

  try {
    statusMsg.textContent = 'Parsing CV with Ollama…';
    animateFill(70, 3000);  // slow crawl while waiting for LLM

    const res = await fetch('/admin/upload', { method: 'POST', body: formData });
    const data = await res.json();

    animateFill(100, 300);
    await sleep(400);
    uploadStatus.hidden = true;

    if (data.success) {
      showResult('✓ CV parsed and site updated successfully. <a href="/" target="_blank">View site ↗</a>', 'success');
      setTimeout(() => location.reload(), 1500);
    } else {
      showResult('✕ ' + (data.error || 'Upload failed.'), 'error');
    }
  } catch (err) {
    uploadStatus.hidden = true;
    showResult('✕ Network error: ' + err.message, 'error');
  }
}

function animateFill(target, duration) {
  const start = parseFloat(statusFill.style.width) || 0;
  const diff  = target - start;
  const startTime = performance.now();
  function step(now) {
    const t = Math.min((now - startTime) / duration, 1);
    statusFill.style.width = (start + diff * easeOut(t)) + '%';
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
function sleep(ms)  { return new Promise(r => setTimeout(r, ms)); }

function showResult(html, type) {
  uploadResult.hidden = false;
  uploadResult.className = 'admin-alert admin-alert--' + type;
  uploadResult.innerHTML = html;
}

/* ─── Sidebar nav active state ───────────────────────────────── */
document.querySelectorAll('.admin-nav-link').forEach(link => {
  link.addEventListener('click', function() {
    document.querySelectorAll('.admin-nav-link').forEach(l => l.classList.remove('active'));
    if (this.getAttribute('href').startsWith('#')) this.classList.add('active');
  });
});
