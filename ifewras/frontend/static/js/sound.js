/**
 * FloodCast AI sound helpers: synthesised buzzer (Web Audio, no audio files) and
 * AI voice playback (Web Speech API). Shared by the control centre and the resident view.
 */
const FCSound = (() => {
    let ctx = null;

    // Browsers only allow audio after a user gesture; call this from any click.
    function unlock() {
        try {
            if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
            if (ctx.state === 'suspended') ctx.resume();
        } catch (e) { /* audio unavailable */ }
        return !!ctx;
    }

    /**
     * Alarm buzzer: alternating two-tone square-wave pulses.
     * @param {object} opts pulses (count), volume (0-1), pulseMs
     */
    function buzzer({ pulses = 4, volume = 0.6, pulseMs = 260 } = {}) {
        if (!unlock() || volume <= 0) return Promise.resolve();
        const start = ctx.currentTime + 0.02;
        const step = pulseMs / 1000;
        const gain = ctx.createGain();
        gain.connect(ctx.destination);
        gain.gain.setValueAtTime(0, start);

        const osc = ctx.createOscillator();
        osc.type = 'square';
        osc.connect(gain);
        for (let i = 0; i < pulses * 2; i++) {
            const t = start + i * step;
            osc.frequency.setValueAtTime(i % 2 === 0 ? 880 : 620, t);
            gain.gain.setValueAtTime(volume * 0.35, t);
            gain.gain.setValueAtTime(0, t + step * 0.85);
        }
        const end = start + pulses * 2 * step;
        osc.start(start);
        osc.stop(end + 0.05);
        return new Promise(resolve => setTimeout(resolve, (end - ctx.currentTime) * 1000 + 80));
    }

    // Voice fallbacks: Assamese voices are rare, Bengali shares the script.
    const VOICE_FALLBACKS = {
        english: ['en-IN', 'en-GB', 'en-US', 'en'],
        hindi: ['hi-IN', 'hi'],
        assamese: ['as-IN', 'as', 'bn-IN', 'bn', 'hi-IN'],
    };

    function pickVoice(language) {
        if (!('speechSynthesis' in window)) return null;
        const voices = speechSynthesis.getVoices();
        for (const tag of VOICE_FALLBACKS[language] || VOICE_FALLBACKS.english) {
            const v = voices.find(x => x.lang.toLowerCase().replace('_', '-').startsWith(tag.toLowerCase()));
            if (v) return v;
        }
        return null;
    }

    /** Speak an alert script with the best available AI voice for the language. */
    function speak(text, language = 'english') {
        return new Promise(resolve => {
            if (!('speechSynthesis' in window)) return resolve({ ok: false, voice: null });
            speechSynthesis.cancel();
            const u = new SpeechSynthesisUtterance(text);
            const voice = pickVoice(language);
            if (voice) { u.voice = voice; u.lang = voice.lang; }
            else u.lang = (VOICE_FALLBACKS[language] || ['en-IN'])[0];
            u.rate = 0.92;
            u.onend = () => resolve({ ok: true, voice: voice ? voice.name : 'browser default' });
            u.onerror = () => resolve({ ok: false, voice: voice ? voice.name : null });
            speechSynthesis.speak(u);
        });
    }

    if ('speechSynthesis' in window) speechSynthesis.getVoices(); // warm the voice list

    return { unlock, buzzer, speak, pickVoice };
})();
