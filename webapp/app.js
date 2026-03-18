// Mini App for DataMatrix/QR/EAN scanning
// Uses html5-qrcode library

let html5QrcodeScanner = null;
let isScanning = false;

// Initialize Telegram WebApp
if (window.Telegram && window.Telegram.WebApp) {
    window.Telegram.WebApp.expand();
    window.Telegram.WebApp.ready();
}

// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const torchBtn = document.getElementById('torchBtn');
const resultDiv = document.getElementById('result');
const resultText = document.getElementById('result-text');
const resultFormat = document.getElementById('result-format');
const errorDiv = document.getElementById('error');
const errorText = document.getElementById('error-text');
const statusDiv = document.getElementById('status');
const readerDiv = document.getElementById('reader');

// Audio for beep
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

function playBeep() {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 1800;
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.15);
}

function playSuccess() {
    playBeep();
    setTimeout(playBeep, 100);
    setTimeout(playBeep, 200);
}

function updateStatus(text, isActive = false, isError = false) {
    const dot = statusDiv.querySelector('.status-dot');
    const textSpan = statusDiv.querySelector('.status-text');
    
    textSpan.textContent = text;
    dot.classList.toggle('active', isActive);
    dot.classList.toggle('error', isError);
}

function showResult(text, format) {
    resultText.textContent = text;
    resultFormat.textContent = format;
    
    resultDiv.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    
    playSuccess();
    
    // Send result to bot
    sendToBot(text, format);
}

function showError(text) {
    errorText.textContent = text;
    
    errorDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    
    updateStatus(text, false, true);
}

function sendToBot(text, format) {
    // Extract GTIN from DataMatrix if possible
    let gtin = null;
    let serial = null;
    let rawData = text;
    
    // Try to parse GS1 format
    // Format: (01)04607163091577(21)5nf+.FSH8B%NW(93)0bBq
    const gtinMatch = text.match(/\(01\)(\d{14})/);
    if (gtinMatch) {
        gtin = gtinMatch[1];
    } else if (text.match(/^\d{14}$/)) {
        gtin = text;
    }
    
    const serialMatch = text.match(/\(21\)([^(\)]+)/);
    if (serialMatch) {
        serial = serialMatch[1].trim();
    }
    
    const result = {
        raw: rawData,
        format: format,
        gtin: gtin,
        serial: serial
    };
    
    console.log('Sending to bot:', result);
    
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.sendData(JSON.stringify(result));
        window.Telegram.WebApp.close();
    }
}

function startScanner() {
    if (isScanning) return;
    
    isScanning = true;
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    startBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    
    updateStatus('Сканирование...', true);
    
    // Create scanner config
    const config = {
        fps: 10,
        qrbox: {
            width: 250,
            height: 250
        },
        aspectRatio: 1.0,
        supportedFormats: [
            Html5QrcodeSupportedFormats.DATA_MATRIX,
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.CODE_93
        ],
        rememberLastUsedCamera: true
    };
    
    html5QrcodeScanner = new Html5QrcodeScanner(
        'reader',
        config,
        /* verbose= */ false
    );
    
    html5QrcodeScanner.render(
        (decodedText, decodedResult) => {
            // Code found!
            console.log('Code found:', decodedText, decodedResult.result.format);
            
            // Stop scanning
            html5QrcodeScanner.clear();
            isScanning = false;
            
            // Show result
            const formatName = getFormatName(decodedResult.result.format);
            showResult(decodedText, formatName);
        },
        (errorMessage) => {
            // Ignore scan errors (they happen frequently when no code is in frame)
            // console.log('Scan error:', errorMessage);
        }
    );
}

function stopScanner() {
    if (!isScanning) return;
    
    if (html5QrcodeScanner) {
        html5QrcodeScanner.clear();
    }
    
    isScanning = false;
    startBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
    
    updateStatus('Готов к сканированию');
}

function getFormatName(format) {
    const formatNames = {
        'DATA_MATRIX': 'DataMatrix (Честный знак)',
        'QR_CODE': 'QR код',
        'EAN_13': 'EAN-13',
        'EAN_8': 'EAN-8',
        'UPC_A': 'UPC-A',
        'UPC_E': 'UPC-E',
        'CODE_128': 'Code 128',
        'CODE_39': 'Code 39',
        'CODE_93': 'Code 93'
    };
    
    return formatNames[format] || format;
}

// Event listeners
startBtn.addEventListener('click', () => {
    startScanner();
});

stopBtn.addEventListener('click', () => {
    stopScanner();
});

// Check if device supports camera
async function checkCamera() {
    try {
        const devices = await Html5Qrcode.getCameras();
        if (devices && devices.length > 0) {
            updateStatus('Камера найдена. Нажмите "Начать сканирование"');
            
            // Check for torch capability
            const device = devices.find(d => d.label.toLowerCase().includes('back')) || devices[0];
            if (device) {
                try {
                    const capabilities = await navigator.mediaDevices.getUserMedia({
                        video: { deviceId: device.id }
                    });
                    const track = capabilities.getVideoTrack();
                    const capabilities2 = track.getCapabilities();
                    if (capabilities2.torch) {
                        torchBtn.classList.remove('hidden');
                    }
                } catch (e) {
                    // Torch not supported
                }
            }
        } else {
            showError('Камера не найдена');
        }
    } catch (e) {
        showError('Нет доступа к камере');
    }
}

// Initialize
checkCamera();
