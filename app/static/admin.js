const annotateForm = document.getElementById("annotate-form");
const trainForm = document.getElementById("train-form");
const labelSelect = document.getElementById("label-select");
const annotateStatus = document.getElementById("annotate-status");
const trainStatus = document.getElementById("train-status");
let pollTimer = null;

async function loadLabels() {
  const res = await fetch('/labels', { credentials: 'same-origin' });
  if (!res.ok) {
    annotateStatus.textContent = '无法加载标签，可能未登录';
    return;
  }
  const data = await res.json();
  labelSelect.innerHTML = '';
  data.labels.forEach(l => {
    const opt = document.createElement('option');
    opt.value = l.id;
    opt.textContent = `${l.id} - ${l.name}`;
    labelSelect.appendChild(opt);
  });
}

function startPolling(targetEl) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    const res = await fetch('/train_status', { credentials: 'same-origin' });
    const data = await res.json();
    if (!res.ok) {
      targetEl.textContent = `错误: ${data.detail || res.status}`;
      clearInterval(pollTimer); pollTimer = null; return;
    }
    targetEl.textContent = `状态: ${data.status} | ${data.message || ''}`;
    if (data.status === 'done' || data.status === 'error') {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }, 1500);
}

annotateForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  annotateStatus.textContent = '上传并训练中...';
  startPolling(annotateStatus);
  const formData = new FormData(annotateForm);
  const res = await fetch('/annotate', { method: 'POST', body: formData, credentials: 'same-origin' });
  const data = await res.json();
  if (!res.ok) {
    annotateStatus.textContent = `错误: ${data.detail || res.status}`;
    return;
  }
  annotateStatus.textContent = `已保存 ${data.record.filename}，训练完成。`;
});

trainForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  trainStatus.textContent = '训练启动...';
  startPolling(trainStatus);
  const res = await fetch('/train', { method: 'POST', credentials: 'same-origin' });
  const data = await res.json();
  if (!res.ok) {
    trainStatus.textContent = `错误: ${data.detail || res.status}`;
    return;
  }
  trainStatus.textContent = '训练完成';
});

loadLabels();
