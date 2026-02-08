// --- Global State ---
let isPlaying = false;
let pollInterval = null;

// --- UI Logic ---
const adoptionSlider = document.getElementById('adoption');
const coalSlider = document.getElementById('coal');
const adoptionVal = document.getElementById('adoption-val');
const coalVal = document.getElementById('coal-val');
const statusDisplay = document.getElementById('status-display');

const initBtn = document.getElementById('init-btn');
const playBtn = document.getElementById('play-btn');
const pauseBtn = document.getElementById('pause-btn');
const resetBtn = document.getElementById('reset-btn');

adoptionSlider.oninput = () => adoptionVal.innerText = parseFloat(adoptionSlider.value).toFixed(2);
coalSlider.oninput = () => coalVal.innerText = parseFloat(coalSlider.value).toFixed(2);

// --- Initialization ---
initBtn.onclick = async () => {
    initBtn.disabled = true;
    playBtn.disabled = true;
    pauseBtn.disabled = true;
    resetBtn.disabled = true;
    
    try {
        await fetch('/init_simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                adoption: parseFloat(adoptionSlider.value),
                coal_price: parseFloat(coalSlider.value)
            })
        });
        
        // Start polling for status
        pollStatus();
    } catch (e) {
        statusDisplay.innerText = "Error: " + e;
        initBtn.disabled = false;
    }
};

function pollStatus() {
    const check = setInterval(async () => {
        const res = await fetch('/status');
        const data = await res.json();
        
        statusDisplay.innerText = "Status: " + data.status;
        
        if (data.ready) {
            clearInterval(check);
            playBtn.disabled = false;
            resetBtn.disabled = false;
            initBtn.disabled = true; // Can't re-init without reset
        }
    }, 1000);
}

// --- Play / Pause / Reset ---
playBtn.onclick = () => {
    isPlaying = true;
    playBtn.disabled = true;
    pauseBtn.disabled = false;
    runStepLoop();
};

pauseBtn.onclick = () => {
    isPlaying = false;
    playBtn.disabled = false;
    pauseBtn.disabled = true;
};

resetBtn.onclick = async () => {
    isPlaying = false;
    await fetch('/reset', { method: 'POST' });
    
    statusDisplay.innerText = "Status: Reset complete";
    initBtn.disabled = false;
    playBtn.disabled = true;
    pauseBtn.disabled = true;
    resetBtn.disabled = true;
    
    // Clear charts (optional, or just leave last state)
};

async function runStepLoop() {
    if (!isPlaying) return;
    
    try {
        const res = await fetch('/step', { method: 'POST' });
        const data = await res.json();
        
        if (data.error) {
            console.error(data.error);
            isPlaying = false;
            return;
        }
        
        updateCharts(data);
        
        if (isPlaying) {
            setTimeout(runStepLoop, 100); // Small delay to prevent freezing UI
        }
    } catch (e) {
        console.error("Step failed", e);
        isPlaying = false;
    }
}

// --- Carousel & Charts Logic (Same as before) ---
// ... (Include previous carousel and chart logic here) ...
const track = document.querySelector('.carousel-track');
const slides = Array.from(track.children);
const dots = Array.from(document.querySelectorAll('.dot'));
let currentSlideIndex = 0;

function updateSlidePosition() {
    const width = track.getBoundingClientRect().width;
    slides.forEach((slide, index) => slide.style.left = width * index + 'px');
    track.style.transform = 'translateX(-' + (width * currentSlideIndex) + 'px)';
    dots.forEach(d => d.classList.remove('current-dot'));
    dots[currentSlideIndex].classList.add('current-dot');
}

function moveCarousel(direction) {
    currentSlideIndex += direction;
    if (currentSlideIndex < 0) currentSlideIndex = slides.length - 1;
    if (currentSlideIndex >= slides.length) currentSlideIndex = 0;
    updateSlidePosition();
}
function jumpToSlide(index) {
    currentSlideIndex = index;
    updateSlidePosition();
}

window.onload = () => { updateSlidePosition(); initCharts(); };
window.onresize = updateSlidePosition;

let charts = {};
function initCharts() {
    const chartIds = ['chart-price-hand', 'chart-price-machine', 'chart-prod-hand', 'chart-prod-machine', 'chart-profit-hand', 'chart-profit-machine'];
    chartIds.forEach(id => {
        const ctx = document.getElementById(id).getContext('2d');
        const isMachine = id.includes('machine');
        charts[id] = new Chart(ctx, {
            type: 'bar',
            data: { labels: [], datasets: [{ label: 'Kiln Count', data: [], backgroundColor: isMachine ? 'rgba(54, 162, 235, 0.6)' : 'rgba(255, 99, 132, 0.6)' }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { title: { display: true, text: 'Waiting...' } }, scales: { y: { beginAtZero: true } } }
        });
    });
}
function updateCharts(data) {
    updateSingleChart('chart-price-hand', data.price.hand);
    updateSingleChart('chart-price-machine', data.price.machine);
    updateSingleChart('chart-prod-hand', data.production.hand);
    updateSingleChart('chart-prod-machine', data.production.machine);
    updateSingleChart('chart-profit-hand', data.profit.hand);
    updateSingleChart('chart-profit-machine', data.profit.machine);
}
function updateSingleChart(id, histData) {
    const chart = charts[id];
    if (!histData || !histData.data) return;
    chart.data.labels = histData.labels;
    chart.data.datasets[0].data = histData.data;
    chart.options.plugins.title.text = `Avg: ${histData.average.toFixed(2)}`;
    chart.update();
}