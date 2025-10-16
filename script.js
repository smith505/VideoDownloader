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

// Ad Modal Functions
let adViewStartTime = null;

function showAdModal() {
    const modal = document.getElementById('adModal');
    modal.classList.remove('hidden');
    adViewStartTime = Date.now();

    // Load the ad
    loadAd();

    // Track ad view
    trackAdView('started');
}

function closeAdModal() {
    const modal = document.getElementById('adModal');
    modal.classList.add('hidden');

    // Track ad completion if viewed for more than 5 seconds
    if (adViewStartTime) {
        const viewDuration = (Date.now() - adViewStartTime) / 1000;
        if (viewDuration >= 5) {
            trackAdView('completed', viewDuration);
            showThankYouMessage();
        }
        adViewStartTime = null;
    }

    // Clear the ad container
    const adContainer = document.getElementById('adContainer');
    adContainer.innerHTML = '';
}

function loadAd() {
    const adContainer = document.getElementById('adContainer');

    // Check if PropellerAds Zone ID is configured
    if (typeof propellerAdsZoneId !== 'undefined' && propellerAdsZoneId !== 'XXXXXX' && propellerAdsZoneId !== '10049059') {
        // Show message and trigger OnClick ad
        adContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; min-height: 250px; display: flex; flex-direction: column; justify-content: center;">
                <p style="color: #666; font-size: 1.2rem; margin-bottom: 20px;">
                    Thank you for supporting us! 💚
                </p>
                <p style="color: #555; font-size: 1rem; margin-bottom: 30px;">
                    The ad will open in a new window.
                </p>
                <button id="triggerAdBtn" style="padding: 15px 40px; background: #4CAF50; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer; margin: 0 auto;">
                    Click Here to View Ad
                </button>
                <p style="color: #999; font-size: 0.85rem; margin-top: 20px;">
                    Please disable your ad blocker if the ad doesn't appear
                </p>
            </div>
        `;

        // Add onclick handler to trigger the ad
        const triggerBtn = document.getElementById('triggerAdBtn');
        if (triggerBtn) {
            triggerBtn.onclick = function() {
                // Trigger PropellerAds OnClick
                const script = document.createElement('script');
                script.type = 'text/javascript';
                script.innerHTML = `
                    (function(d,z,s){s.src='https://'+d+'/400/'+z;try{(document.body||document.documentElement).appendChild(s)}catch(e){}})('gloomaug.net',${propellerAdsZoneId},document.createElement('script'))
                `;
                document.body.appendChild(script);

                console.log('PropellerAds OnClick triggered');

                // Show thank you message after click
                adContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; min-height: 250px; display: flex; flex-direction: column; justify-content: center;">
                        <p style="color: #4CAF50; font-size: 1.3rem; margin-bottom: 15px;">
                            ✓ Thank You!
                        </p>
                        <p style="color: #666; font-size: 1rem; margin-bottom: 15px;">
                            The ad should open in a new window.
                        </p>
                        <p style="color: #999; font-size: 0.9rem;">
                            Your support helps keep this service free!
                        </p>
                    </div>
                `;

                // Auto close after 3 seconds
                setTimeout(() => {
                    closeAdModal();
                }, 3000);
            };
        }

    } else {
        // Show placeholder if PropellerAds not configured
        console.log('PropellerAds not configured yet');
        showAdPlaceholder();
    }
}

function showAdPlaceholder() {
    const adContainer = document.getElementById('adContainer');
    adContainer.innerHTML = `
        <div style="text-align: center; padding: 40px; min-height: 250px; display: flex; flex-direction: column; justify-content: center;">
            <p style="color: #666; font-size: 1.1rem; margin-bottom: 15px;">
                Thank you so much for your support! 🙏
            </p>
            <p style="color: #999; font-size: 0.9rem; margin-bottom: 10px;">
                Ads are not yet configured. Once PropellerAds is set up, ads will appear here.
            </p>
            <p style="color: #999; font-size: 0.9rem;">
                Your willingness to help is greatly appreciated!
            </p>
            <p style="color: #4CAF50; font-size: 0.9rem; margin-top: 15px;">
                ✓ Support counted!
            </p>
            <p style="color: #666; font-size: 0.85rem; margin-top: 15px;">
                In the meantime, consider <a href="https://ko-fi.com/universalvideodownloader" target="_blank" style="color: #4CAF50; text-decoration: underline;">donating on Ko-fi</a>
            </p>
        </div>
    `;

    // Track the attempt even if no ad shown
    trackAdView('placeholder_shown');

    // Auto-close after 4 seconds for placeholder
    setTimeout(() => {
        closeAdModal();
    }, 4000);
}

function showCloseButton() {
    const modal = document.getElementById('adModal');
    if (!modal.classList.contains('hidden')) {
        const modalContent = modal.querySelector('.ad-modal-content');
        if (modalContent && !modalContent.querySelector('.close-after-timer')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'close-after-timer';
            closeBtn.textContent = 'Close';
            closeBtn.style.cssText = 'margin-top: 15px; padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1rem;';
            closeBtn.onclick = closeAdModal;
            modalContent.appendChild(closeBtn);
        }
    }
}

function showThankYouMessage() {
    const error = document.getElementById('error');
    error.textContent = 'Thank you for supporting us! 💚';
    error.style.backgroundColor = '#4CAF50';
    error.style.color = 'white';
    error.classList.remove('hidden');

    setTimeout(() => {
        error.classList.add('hidden');
        error.style.backgroundColor = '';
        error.style.color = '';
    }, 3000);
}

async function trackAdView(status, duration = 0) {
    try {
        // You can implement backend tracking here if needed
        console.log(`Ad view ${status}`, duration ? `(${duration.toFixed(1)}s)` : '');

        // Optional: Send to analytics
        // await fetch(`${API_URL}/track-ad`, {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ status, duration })
        // });
    } catch (e) {
        console.error('Tracking error:', e);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('adModal');
    if (event.target === modal) {
        closeAdModal();
    }
}
