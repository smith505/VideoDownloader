// Auto-detect API URL based on environment
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'
    : '/api';

// Load donation progress on page load
async function loadDonationProgress() {
    try {
        const response = await fetch(`${API_URL}/donations`);
        const data = await response.json();

        const progressBar = document.getElementById('goalProgress');
        if (progressBar && data.percentage !== undefined) {
            // Animate the progress bar
            setTimeout(() => {
                progressBar.style.width = `${data.percentage}%`;
            }, 100);
        }
    } catch (error) {
        console.error('Failed to load donation progress:', error);
    }
}

// Load donation progress when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadDonationProgress();
    // Auto-update progress bar every 30 seconds
    setInterval(loadDonationProgress, 30000);
});

// Check if URL is YouTube
function isYouTubeURL(url) {
    return url.includes('youtube.com') || url.includes('youtu.be');
}

// Update quality visibility based on URL
function updateQualityVisibility() {
    const url = document.getElementById('urlInput').value.trim();
    const qualitySection = document.querySelector('.quality-selection');

    // Hide quality selector only if URL is non-empty AND not YouTube
    if (url && !isYouTubeURL(url)) {
        qualitySection.classList.add('hidden');
    } else {
        qualitySection.classList.remove('hidden');
    }
}

// Listen for URL input changes
document.getElementById('urlInput').addEventListener('input', updateQualityVisibility);

// Update quality options when format type changes
document.querySelectorAll('input[name="downloadType"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        updateQualityOptions(e.target.value);
    });
});

function updateQualityOptions(type) {
    const qualitySelect = document.getElementById('qualitySelect');
    const qualityLabel = document.getElementById('qualityLabel');
    qualitySelect.innerHTML = '';

    if (type === 'video') {
        qualityLabel.textContent = 'Quality:';

        const videoQualities = [
            { value: '1080', label: '1080p (Full HD)' },
            { value: '720', label: '720p (HD)' },
            { value: '480', label: '480p (SD)' },
            { value: '360', label: '360p (Low)' },
            { value: '144', label: '144p (Very Low)' }
        ];

        videoQualities.forEach(q => {
            const option = document.createElement('option');
            option.value = q.value;
            option.textContent = q.label;
            qualitySelect.appendChild(option);
        });
    } else {
        qualityLabel.textContent = 'Bitrate:';

        const audioQualities = [
            { value: '320', label: '320 kbps (Best)' },
            { value: '256', label: '256 kbps (High)' },
            { value: '128', label: '128 kbps (Medium)', selected: true },
            { value: '96', label: '96 kbps (Low)' }
        ];

        audioQualities.forEach(q => {
            const option = document.createElement('option');
            option.value = q.value;
            option.textContent = q.label;
            if (q.selected) {
                option.selected = true;
            }
            qualitySelect.appendChild(option);
        });
    }
}

async function downloadFile() {
    const url = document.getElementById('urlInput').value.trim();
    const type = document.querySelector('input[name="downloadType"]:checked').value;
    const quality = document.getElementById('qualitySelect').value;
    const downloadProgress = document.getElementById('downloadProgress');
    const error = document.getElementById('error');

    error.classList.add('hidden');

    if (!url) {
        showError('Please enter a valid URL');
        return;
    }

    downloadProgress.classList.remove('hidden');

    try {
        const response = await fetch(`${API_URL}/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url,
                type,
                quality: parseInt(quality)
            })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Download failed');
        }

        // Get filename from Content-Disposition header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'download';
        if (contentDisposition) {
            const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(contentDisposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        // Download the file
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

    } catch (err) {
        showError(err.message);
    } finally {
        downloadProgress.classList.add('hidden');
    }
}

function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.classList.remove('hidden');
}

// Allow Enter key to download
document.getElementById('urlInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        downloadFile();
    }
});
