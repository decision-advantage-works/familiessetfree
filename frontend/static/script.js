// --- Global State ---
let isPlaying = false;
let pollInterval = null;

// --- UI Logic ---
const adoptionSlider = document.getElementById('adoption');
const coalSlider = document.getElementById('coal');
const machineDemandSlider = document.getElementById('machine_demand');

const adoptionVal = document.getElementById('adoption-val');
const coalVal = document.getElementById('coal-val');
const machineDemandVal = document.getElementById('machine_demand-val');

const statusText = document.getElementById('status-text');
const dayCounter = document.getElementById('day-counter');

const initBtn = document.getElementById('init-btn');
const playBtn = document.getElementById('play-btn');
const pauseBtn = document.getElementById('pause-btn');
const resetBtn = document.getElementById('reset-btn');

adoptionSlider.oninput = () => adoptionVal.innerText = parseFloat(adoptionSlider.value).toFixed(2);
coalSlider.oninput = () => coalVal.innerText = parseFloat(coalSlider.value).toFixed(2);
machineDemandSlider.oninput = () => machineDemandVal.innerText = parseFloat(machineDemandSlider.value).toFixed(2);

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
                coal_price: parseFloat(coalSlider.value),
                machine_demand: parseFloat(machineDemandSlider.value)
            })
        });
        
        // Start polling for status
        pollStatus();
    } catch (e) {
        statusText.innerText = "Error: " + e;
        initBtn.disabled = false;
    }
};

function pollStatus() {
    const check = setInterval(async () => {
        const res = await fetch('/status');
        const data = await res.json();
        
        statusText.innerText = data.status;
        
        // UPDATED: Show Day first, then Agent count if available
        let agentDisplay = data.agent_count ? data.agent_count : 0;
        dayCounter.innerText = "Day: " + data.step + " | Agents: " + agentDisplay + "/" + agentDisplay;
        
        if (data.ready) {
            clearInterval(check);
            playBtn.disabled = false;
            resetBtn.disabled = false;
            initBtn.disabled = true; 
        }
    }, 500); // Faster polling for initialization feedback
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
    
    statusText.innerText = "Reset complete";
    dayCounter.innerText = "Day: 0 | Agents: 0/0";
    initBtn.disabled = false;
    playBtn.disabled = true;
    pauseBtn.disabled = true;
    resetBtn.disabled = true;
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
        
        // Update charts and Day counter
        updateCharts(data);
        console.log(data.profit)
        
        dayCounter.innerText = "Day: " + data.step;
        
        if (isPlaying) {
            setTimeout(runStepLoop, 50); // Fast loop
        }
    } catch (e) {
        console.error("Step failed", e);
        isPlaying = false;
    }
}

// --- Carousel & Charts Logic ---
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
    const chartIds = [
        {id: 'chart-price-hand', xLabel: 'Price (PKR)', yLabel: 'Kilns'},
        {id: 'chart-price-machine', xLabel: 'Price (PKR)', yLabel: 'Kilns'},
        {id: 'chart-prod-hand', xLabel: 'Brick Output', yLabel: 'Kilns'},
        {id: 'chart-prod-machine', xLabel: 'Brick Output', yLabel: 'Kilns'},
        {id: 'chart-profit-hand', xLabel: 'Profit (PKR)', yLabel: 'Kilns'},
        {id: 'chart-profit-machine', xLabel: 'Profit (PKR)', yLabel: 'Kilns'}
    ];
    
    chartIds.forEach(conf => {
        const ctx = document.getElementById(conf.id).getContext('2d');
        const isMachine = conf.id.includes('machine');
        
        charts[conf.id] = new Chart(ctx, {
            type: 'bar',
            data: { 
                labels: [], 
                datasets: [{ 
                    label: 'Count', 
                    data: [], 
                    backgroundColor: isMachine ? 'rgba(54, 162, 235, 0.6)' : 'rgba(255, 99, 132, 0.6)' 
                }] 
            },
            options: { 
                responsive: true, 
                maintainAspectRatio: false, 
                layout: {
                    padding: {
                        bottom: 20, // Fix for labels being cut off
                        left: 10,
                        right: 10
                    }
                },
                plugins: { 
                    title: { display: true, text: 'Waiting for data...' },
                    legend: { display: false }
                }, 
                scales: { 
                    y: { 
                        beginAtZero: true,
                        title: { display: true, text: conf.yLabel }
                    },
                    x: {
                        title: { display: true, text: conf.xLabel },
                        ticks: {
                            maxRotation: 0, // Keep labels horizontal if possible
                            autoSkip: true
                        }
                    }
                } 
            }
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