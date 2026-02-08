// --- UI Logic ---
const adoptionSlider = document.getElementById('adoption');
const coalSlider = document.getElementById('coal');
const adoptionVal = document.getElementById('adoption-val');
const coalVal = document.getElementById('coal-val');

adoptionSlider.oninput = () => adoptionVal.innerText = parseFloat(adoptionSlider.value).toFixed(2);
coalSlider.oninput = () => coalVal.innerText = parseFloat(coalSlider.value).toFixed(2);

// --- Carousel Logic ---
const track = document.querySelector('.carousel-track');
const slides = Array.from(track.children);
const dots = Array.from(document.querySelectorAll('.dot'));
let currentSlideIndex = 0;

function updateSlidePosition() {
    const width = track.getBoundingClientRect().width;
    slides.forEach((slide, index) => {
        slide.style.left = width * index + 'px';
    });
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

window.onload = () => {
    updateSlidePosition();
    initCharts();
};
window.onresize = updateSlidePosition;

// --- Chart.js Logic ---
let charts = {};

function initCharts() {
    const chartIds = [
        'chart-price-hand', 'chart-price-machine',
        'chart-prod-hand', 'chart-prod-machine',
        'chart-profit-hand', 'chart-profit-machine'
    ];
    
    chartIds.forEach(id => {
        const ctx = document.getElementById(id).getContext('2d');
        const isMachine = id.includes('machine');
        
        charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Kiln Count',
                    data: [],
                    backgroundColor: isMachine ? 'rgba(54, 162, 235, 0.6)' : 'rgba(255, 99, 132, 0.6)',
                    borderColor: isMachine ? 'rgba(54, 162, 235, 1)' : 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: 'Waiting for data...' }
                },
                scales: {
                    y: { beginAtZero: true },
                    x: { title: {display: true, text: 'Range'} }
                }
            }
        });
    });
}

function updateChart(chartId, histData) {
    const chart = charts[chartId];
    if (!histData || histData.data.length === 0) {
        chart.data.datasets[0].data = [];
        chart.options.plugins.title.text = "No Data";
        chart.update();
        return;
    }

    chart.data.labels = histData.labels;
    chart.data.datasets[0].data = histData.data;
    chart.options.plugins.title.text = `Average: ${histData.average.toFixed(2)}`;
    chart.update();
}

// --- API Call ---
document.getElementById('run-btn').addEventListener('click', async () => {
    const btn = document.getElementById('run-btn');
    const originalText = btn.innerText;
    btn.innerText = "Running Simulation...";
    btn.disabled = true;

    try {
        const response = await fetch('/run_simulation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                adoption: parseFloat(adoptionSlider.value),
                coal_price: parseFloat(coalSlider.value)
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert("Error: " + data.error);
            return;
        }

        updateChart('chart-price-hand', data.price.hand);
        updateChart('chart-price-machine', data.price.machine);
        updateChart('chart-prod-hand', data.production.hand);
        updateChart('chart-prod-machine', data.production.machine);
        updateChart('chart-profit-hand', data.profit.hand);
        updateChart('chart-profit-machine', data.profit.machine);

    } catch (error) {
        console.error("Error:", error);
        alert("Simulation failed. See console for details.");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
});