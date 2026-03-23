// Mini App for DataMatrix/QR/EAN scanning
// Uses html5-qrcode library and Telegram WebApp SDK

let html5Qrcode = null;
let isScanning = false;

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

async function sendToBot(text, format) {
    console.log('Sending scan data:', { text, format });
    
    const scanData = JSON.stringify({
        raw: text,
        scan_format: format
    });
    
    // Use tg.sendData to send data back to bot
    // This works with KeyboardButton (not InlineKeyboardButton)
    if (tg && tg.sendData) {
        tg.sendData(scanData);
        
        updateStatus('Код отправлен!', false);
        tg.showPopup({
            title: 'Успех',
            message: `Код ${text.substring(0, 20)}${text.length > 20 ? '...' : ''} отправлен`,
            buttons: [{type: 'ok'}]
        });
        
        // Close the WebApp after a short delay
        setTimeout(() => {
            tg.close();
        }, 1000);
    } else {
        // Fallback: send to API (for debugging or if sendData not available)
        console.log('tg.sendData not available, falling back to API');
        
        try {
            const telegramId = tg.initDataUnsafe?.user?.id;
            
            if (!telegramId) {
                console.error('No telegram ID available');
                tg.showPopup({
                    title: 'Ошибка',
                    message: 'Не удалось определить пользователя',
                    buttons: [{type: 'ok'}]
                });
                return;
            }
            
            const apiUrl = window.location.origin + '/api/v1/scan/webapp';
            
            const response = await fetch(`${apiUrl}?telegram_id=${telegramId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: scanData
            });
            
            if (response.ok) {
                updateStatus('Код отправлен!', false);
                tg.showPopup({
                    title: 'Успех',
                    message: `Код ${text.substring(0, 20)}${text.length > 20 ? '...' : ''} отправлен`,
                    buttons: [{type: 'ok'}]
                });
                setTimeout(() => {
                    tg.close();
                }, 1500);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('Error sending to API:', error);
            updateStatus('Ошибка отправки', false, true);
            tg.showPopup({
                title: 'Ошибка',
                message: 'Не удалось отправить данные. Попробуйте еще раз.',
                buttons: [{type: 'ok'}]
            });
        }
    }
}

async function startScanner() {
    if (isScanning) {
        console.log('Scanner already running');
        return;
    }
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Ваш браузер не поддерживает доступ к камере', true);
        return;
    }
    
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        showError('Для доступа к камере требуется HTTPS соединение', true);
        return;
    }
    
    if (typeof Html5Qrcode === 'undefined') {
        showError('Библиотека сканирования не загружена', true);
        return;
    }
    
    isScanning = true;
    resultDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    startBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    
    updateStatus('Запуск камеры...', true);
    
    try {
        // Инициализируем сканер сразу
        html5Qrcode = new Html5Qrcode("reader");
        
        // Конфигурация: используем environment (заднюю камеру) по умолчанию
        // Это избавляет от необходимости вызывать getCameras() отдельно
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
        
        // Запускаем сканирование
        // Используем { facingMode: "environment" } вместо ID камеры
        await html5Qrcode.start(
            { facingMode: "environment" }, 
            config,
            (decodedText, decodedResult) => {
                // Успешное сканирование
                console.log('Code found:', decodedText);
                
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
                // Игнорируем ошибки сканирования
            }
        );
        
        updateStatus('Сканирование... Наведите камеру на штрихкод', true);
        
        // --- УПРОЩЕННАЯ ЛОГИКА ФОНАРИКА ---
        // Мы не создаем новый поток! Пробуем применить ограничения к текущему.
        // К сожалению, html5-qrcode не дает простого доступа к треку, 
        // поэтому надежнее просто скрыть кнопку фонарика или управлять ею через API библиотеки, если версия новая.
        // В старых версиях библиотеки управлять фонариком сложно без хаков.
        // Лучший вариант здесь — убрать блок с getUserMedia полностью.
        torchBtn.classList.add('hidden'); // Скрываем кнопку фонарика для простоты, или используем API библиотеки, если оно есть.
        // Если очень нужен фонарик, его можно включить через scanStart callback в новых версиях библиотеки.

    } catch (err) {
        console.error('Failed to start scanner:', err);
        isScanning = false;
        startBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        
        let errorMessage = 'Не удалось запустить камеру.\n\n';
        
        if (err.message && err.message.includes('Permission')) {
            errorMessage += '❌ Разрешите доступ к камере в настройках браузера или Telegram.';
        } else if (err.message && err.message.includes('not found')) {
            errorMessage += '📱 Камера не обнаружена.';
        } else {
            errorMessage += err.message || 'Неизвестная ошибка';
        }
        
        showError(errorMessage, true);
        updateStatus('Ошибка доступа к камере', false, true);
    }
}

function stopScanner() {
    if (html5Qrcode && isScanning) {
        html5Qrcode.stop().then(() => {
            html5Qrcode.clear();
            isScanning = false;
            startBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
            readerDiv.classList.add('hidden');
            updateStatus('Сканирование остановлено');
        }).catch(err => {
            console.error('Error stopping scanner:', err);
        });
    } else {
        console.log('Scanner not running');
    }
}

function getFormatName(format) {
    return format;
}
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

// Проверка поддержки камеры при загрузке (разрешение запрашивается только в startScanner)
async function checkCameraSupport() {
    console.log('Checking camera support...');
    
    // Проверяем наличие библиотеки
    if (typeof Html5Qrcode === 'undefined') {
        console.error('Html5Qrcode library not loaded');
        updateStatus('Загрузка библиотеки...', false);
        
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
    
    // Проверяем базовую поддержку
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Ваш браузер не поддерживает доступ к камере', true);
        updateStatus('Камера не поддерживается', false, true);
        return;
    }
    
    if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        showError('⚠️ Для работы камеры требуется HTTPS', true);
        updateStatus('Требуется HTTPS', false, true);
        return;
    }
    
    // Разрешение камеры запрашивается автоматически при startScanner()
    updateStatus('Готов к сканированию. Нажмите "Начать сканирование".');
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