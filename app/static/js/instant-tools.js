export const InstantTools = {
  wordCounter: (text) => ({ words: (text.trim().match(/\S+/g) || []).length, chars: text.length }),
  caseConverter: (text) => ({ upper: text.toUpperCase(), lower: text.toLowerCase(), title: text.replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()) }),
  passwordGenerator: (length = 16) => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+';
    return crypto.getRandomValues(new Uint32Array(length)).reduce((a, n) => a + chars[n % chars.length], '');
  },
  base64EncodeDecode: (input, mode = 'encode') => mode === 'encode' ? btoa(unescape(encodeURIComponent(input))) : decodeURIComponent(escape(atob(input))),
  qrCodeUrl: (text, size = 240) => `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(text)}`
};
