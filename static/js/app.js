function togglePassword(button) {
  const input = button.parentElement.querySelector('input');
  input.type = input.type === 'password' ? 'text' : 'password';
  button.innerHTML = input.type === 'password' ? '<i class="fa-regular fa-eye"></i>' : '<i class="fa-regular fa-eye-slash"></i>';
}

document.querySelectorAll('.tilt-card').forEach((card) => {
  card.addEventListener('pointermove', (event) => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || window.innerWidth < 781) return;
    const bounds = card.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2;
    const y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2;
    card.style.transform = `perspective(1100px) rotateX(${y * -3.5}deg) rotateY(${x * 4.5}deg)`;
  });
  card.addEventListener('pointerleave', () => { card.style.transform = ''; });
});

function drawResolutionChart(id) {
  const canvas = document.getElementById(id);
  if (!canvas || typeof Chart === 'undefined') return;
  new Chart(canvas, {
    type: 'line',
    data: { labels: ['May', 'Jun', 'Jul', 'Aug', 'Sep'], datasets: [{ data: [54, 63, 59, 76, 86], borderColor: '#ff6f73', backgroundColor: 'rgba(255,111,115,.16)', fill: true, tension: .45, pointRadius: 0, borderWidth: 3 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#a4acbb', font: { family: 'DM Mono', size: 9 } } }, y: { display: false, min: 0, max: 100 } } }
  });
}

setTimeout(() => document.querySelectorAll('.cc-toast').forEach((toast) => setTimeout(() => toast.remove(), 5000)), 20);
