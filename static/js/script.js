document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const video = document.getElementById('qr-video');
    const canvas = document.getElementById('qr-canvas');
    const startScannerBtn = document.getElementById('start-scanner');
    const qrUpload = document.getElementById('qr-upload');
    const scanStatus = document.getElementById('scan-status');
    const videoContainer = document.getElementById('video-container');
    const safetyModal = document.getElementById('safety-modal');
    const modalHeader = document.getElementById('modal-header');
    const modalTitle = document.getElementById('modal-title');
    const modalMessage = document.getElementById('modal-message');
    const urlDisplay = document.getElementById('url-display');
    const proceedBtn = document.getElementById('proceed-visit');
    const cancelBtn = document.getElementById('cancel-visit');
    const safeCount = document.getElementById('safe-count');
    const unsafeCount = document.getElementById('unsafe-count');
    
    // State variables
    let scannerActive = false;
    let stream = null;
    let currentUrl = '';
    let safeScans = parseInt(localStorage.getItem('safeScans')) || 0;
    let unsafeScans = parseInt(localStorage.getItem('unsafeScans')) || 0;
    
    // Initialize
    updateStats();
    
    // Event Listeners
    startScannerBtn.addEventListener('click', toggleScanner);
    qrUpload.addEventListener('change', handleFileUpload);
    proceedBtn.addEventListener('click', visitSite);
    cancelBtn.addEventListener('click', closeModal);
    
    // Toggle Scanner Function
    function toggleScanner() {
        if (scannerActive) {
            stopScanner();
            startScannerBtn.innerHTML = '<i class="fas fa-camera"></i> Live Scan';
            videoContainer.style.display = 'none';
            scanStatus.style.display = 'flex';
        } else {
            startScanner();
            startScannerBtn.innerHTML = '<i class="fas fa-stop"></i> Stop Scanner';
            videoContainer.style.display = 'block';
            scanStatus.style.display = 'none';
        }
    }

    // Start Scanner Function
    function startScanner() {
        if (stream) return;
        
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        })
        .then(function(s) {
            stream = s;
            video.srcObject = stream;
            scannerActive = true;
            video.play()
                .then(() => {
                    scanFrame();
                })
                .catch(err => {
                    console.error("Video play error:", err);
                    showError("Couldn't start camera. Please try again.");
                    stopScanner();
                });
        })
        .catch(function(err) {
            console.error("Camera error:", err);
            showError("Camera access denied. Please enable permissions.");
        });
    }

    // Stop Scanner Function
    function stopScanner() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        scannerActive = false;
    }

    // Scan Frame Function
    function scanFrame() {
        if (!scannerActive) return;

        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            
            if (code) {
                stopScanner();
                checkUrlSafety(code.data);
                return;
            }
        }
        
        requestAnimationFrame(scanFrame);
    }

    // Handle File Upload Function
    function handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Reset file input
        event.target.value = '';

        // Show loading state
        scanStatus.innerHTML = `
            <div class="result-item checking">
                <div class="result-content">
                    <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--warning);"></i>
                    <p style="margin-top: 15px;">Analyzing QR code...</p>
                </div>
            </div>
        `;

        const formData = new FormData();
        formData.append('file', file);

        fetch('/scan', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            if (data.results && data.results.length > 0) {
                checkUrlSafety(data.results[0].data);
            } else {
                showError('No QR code found in the image');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message);
        });
    }

    // Check URL Safety Function
    async function checkUrlSafety(url) {
        currentUrl = url;
        
        // Validate URL
        if (!isValidUrl(url)) {
            showResult({
                url: url,
                isSafe: null,
                type: 'TEXT'
            });
            return;
        }

        // Show checking state
        showResult({
            url: url,
            isSafe: 'checking',
            type: 'URL'
        });

        try {
            // Call backend to check safety
            const response = await fetch('/check-safety', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) {
                throw new Error(`Safety check failed: ${response.status}`);
            }

            const safetyData = await response.json();

            if (safetyData.error) {
                throw new Error(safetyData.error);
            }

            // Update stats
            if (safetyData.is_safe) {
                safeScans++;
            } else {
                unsafeScans++;
            }
            updateStats();
            localStorage.setItem('safeScans', safeScans);
            localStorage.setItem('unsafeScans', unsafeScans);

            // Show result
            showResult({
                url: url,
                isSafe: safetyData.is_safe,
                type: 'URL',
                details: safetyData.details
            });

        } catch (error) {
            console.error('Safety check error:', error);
            showResult({
                url: url,
                isSafe: 'error',
                type: 'URL',
                error: error.message
            });
        }
    }

    // Show Result Function
    function showResult(result) {
        if (result.type === 'URL') {
            if (result.isSafe === true) {
                // Safe URL - show modal with option to proceed
                modalHeader.className = 'modal-header safe';
                modalTitle.textContent = 'URL Verified - Safe';
                modalMessage.textContent = 'This website appears to be safe';
                modalMessage.innerHTML = '<i class="fas fa-check-circle"></i> This website appears to be safe';
                urlDisplay.textContent = result.url;
                safetyModal.classList.add('active');
            } else if (result.isSafe === false) {
                // Unsafe URL - show warning modal
                modalHeader.className = 'modal-header unsafe';
                modalTitle.textContent = 'Security Warning!';
                modalMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> This website may be dangerous';
                urlDisplay.textContent = result.url;
                proceedBtn.style.display = 'none'; // Hide proceed button for unsafe sites
                safetyModal.classList.add('active');
            } else {
                // Error or checking state
                let statusHtml = '';
                if (result.isSafe === 'checking') {
                    statusHtml = `
                        <div class="result-item checking">
                            <div class="result-content">
                                <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--warning);"></i>
                                <p style="margin-top: 15px;">Checking URL safety...</p>
                                <p class="url-display">${result.url}</p>
                            </div>
                        </div>
                    `;
                } else {
                    statusHtml = `
                        <div class="result-item error">
                            <div class="result-content">
                                <i class="fas fa-times-circle" style="font-size: 2rem; color: var(--danger);"></i>
                                <p style="margin-top: 15px;">${result.error || 'Safety check failed'}</p>
                                <p class="url-display">${result.url}</p>
                            </div>
                        </div>
                    `;
                }
                scanStatus.innerHTML = statusHtml;
                scanStatus.style.display = 'flex';
            }
        } else {
            // Not a URL (text content)
            scanStatus.innerHTML = `
                <div class="result-item">
                    <div class="result-content">
                        <i class="fas fa-info-circle" style="font-size: 2rem; color: var(--primary);"></i>
                        <p style="margin-top: 15px;">QR Code Content:</p>
                        <p class="url-display">${result.url}</p>
                    </div>
                </div>
            `;
            scanStatus.style.display = 'flex';
        }
    }

    // Show Error Function
    function showError(message) {
        scanStatus.innerHTML = `
            <div class="result-item error">
                <div class="result-content">
                    <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--danger);"></i>
                    <p style="margin-top: 15px;">${message}</p>
                </div>
            </div>
        `;
        scanStatus.style.display = 'flex';
    }

    // Visit Site Function
    function visitSite() {
        window.open(currentUrl, '_blank');
        closeModal();
    }

    // Close Modal Function
    function closeModal() {
        safetyModal.classList.remove('active');
        proceedBtn.style.display = 'block'; // Reset proceed button visibility
        startScannerBtn.innerHTML = '<i class="fas fa-camera"></i> Live Scan';
        videoContainer.style.display = 'none';
        scanStatus.style.display = 'flex';
    }

    // Update Stats Function
    function updateStats() {
        safeCount.textContent = safeScans;
        unsafeCount.textContent = unsafeScans;
    }

    // Helper Functions
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    // Clean up on page unload
    window.addEventListener('beforeunload', stopScanner);
});