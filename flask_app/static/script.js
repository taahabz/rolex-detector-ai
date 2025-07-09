// Audio recording and enhanced UX
document.addEventListener('DOMContentLoaded', function() {
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
    let countdownInterval = null;
    let recordingInterval = null;
    let recordingTimeLeft = 5;

    // Initialize audio context
    let audioContext = null;
    function initAudioContext() {
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Audio context not supported');
        }
    }

    // Request microphone permission and start recording
    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });
            
            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            recordedChunks = [];
            
            mediaRecorder.ondataavailable = function(event) {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };
            
            mediaRecorder.onstop = function() {
                recordedBlob = new Blob(recordedChunks, {
                    type: 'audio/webm;codecs=opus'
                });
                
                const audioURL = URL.createObjectURL(recordedBlob);
                audioPlayback.src = audioURL;
                
                // Show recorded audio section
                recordedAudio.style.display = 'block';
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
                
                // Reset UI
                recordBtn.disabled = false;
                stopBtn.disabled = true;
                recordingStatus.style.display = 'none';
            };
            
            // Start countdown
            startCountdown();
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            showError('Microphone access denied. Please allow microphone access and try again.');
            recordBtn.disabled = false;
        }
    }

    // Start 3-second countdown
    function startCountdown() {
        let count = 3;
        countdownNumber.textContent = count;
        countdown.style.display = 'block';
        recordBtn.disabled = true;
        
        countdownInterval = setInterval(() => {
            count--;
            if (count > 0) {
                countdownNumber.textContent = count;
            } else {
                clearInterval(countdownInterval);
                countdown.style.display = 'none';
                startActualRecording();
            }
        }, 1000);
    }

    // Start actual recording after countdown
    function startActualRecording() {
        mediaRecorder.start();
        recordingStatus.style.display = 'block';
        stopBtn.disabled = false;
        recordingTimeLeft = 5;
        recordingTimer.textContent = recordingTimeLeft;
        
        recordingInterval = setInterval(() => {
            recordingTimeLeft--;
            recordingTimer.textContent = recordingTimeLeft;
            
            if (recordingTimeLeft <= 0) {
                stopRecording();
            }
        }, 1000);
    }

    // Stop recording
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        
        clearInterval(recordingInterval);
        clearInterval(countdownInterval);
        
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        countdown.style.display = 'none';
        recordingStatus.style.display = 'none';
    }

    // Convert recorded blob to file and submit
    function useRecording() {
        if (recordedBlob) {
            // Create a File object from the blob
            const file = new File([recordedBlob], 'recorded_audio.webm', {
                type: 'audio/webm;codecs=opus'
            });
            
            // Create a new FileList-like object
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Update UI
            fileName.textContent = 'recorded_audio.webm';
            fileInfo.style.display = 'block';
            submitBtn.disabled = false;
            
            // Hide recorded audio section
            recordedAudio.style.display = 'none';
            
            // Show success message
            showSuccess('Recording ready for analysis!');
        }
    }

    // Reset recording
    function resetRecording() {
        recordedAudio.style.display = 'none';
        recordedBlob = null;
        recordedChunks = [];
        
        // Reset file input
        fileInput.value = '';
        fileInfo.style.display = 'none';
        submitBtn.disabled = true;
    }

    // File validation
    function isAudioFile(file) {
        const audioTypes = ['audio/wav', 'audio/mpeg', 'audio/mp3', 'audio/m4a', 'audio/flac', 'audio/ogg', 'audio/webm'];
        return audioTypes.includes(file.type) || file.name.match(/\.(wav|mp3|m4a|flac|ogg|webm)$/i);
    }

    // File size validation (max 10MB)
    function isValidFileSize(file) {
        return file.size <= 10 * 1024 * 1024; // 10MB
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
        fileLabel.style.border = '3px solid #4caf50';
        fileLabel.style.background = '#e8f5e8';
        submitBtn.disabled = false;

        // Hide recording section if file is selected
        recordedAudio.style.display = 'none';

        // Create audio preview
        createAudioPreview(file);
    }

    // Create audio preview
    function createAudioPreview(file) {
        const url = URL.createObjectURL(file);
        
        // Remove existing preview
        const existingPreview = document.getElementById('audio-preview');
        if (existingPreview) {
            existingPreview.remove();
        }

        // Create new preview
        const preview = document.createElement('div');
        preview.id = 'audio-preview';
        preview.innerHTML = `
            <div class="audio-preview">
                <div class="preview-title">Audio Preview:</div>
                <audio controls>
                    <source src="${url}" type="${file.type}">
                    Your browser does not support the audio element.
                </audio>
                <div class="preview-info">
                    <span>📊 Size: ${formatFileSize(file.size)}</span>
                    <span>⏱️ Type: ${file.type || 'Unknown'}</span>
                </div>
            </div>
        `;
        
        fileInfo.appendChild(preview);
    }

    // Format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
        const container = document.querySelector('.container');
        container.insertBefore(errorDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Show success message
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'flash-message flash-info';
        successDiv.innerHTML = `<span class="flash-icon">ℹ️</span>${message}`;
        
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.flash-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Add new message
        const container = document.querySelector('.container');
        container.insertBefore(successDiv, container.firstChild);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    // Event listeners
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    useRecordingBtn.addEventListener('click', useRecording);
    reRecordBtn.addEventListener('click', resetRecording);

    // File input change event
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        handleFileSelect(file);
    });

    // Drag and drop events
    fileLabel.addEventListener('dragover', function(e) {
        e.preventDefault();
        fileLabel.classList.add('dragover');
    });

    fileLabel.addEventListener('dragleave', function(e) {
        e.preventDefault();
        fileLabel.classList.remove('dragover');
    });

    fileLabel.addEventListener('drop', function(e) {
        e.preventDefault();
        fileLabel.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });

    // Form submission
    uploadForm.addEventListener('submit', function(e) {
        if (fileInput.files.length === 0) {
            e.preventDefault();
            showError('Please select an audio file or record audio first!');
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '🔄 Analyzing...';
        loading.style.display = 'block';

        // Scroll to loading
        loading.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    // Initialize audio context on first user interaction
    document.addEventListener('click', function() {
        if (!audioContext) {
            initAudioContext();
        }
    }, { once: true });

    // Auto-scroll to result if present
    const resultSection = document.querySelector('.result-section');
    if (resultSection) {
        setTimeout(() => {
            resultSection.scrollIntoView({ 
                behavior: 'smooth',
                block: 'center'
            });
        }, 100);
    }

    // Check for microphone support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        recordBtn.disabled = true;
        recordBtn.innerHTML = '<span class="record-icon">❌</span><span class="record-text">Recording Not Supported</span>';
        showError('Audio recording is not supported in your browser. Please use file upload instead.');
    }
});
