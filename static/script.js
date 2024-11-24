const socket = io();
const toggleBtn = document.getElementById('toggle-btn');
const transcriptText = document.getElementById('transcript-text');
const themeToggle = document.getElementById('theme-toggle');
const status = document.getElementById('status');
const body = document.body;
const searchBar = document.getElementById('search-bar');
const summary = document.getElementById('transcript-summary');
const noiseBar = document.getElementById('noise-bar');
const noiseLevelText = document.getElementById('noise-level-text');
const analyzeBtn = document.getElementById('analyze-btn');

let isRecording = false;
let analyzedText = '';

// Toggle Recording
toggleBtn.addEventListener('click', () => {
    isRecording = !isRecording;
    toggleBtn.textContent = isRecording ? "🛑 Stop Recording" : "🎤 Start Recording";
    toggleBtn.classList.toggle('mic-on', isRecording);
    toggleBtn.classList.toggle('mic-off', !isRecording);
    status.textContent = isRecording ? "Recording in progress..." : "Press the button to start transcription";
    socket.emit('toggle_transcription');
});

// Display Real-Time Transcript
socket.on('partial_transcript', data => {
    transcriptText.innerHTML = analyzedText + data.text;
});

// Display Analyzed Text
socket.on('formatted_transcript', data => {
    analyzedText += data.text + "<br>";
    transcriptText.innerHTML = analyzedText;
});

// Update Noise Level
socket.on('noise_level', data => {
    const level = data.level;
    noiseBar.style.width = `${level}%`;
    if (level > 70) {
        noiseBar.style.backgroundColor = 'red';
        noiseLevelText.textContent = "High Noise";
    } else if (level > 40) {
        noiseBar.style.backgroundColor = 'yellow';
        noiseLevelText.textContent = "Moderate Noise";
    } else {
        noiseBar.style.backgroundColor = 'green';
        noiseLevelText.textContent = "Low Noise";
    }
});

// Analyze Now
analyzeBtn.addEventListener('click', () => {
    const transcript = transcriptText.innerText.trim();
    if (!transcript) {
        alert("No transcript available to analyze.");
        return;
    }

    socket.emit('analyze_transcript', { text: transcript });
});

// Display Analysis Results
socket.on('analysis_result', data => {
    summary.innerText = data.text;
});

// Download Transcript
document.getElementById('download-btn').addEventListener('click', () => {
    const transcript = transcriptText.innerText.trim();
    if (!transcript) {
        alert("No transcript available to download.");
        return;
    }

    const blob = new Blob([transcript], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = "transcript.txt";
    a.click();
    URL.revokeObjectURL(url);
});

// Theme Toggle
themeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    themeToggle.textContent = body.classList.contains('dark-mode') ? '☀️ Light Mode' : '🌙 Dark Mode';
});

// Search Transcript
searchBar.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const lines = transcriptText.innerHTML.split('<br>');
    transcriptText.innerHTML = lines
        .map(line => line.toLowerCase().includes(query) ? `<span style="background-color: yellow;">${line}</span>` : line)
        .join('<br>');
});

