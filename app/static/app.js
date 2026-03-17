const predictForm = document.getElementById("predict-form");
const predictResult = document.getElementById("predict-result");

predictForm?.addEventListener('submit', async (e) => {
  e.preventDefault();
  predictResult.textContent = '识别中...';
  const formData = new FormData(predictForm);
  const res = await fetch('/predict', { method: 'POST', body: formData });
  const data = await res.json();
  if (!res.ok) {
    predictResult.textContent = `错误: ${data.detail || res.status}`;
    return;
  }
  predictResult.innerHTML = `动作: <strong>${data.label_name}</strong><br>置信度: ${(data.confidence*100).toFixed(1)}%<br>标准度评分: ${data.score}<br>建议: <ul>${data.suggestions.map(s=>`<li>${s}</li>`).join('')}</ul><br>帧数: ${data.stats.frames}`;
});
