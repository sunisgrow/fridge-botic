// Mini App for DataMatrix/QR/EAN scanning
// Uses html5-qrcode library and Telegram WebApp SDK

let html5Qrcode = null;
let isScanning = false;
let currentCameraId = null;
let torchAvailable = false;
let cachedCameras = null;

// Initialize Telegram WebApp
const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

if (tg) {
    tg.expand(); // Разворачиваем на весь экран
    tg.ready(); // Сообщаем, что приложение готово
    console.log('Telegram WebApp initialized', tg.platform, 'version:', tg.version);
    
    // Настраиваем основную кнопку Telegram
    tg.MainButton.setText('Сканировать').hide();
    tg.onEvent('mainButtonClicked', () => {
        startScanner();
    });
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
let audioContext = null;

function initAudio() {
    if (!audioContext && window.AudioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        // Resume on user interaction
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
    }
    return audioContext;
}

function playBeep() {
    try {
        const ctx = initAudio();
        if (!ctx) return;
        
        const oscillator = ctx.createOscillator();
        const gainNode = ctx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(ctx.destination);
        
        oscillator.frequency.value = 1800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.15);
        
        oscillator.start(ctx.currentTime);
        oscillator.stop(ctx.currentTime + 0.15);
    } catch (e) {
        console.log('Audio not supported:', e);
    }
}

function playSuccess() {
    playBeep();
    setTimeout(playBeep, 100);
}

function updateStatus(text, isActive = false, isError = false) {
    const dot = statusDiv.querySelector('.status-dot');
    const textSpan = statusDiv.querySelector('.status-text');
    
    if (textSpan) {
        textSpan.textContent = text;
    }
    if (dot) {
        dot.classList.toggle('active', isActive);
        dot.classList.toggle('error', isError);
    }
    console.log('Status:', text);
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

function showError(text, isPermanent = false) {
    errorText.textContent = text;
    
    errorDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    
    updateStatus(text, false, true);
    
    if (!isPermanent) {
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    }
}

function sendToBot(text, format) {
    // Extract GTIN from DataMatrix if possible
    let gtin = null;
    let serial = null;
    let rawData = text;
    
    // Try to parse GS1 format
    const gtinMatch = text.match(/\(01\)(\d{14})/);
    if (gtinMatch) {
        gtin = gtinMatch[1];
    } else if (text.match(/^\d{14}$/)) {
        gtin = text;
    } else if (text.match(/^\d{13}$/)) {
        gtin = '0' + text;
    } else if (text.match(/^\d{8}$/)) {
        gtin = '000000' + text;
    }
    
    const serialMatch = text.match(/\(21\)([^(\)]+)/);
    if (serialMatch) {
        serial = serialMatch[1].trim();
    }
    
    const result = {
        raw: rawData,
        format: format,
        gtin: gtin,
        serial: serial,
        timestamp: new Date().toISOString()
    };
    
    console.log('Sending to bot:', result);
    
    if (tg) {
        // Отправляем данные в бот
        tg.sendData(JSON.stringify(result));
        updateStatus('Код отправлен!', false);
        
        // Показываем уведомление через Telegram
        tg.showPopup({
            title: 'Успех',
            message: `Код ${text.substring(0, 20)}${text.length > 20 ? '...' : ''} отправлен`,
            buttons: [{type: 'ok'}]
        });
        
        // Закрываем mini app через 1.5 секунды
        setTimeout(() => {
            tg.close();
        }, 1500);
    } else {
        console.log('No Telegram WebApp available');
        updateStatus('Код найден: ' + text.substring(0, 30), false);
    }
}

async function startScanner() {
    if (isScanning) {
        console.log('Scanner already running');
        return;
    }
    
    // Проверяем поддержку getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Ваш браузер не поддерживает доступ к камере\n\nИспользуйте современный браузер (Chrome, Safari, Firefox)', true);
        return;
    }
    
    // Проверяем HTTPS (обязательно для getUserMedia)
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        showError('Для доступа к камере требуется HTTPS соединение\n\nТекущий протокол: ' + location.protocol, true);
        return;
    }
    
    // Проверяем, что библиотека загружена
    if (typeof Html5Qrcode === 'undefined') {
        showError('Библиотека сканирования не загружена\nПроверьте интернет-соединение', true);
        return;
    }
    
    isScanning = true;
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    startBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    
    updateStatus('Запрос доступа к камере...', true);
    
    try {
        // Получаем список доступных камер (используем кэш если есть)
        let cameras = cachedCameras;
        if (!cameras) {
            cameras = await Html5Qrcode.getCameras();
            cachedCameras = cameras;
        }
        console.log('Available cameras:', cameras);
        
        if (!cameras || cameras.length === 0) {
            throw new Error('Камеры не найдены на устройстве');
        }
        
        // Выбираем заднюю камеру если есть
        const backCamera = cameras.find(camera => 
            camera.label.toLowerCase().includes('back') || 
            camera.label.toLowerCase().includes('environment') ||
            camera.label.toLowerCase().includes('rear')
        );
        
        currentCameraId = backCamera ? backCamera.id : cameras[0].id;
        console.log('Selected camera:', currentCameraId);
        
        // Создаем конфигурацию для сканера
        const config = {
            fps: 15,
            qrbox: { width: 280, height: 280 },
            aspectRatio: 1.0,
            rememberLastUsedCamera: true,
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
            ]
        };
        
        // Инициализируем сканер
        html5Qrcode = new Html5Qrcode("reader");
        
        updateStatus('Запуск камеры...', true);
        
        // Запускаем сканирование
        await html5Qrcode.start(
            currentCameraId,
            config,
            (decodedText, decodedResult) => {
                // Успешное сканирование
                console.log('Code found:', decodedText);
                
                // Останавливаем сканирование
                if (html5Qrcode && isScanning) {
                    html5Qrcode.stop().then(() => {
                        isScanning = false;
                        startBtn.classList.remove('hidden');
                        stopBtn.classList.add('hidden');
                        torchBtn.classList.add('hidden');
                        
                        const formatName = getFormatName(decodedResult.result.format.formatName);
                        showResult(decodedText, formatName);
                    }).catch(err => {
                        console.error('Error stopping scanner:', err);
                        isScanning = false;
                    });
                }
            },
            (errorMessage) => {
                // Игнорируем ошибки сканирования (они возникают постоянно)
                // Но логируем для отладки
                if (errorMessage && !errorMessage.includes('No MultiFormat')) {
                    console.debug('Scan error:', errorMessage);
                }
            }
        );
        
        updateStatus('Сканирование... Наведите камеру на штрихкод', true);
        
        // Проверяем поддержку фонарика
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { deviceId: { exact: currentCameraId } }
            });
            const track = stream.getVideoTracks()[0];
            if (track) {
                const capabilities = track.getCapabilities();
                if (capabilities.torch) {
                    torchAvailable = true;
                    torchBtn.classList.remove('hidden');
                    
                    let torchOn = false;
                    torchBtn.onclick = async () => {
                        try {
                            torchOn = !torchOn;
                            await track.applyConstraints({
                                advanced: [{ torch: torchOn }]
                            });
                            torchBtn.textContent = torchOn ? '🔦 Фонарик (вкл)' : '🔦 Фонарик';
                        } catch (e) {
                            console.log('Torch toggle failed:', e);
                        }
                    };
                }
            }
            stream.getTracks().forEach(track => track.stop());
        } catch (e) {
            console.log('Torch not supported:', e);
        }
        
    } catch (err) {
        console.error('Failed to start scanner:', err);
        isScanning = false;
        startBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        
        let errorMessage = 'Не удалось запустить камеру.\n\n';
        
        if (err.message && err.message.includes('Permission')) {
            errorMessage += '❌ Разрешите доступ к камере:\n';
            errorMessage += '• В Telegram: нажмите ⋮ → Настройки → Камера\n';
            errorMessage += '• В браузере: нажмите на 🔒 в адресной строке\n';
            errorMessage += '• Разрешите доступ и перезагрузите страницу';
        } else if (err.message && err.message.includes('not found')) {
            errorMessage += '📱 Камера не обнаружена на устройстве.\n';
            errorMessage += 'Убедитесь, что камера работает и доступна.';
        } else {
            errorMessage += err.message || 'Неизвестная ошибка';
        }
        
        showError(errorMessage, true);
        updateStatus('Ошибка доступа к камере', false, true);
    }
}

async function stopScanner() {
    if (!isScanning) return;
    
    try {
        if (html5Qrcode && html5Qrcode.isScanning) {
            await html5Qrcode.stop();
        }
    } catch (err) {
        console.error('Error stopping scanner:', err);
    }
    
    isScanning = false;
    startBtn.classList.remove('hidden');
    stopBtn.classList.add('hidden');
    torchBtn.classList.add('hidden');
    torchAvailable = false;
    
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
if (startBtn) {
    startBtn.addEventListener('click', (e) => {
        e.preventDefault();
        startScanner();
    });
}

if (stopBtn) {
    stopBtn.addEventListener('click', (e) => {
        e.preventDefault();
        stopScanner();
    });
}

// Проверка поддержки камеры при загрузке
async function checkCameraSupport() {
    console.log('Checking camera support...');
    
    // Проверяем наличие необходимых API
    if (typeof Html5Qrcode === 'undefined') {
        console.error('Html5Qrcode library not loaded');
        updateStatus('Загрузка библиотеки...', false);
        
        // Ждем загрузки библиотеки
        let attempts = 0;
        const checkInterval = setInterval(() => {
            if (typeof Html5Qrcode !== 'undefined') {
                clearInterval(checkInterval);
                checkCameraSupport();
            } else if (attempts++ > 20) {
                clearInterval(checkInterval);
                showError('Не удалось загрузить библиотеку сканирования\nПроверьте интернет-соединение', true);
            }
        }, 500);
        return;
    }
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Ваш браузер не поддерживает доступ к камере\n\nРекомендуем использовать:\n• Chrome на Android\n• Safari на iOS\n• Telegram Desktop на ПК', true);
        updateStatus('Камера не поддерживается', false, true);
        return;
    }
    
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        showError('⚠️ Для работы камеры требуется HTTPS\n\nТекущий протокол: ' + location.protocol, true);
        updateStatus('Требуется HTTPS', false, true);
        return;
    }
    
    // Кэшируем список камер сразу (один раз запросит разрешение)
    try {
        cachedCameras = await Html5Qrcode.getCameras();
        console.log('Cameras found:', cachedCameras.length);
        
        if (cachedCameras && cachedCameras.length > 0) {
            updateStatus('✅ Камера готова. Нажмите "Начать сканирование"');
            
            // Показываем уведомление в Telegram
            if (tg && tg.platform !== 'unknown') {
                tg.showPopup({
                    title: 'Готов к работе',
                    message: 'Камера обнаружена. Нажмите кнопку "Начать сканирование" для запуска',
                    buttons: [{type: 'ok'}]
                });
            }
        } else {
            updateStatus('❌ Камера не обнаружена', false, true);
            showError('Камера не найдена на вашем устройстве\n\nУбедитесь, что:\n• Устройство имеет камеру\n• Доступ к камере разрешен\n• Вы используете поддерживаемый браузер');
        }
    } catch (err) {
        console.error('Camera check failed:', err);
        updateStatus('Нажмите "Начать сканирование" для доступа к камере', true);
    }
}

// Запускаем проверку после загрузки страницы
window.addEventListener('load', () => {
    console.log('Page loaded, initializing...');
    checkCameraSupport();
});

// Обработка закрытия приложения
if (tg) {
    tg.onEvent('viewportChanged', () => {
        console.log('Viewport changed');
    });
}

// Экспортируем функции для отладки
window.debugScanner = {
    start: startScanner,
    stop: stopScanner,
    check: checkCameraSupport
};