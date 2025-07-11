// Audio recording and file upload functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.getElementById('file-label');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const submitBtn = document.getElementById('submit-btn');
    const uploadForm = document.getElementById('upload-form');
    const loading = document.getElementById('loading');
    
    // Recording elements
    const recordBtn = document.getElementById('record-btn');
    const stopBtn = document.getElementById('stop-btn');
    const countdown = document.getElementById('countdown');
    const countdownNumber = document.getElementById('countdown-number');
    const recordingStatus = document.getElementById('recording-status');
    const recordingTimer = document.getElementById('recording-timer');
    const recordedAudio = document.getElementById('recorded-audio');
    const audioPlayback = document.getElementById('audio-playback');
    const useRecordingBtn = document.getElementById('use-recording-btn');
    const reRecordBtn = document.getElementById('re-record-btn');
    
    // Recording variables
    let mediaRecorder = null;
    let recordedChunks = [];
    let recordedBlob = null;
    let stream = null;
    let countdownInterval = null;
    let recordingInterval = null;
    let countdownTime = 3;
    let recordingTime = 5;

    // Initialize
    resetUI();

    // File validation
    function isAudioFile(file) {
        const audioTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/m4a', 'audio/flac', 'audio/ogg', 'audio/webm'];
        return audioTypes.includes(file.type) || file.name.match(/\.(wav|mp3|m4a|flac|ogg|webm)$/i);
    }

    // File size validation (max 10MB)
    function isValidFileSize(file) {
        return file.size <= 10 * 1024 * 1024; // 10MB
    }

    // Reset UI to initial state
    function resetUI() {
        // Hide all status elements
        countdown.style.display = 'none';
        recordingStatus.style.display = 'none';
        recordedAudio.style.display = 'none';
        fileInfo.style.display = 'none';
        
        // Reset buttons
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        submitBtn.disabled = true;
        
        // Reset file input
        fileInput.value = '';
        
        // Reset recorded data
        recordedBlob = null;
        recordedChunks = [];
        
        // Clear stored blob
        window.recordedAudioBlob = null;
        window.recordedAudioFilename = null;
        
        // Reset recorded actions to original state
        const recordedActions = document.querySelector('.recorded-actions');
        recordedActions.innerHTML = `
            <button type="button" class="use-btn" id="use-recording-btn">Use</button>
            <button type="button" class="retry-btn" id="re-record-btn">Retry</button>
        `;
        
        // Re-attach event listeners for the new buttons
        document.getElementById('use-recording-btn').addEventListener('click', useRecording);
        document.getElementById('re-record-btn').addEventListener('click', resetUI);
    }

    // Start recording process
    async function startRecording() {
        try {
            // Request microphone access
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Start countdown
            startCountdown();
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            showError('Could not access microphone. Please check permissions.');
        }
    }

    // Start countdown
    function startCountdown() {
        countdown.style.display = 'block';
        countdownTime = 3;
        countdownNumber.textContent = countdownTime;
        
        recordBtn.disabled = true;
        
        countdownInterval = setInterval(() => {
            countdownTime--;
            if (countdownTime > 0) {
                countdownNumber.textContent = countdownTime;
            } else {
                clearInterval(countdownInterval);
                countdown.style.display = 'none';
                startActualRecording();
            }
        }, 1000);
    }

    // Start actual recording
    function startActualRecording() {
        try {
            console.log('=== STARTING RECORDING DEBUG ===');
            
            // Check what formats are supported
            console.log('Checking MediaRecorder support:');
            console.log('audio/wav supported:', MediaRecorder.isTypeSupported('audio/wav'));
            console.log('audio/webm supported:', MediaRecorder.isTypeSupported('audio/webm'));
            console.log('audio/webm;codecs=opus supported:', MediaRecorder.isTypeSupported('audio/webm;codecs=opus'));
            console.log('audio/mp4 supported:', MediaRecorder.isTypeSupported('audio/mp4'));
            
            // Create media recorder with WAV format instead of WebM
            const options = {
                mimeType: 'audio/wav'
            };
            
            // Fallback to WebM if WAV is not supported
            if (!MediaRecorder.isTypeSupported('audio/wav')) {
                console.log('WAV not supported, trying audio/webm');
                options.mimeType = 'audio/webm;codecs=opus';
            }
            
            console.log('Selected mimeType:', options.mimeType);
            
            mediaRecorder = new MediaRecorder(stream, options);
            console.log('MediaRecorder created with mimeType:', mediaRecorder.mimeType);
            recordedChunks = [];
            
            // Set up event handlers
            mediaRecorder.ondataavailable = function(event) {
                console.log('Data available, size:', event.data.size, 'type:', event.data.type);
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };
            
            mediaRecorder.onstop = function() {
                console.log('Recording stopped. Chunks:', recordedChunks.length);
                console.log('MediaRecorder final mimeType:', mediaRecorder.mimeType);
                
                // Create blob from recorded chunks - use the same type as recording
                const mimeType = mediaRecorder.mimeType || 'audio/wav';
                recordedBlob = new Blob(recordedChunks, { type: mimeType });
                
                console.log('Created blob - size:', recordedBlob.size, 'type:', recordedBlob.type);
                
                // Create audio URL and set to player
                const audioUrl = URL.createObjectURL(recordedBlob);
                audioPlayback.src = audioUrl;
                
                // Show recorded audio section
                recordingStatus.style.display = 'none';
                recordedAudio.style.display = 'block';
                
                // Stop stream
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                
                // Reset buttons
                recordBtn.disabled = false;
                stopBtn.disabled = true;
                
                console.log('=== RECORDING COMPLETE ===');
            };
            
            // Start recording
            mediaRecorder.start();
            console.log('MediaRecorder started');
            
            // Show recording status
            recordingStatus.style.display = 'flex';
            recordingTime = 5;
            recordingTimer.textContent = recordingTime;
            
            stopBtn.disabled = false;
            
            // Start recording timer
            recordingInterval = setInterval(() => {
                recordingTime--;
                recordingTimer.textContent = recordingTime;
                
                if (recordingTime <= 0) {
                    stopRecording();
                }
            }, 1000);
            
        } catch (error) {
            console.error('Error starting recording:', error);
            showError('Error starting recording. Please try again.');
        }
    }

    // Stop recording
    function stopRecording() {
        if (recordingInterval) {
            clearInterval(recordingInterval);
        }
        
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
    }

    // Use recorded audio
    function useRecording() {
        console.log('=== USE RECORDING DEBUG ===');
        if (recordedBlob) {
            console.log('Original blob - size:', recordedBlob.size, 'type:', recordedBlob.type);
            
            // Store the blob globally for form submission
            window.recordedAudioBlob = recordedBlob;
            
            // Determine file extension based on blob type
            const mimeType = recordedBlob.type;
            let extension = '.wav';
            let filename = 'recorded-audio.wav';
            
            if (mimeType.includes('webm')) {
                extension = '.webm';
                filename = 'recorded-audio.webm';
            }
            
            console.log('Determined filename:', filename, 'extension:', extension);
            
            // Store filename for form submission
            window.recordedAudioFilename = filename;
            
            // Clear any existing file selection
            fileInput.value = '';
            
            // Enable submit button
            submitBtn.disabled = false;
            
            // Hide file info in upload section (since we're using recorded audio)
            fileInfo.style.display = 'none';
            
            // Keep recorded audio section visible but update its appearance
            const recordedActions = document.querySelector('.recorded-actions');
            recordedActions.innerHTML = '<span style="color: #4caf50; font-weight: 600;">✓ Ready to analyze</span>';
            
            console.log('=== USE RECORDING COMPLETE ===');
            console.log('Stored blob size:', window.recordedAudioBlob.size);
            console.log('Stored filename:', window.recordedAudioFilename);
        } else {
            console.log('ERROR: No recorded blob available');
        }
    }

    // Handle file selection
    function handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        if (!isAudioFile(file)) {
            showError('Please select a valid audio file (WAV, MP3, M4A, FLAC, OGG, WebM)');
            return;
        }

        // Validate file size
        if (!isValidFileSize(file)) {
            showError('File size must be less than 10MB');
            return;
        }

        // Update UI
        fileName.textContent = file.name;
        fileInfo.style.display = 'block';
        submitBtn.disabled = false;

        // Hide recorded audio if shown and reset its state
        recordedAudio.style.display = 'none';
        
        // Reset recorded actions to original state
        const recordedActions = document.querySelector('.recorded-actions');
        recordedActions.innerHTML = `
            <button type="button" class="use-btn" id="use-recording-btn">Use</button>
            <button type="button" class="retry-btn" id="re-record-btn">Retry</button>
        `;
        
        // Re-attach event listeners for the new buttons
        document.getElementById('use-recording-btn').addEventListener('click', useRecording);
        document.getElementById('re-record-btn').addEventListener('click', resetUI);
    }

    // Show error message
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'flash-message flash-error';
        errorDiv.innerHTML = `<span class="flash-icon">❌</span>${message}`;
        
        // Remove existing errors
        const existingErrors = document.querySelectorAll('.flash-error');
        existingErrors.forEach(err => err.remove());
        
        // Add new error
        const container = document.querySelector('.main-content');
        container.insertBefore(errorDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Event listeners
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    useRecordingBtn.addEventListener('click', useRecording);
    reRecordBtn.addEventListener('click', resetUI);

    // File input change event
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        handleFileSelect(file);
    });

    // Drag and drop events
    fileLabel.addEventListener('dragover', function(e) {
        e.preventDefault();
        fileLabel.style.borderColor = 'rgba(201, 169, 110, 0.8)';
        fileLabel.style.background = 'rgba(201, 169, 110, 0.15)';
    });

    fileLabel.addEventListener('dragleave', function(e) {
        e.preventDefault();
        fileLabel.style.borderColor = 'rgba(255, 255, 255, 0.3)';
        fileLabel.style.background = 'rgba(255, 255, 255, 0.05)';
    });

    fileLabel.addEventListener('drop', function(e) {
        e.preventDefault();
        fileLabel.style.borderColor = 'rgba(255, 255, 255, 0.3)';
        fileLabel.style.background = 'rgba(255, 255, 255, 0.05)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });

    // Form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault(); // Always prevent default, we'll handle submission manually
        
        console.log('=== FORM SUBMISSION DEBUG ===');
        console.log('File input files:', fileInput.files.length);
        console.log('Recorded blob available:', !!window.recordedAudioBlob);
        
        // Check if we have either a file or recorded audio
        if (fileInput.files.length === 0 && !window.recordedAudioBlob) {
            showError('Please record audio or select a file first!');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="btn-icon">🔄</span><span class="btn-text">Analyzing...</span>';
        loading.style.display = 'block';
        
        // Create FormData
        const formData = new FormData();
        
        if (window.recordedAudioBlob) {
            // Use recorded audio
            console.log('Using recorded audio blob - size:', window.recordedAudioBlob.size);
            const file = new File([window.recordedAudioBlob], window.recordedAudioFilename, { 
                type: window.recordedAudioBlob.type 
            });
            formData.append('file', file);
            console.log('Created file for upload - name:', file.name, 'size:', file.size, 'type:', file.type);
        } else {
            // Use uploaded file
            console.log('Using uploaded file - name:', fileInput.files[0].name, 'size:', fileInput.files[0].size);
            formData.append('file', fileInput.files[0]);
        }
        
        console.log('=== SENDING REQUEST ===');
        
        // Send the form data
        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            // Replace the page content with the response
            document.open();
            document.write(html);
            document.close();
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred while analyzing the audio. Please try again.');
            
            // Reset loading state
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="btn-icon">🔍</span><span class="btn-text">Analyze</span>';
            loading.style.display = 'none';
        });
    });
});
