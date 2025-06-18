// Ein einfacher Konsolen-Logger, um die Server-Abhängigkeit zu erfüllen.
const logger = {
    info: (...args) => console.log('[INFO]', ...args),
    error: (...args) => console.error('[ERROR]', ...args),
    warn: (...args) => console.warn('[WARN]', ...args),
    debug: (...args) => console.log('[DEBUG]', ...args),
    // Die child-Methode wird für die Kompatibilität mit dem bestehenden Code benötigt.
    child: function() { return this; } 
};

module.exports = logger;
