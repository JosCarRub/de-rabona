
const AI_ENDPOINT = '/api/agent/query-database-agent';

let isListening = false;
let isProcessing = false;
let isSpeaking = false;
let recognition = null;
let speechSynthesis = window.speechSynthesis;
let currentUtterance = null;

let voiceInput, voiceBtn, sendBtn, muteBtn, volumeRange, statusDot, statusText;

document.addEventListener('DOMContentLoaded', function() {
    initializeDOMElements();
    initializeSpeechRecognition();
    initializeEventListeners();
    initializeTextToSpeech();
    updateStatus('ready', 'Listo para escuchar');
});

function initializeDOMElements() {
    voiceInput = document.getElementById('voiceInput');
    voiceBtn = document.getElementById('voiceBtn');
    sendBtn = document.getElementById('sendBtn');
    muteBtn = document.getElementById('muteBtn');
    volumeRange = document.getElementById('volumeRange');
    statusDot = document.getElementById('statusDot');
    statusText = document.getElementById('statusText');
}

function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.lang = 'es-ES';
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        
        recognition.onstart = () => {
            console.log('🎤 Reconocimiento iniciado');
            isListening = true;
            setAnimationState('processing'); // Animación mientras escucha
            updateStatus('listening', 'Escuchando...');
            voiceBtn.classList.add('recording');
        };
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('🎤 Texto reconocido:', transcript);
            voiceInput.value = transcript;
            sendMessage(transcript);
        };
        
        recognition.onerror = (event) => {
            console.error('❌ Error en reconocimiento:', event.error);
            updateStatus('error', 'Error en reconocimiento');
            stopListening();
        };
        
        recognition.onend = () => {
            console.log('🎤 Reconocimiento terminado');
            stopListening();
        };
    } else {
        console.log('❌ Reconocimiento de voz no disponible');
        if (voiceBtn) voiceBtn.style.display = 'none';
    }
}

// Inicializar text-to-speech
function initializeTextToSpeech() {
    if ('speechSynthesis' in window) {
        console.log('🔊 Text-to-Speech disponible');
        
        // Cargar voces
        speechSynthesis.addEventListener('voiceschanged', () => {
            console.log('🔊 Voces cargadas:', speechSynthesis.getVoices().length);
        });
    } else {
        console.log('❌ Text-to-Speech no disponible');
    }
}

// Inicializar event listeners
function initializeEventListeners() {
    // Botón de voz
    if (voiceBtn) {
        voiceBtn.addEventListener('click', toggleListening);
    }
    
    // Botón de enviar
    if (sendBtn) {
        sendBtn.addEventListener('click', () => {
            const message = voiceInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        });
    }
    

    if (voiceInput) {
        voiceInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = voiceInput.value.trim();
                if (message) {
                    sendMessage(message);
                }
            }
        });
    }
    
    // Botón de silenciar
    if (muteBtn) {
        muteBtn.addEventListener('click', toggleMute);
    }
    
    // Control de volumen
    if (volumeRange) {
        volumeRange.addEventListener('input', (e) => {
            const volume = e.target.value / 100;
            if (currentUtterance) {
                currentUtterance.volume = volume;
            }
        });
    }
}

// Toggle del micrófono
function toggleListening() {
    if (!recognition) {
        console.log('❌ Reconocimiento no disponible');
        return;
    }
    
    if (isListening) {
        stopListening();
    } else {
        startListening();
    }
}

// Iniciar escucha
function startListening() {
    if (isProcessing || isSpeaking) {
        return;
    }
    
    try {
        recognition.start();
    } catch (error) {
        console.error('Error iniciando reconocimiento:', error);
        updateStatus('error', 'Error iniciando micrófono');
    }
}

// Detener escucha
function stopListening() {
    isListening = false;
    if (voiceBtn) voiceBtn.classList.remove('recording');
    setAnimationState('idle');
    updateStatus('ready', 'Listo para escuchar');
    
    if (recognition) {
        try {
            recognition.stop();
        } catch (error) {
            console.log('Error deteniendo reconocimiento:', error);
        }
    }
}

// Enviar mensaje al AI
async function sendMessage(message) {
    if (isProcessing || !message.trim()) return;
    
    isProcessing = true;
    setAnimationState('processing'); // Activar animación de procesamiento
    updateStatus('processing', 'Procesando...');
    if (sendBtn) sendBtn.disabled = true;
    voiceInput.value = '';
    
    try {
        const response = await fetch(AI_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message
            })
        });
        
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (data.answer) {
            await speakResponse(data.answer);
        } else {
            throw new Error('Respuesta vacía del servidor');
        }
        
    } catch (error) {
        console.error('Error comunicándose con IA:', error);
        updateStatus('error', `Error: ${error.message}`);
        await speakResponse(`Lo siento, ha ocurrido un error: ${error.message}`);
    } finally {
        isProcessing = false;
        if (sendBtn) sendBtn.disabled = false;
        setAnimationState('idle');
        updateStatus('ready', 'Listo para escuchar');
    }
}

// Hablar respuesta
async function speakResponse(text) {
    return new Promise((resolve) => {
        if (!speechSynthesis) {
            console.log('❌ Speech synthesis no disponible');
            resolve();
            return;
        }
        
        // Detener cualquier speech anterior
        speechSynthesis.cancel();
        
        // Limpiar texto
        const cleanText = text
            .replace(/<[^>]*>/g, '')
            .replace(/\*\*(.*?)\*\*/g, '$1')
            .replace(/\*(.*?)\*/g, '$1')
            .replace(/•/g, '')
            .trim();
        
        if (!cleanText) {
            resolve();
            return;
        }
        
        // Crear utterance
        currentUtterance = new SpeechSynthesisUtterance(cleanText);
        
        // Configurar voz en español
        const voices = speechSynthesis.getVoices();
        const spanishVoice = voices.find(voice => 
            voice.lang.includes('es') || 
            voice.name.toLowerCase().includes('spanish')
        );
        
        if (spanishVoice) {
            currentUtterance.voice = spanishVoice;
        }
        
        currentUtterance.lang = 'es-ES';
        currentUtterance.rate = 0.9;
        currentUtterance.pitch = 1.0;
        currentUtterance.volume = volumeRange ? volumeRange.value / 100 : 0.8;
        
        // Event listeners
        currentUtterance.onstart = () => {
            console.log('🔊 Hablando...');
            isSpeaking = true;
            setAnimationState('speaking'); // Activar animación de habla
            updateStatus('speaking', 'Hablando...');
        };
        
        currentUtterance.onend = () => {
            console.log('🔊 Speech terminado');
            isSpeaking = false;
            setAnimationState('idle');
            updateStatus('ready', 'Listo para escuchar');
            resolve();
        };
        
        currentUtterance.onerror = (event) => {
            console.error('❌ Error en speech:', event.error);
            isSpeaking = false;
            setAnimationState('idle');
            updateStatus('error', 'Error en síntesis de voz');
            resolve();
        };
        
        // Hablar
        speechSynthesis.speak(currentUtterance);
    });
}

// Actualizar estado general
function updateStatus(status, text) {
    if (statusText) statusText.textContent = text;
    
    // Actualizar indicador visual
    if (statusDot) {
        statusDot.className = 'status-dot';
        switch (status) {
            case 'ready':
                statusDot.style.background = '#00d4b1';
                break;
            case 'listening':
                statusDot.style.background = '#ffd700';
                break;
            case 'processing':
                statusDot.style.background = '#ff9500';
                break;
            case 'speaking':
                statusDot.style.background = '#00bfff';
                break;
            case 'error':
                statusDot.style.background = '#ff6b6b';
                break;
        }
    }
}

// Toggle mute
function toggleMute() {
    if (!muteBtn || !volumeRange) return;
    
    const icon = muteBtn.querySelector('i');
    if (speechSynthesis.paused || volumeRange.value == 0) {
        speechSynthesis.resume();
        volumeRange.value = 80;
        if (icon) icon.className = 'fas fa-volume-up';
    } else {
        speechSynthesis.pause();
        volumeRange.value = 0;
        if (icon) icon.className = 'fas fa-volume-mute';
    }
}


function setAnimationState(state) {
    if (typeof window.setAnimationState === 'function') {
        window.setAnimationState(state);
    } else {
        console.log('⚠️ setAnimationState no disponible aún, estado:', state);
    }
}