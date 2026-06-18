/**
 * CRTCaptcha
 * Affiche un texte via persistance rétinienne, indéchiffrable par OCR/IA.
 *
 * Principe :
 *  - Chaque frame ne montre qu'une tranche de pixels réels + autant de bruit aléatoire
 *  - Le bruit est régénéré à chaque cycle → impossible à neutraliser par somme de frames
 *  - L'œil humain reconstitue l'image, aucun algo ne peut le faire sur capture statique
 *
 * Usage :
 *   const captcha = new CRTCaptcha('#container', {
 *     pixels: [[x,y], ...],   // coordonnées des pixels du texte (espace ORIG_W × ORIG_H)
 *     origW: 83, origH: 48,   // dimensions de la grille source
 *     scale: 8,               // agrandissement
 *     slices: 4,              // tranches par cycle (4 = 80ms/cycle à 20ms/frame)
 *     frameMs: 20,            // délai entre frames (min recommandé : 16ms)
 *     color: [210, 255, 190], // couleur phosphore RGB
 *   });
 *   captcha.start();
 *   captcha.stop();
 *   captcha.destroy();
 */

class CRTCaptcha {
  constructor(selector, options = {}) {
    this.container =
      typeof selector === 'string'
        ? document.querySelector(selector)
        : selector;

    if (!this.container) throw new Error(`CRTCaptcha: element "${selector}" introuvable`);

    const {
      pixels  = [],
      origW   = 83,
      origH   = 48,
      scale   = 8,
      slices  = 4,
      frameMs = 20,
      color   = [210, 255, 190],
    } = options;

    this._pixels  = pixels;
    this._origW   = origW;
    this._origH   = origH;
    this._scale   = scale;
    this._slices  = slices;
    this._frameMs = frameMs;
    this._color   = color;

    this._W = origW * scale;
    this._H = origH * scale;
    this._N = pixels.length;
    this._perSlice = Math.ceil(this._N / slices);

    this._canvas = document.createElement('canvas');
    this._canvas.width  = this._W;
    this._canvas.height = this._H;
    this._canvas.style.imageRendering = 'pixelated';
    this.container.appendChild(this._canvas);

    this._ctx       = this._canvas.getContext('2d');
    this._slice     = 0;
    this._sliceData = [];
    this._lastTime  = 0;
    this._rafId     = null;
    this._running   = false;
  }

  // Mélange Fisher-Yates
  _shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }

  // Reconstruit les tranches avec un ordre aléatoire frais
  _rebuildSlices() {
    const order = this._shuffle([...Array(this._N).keys()]);
    this._sliceData = [];
    for (let s = 0; s < this._slices; s++) {
      this._sliceData.push(
        order
          .slice(s * this._perSlice, (s + 1) * this._perSlice)
          .map(i => this._pixels[i])
      );
    }
  }

  _drawFrame(ts) {
    if (!this._running) return;

    if (ts - this._lastTime >= this._frameMs) {
      this._lastTime = ts;

      if (this._slice === 0) this._rebuildSlices();

      const { _W: W, _H: H, _scale: S, _origW: OW, _origH: OH, _color: C } = this;
      const imgData = this._ctx.createImageData(W, H);
      const d = imgData.data;
      const [R, G, B] = C;

      // Alpha plein partout
      for (let i = 3; i < d.length; i += 4) d[i] = 255;

      const fill = (px, py) => {
        const x0 = px * S, y0 = py * S;
        for (let dy = 0; dy < S; dy++) {
          for (let dx = 0; dx < S; dx++) {
            const idx = ((y0 + dy) * W + (x0 + dx)) * 4;
            d[idx] = R; d[idx + 1] = G; d[idx + 2] = B;
          }
        }
      };

      // Pixels réels de la tranche courante
      for (const [px, py] of this._sliceData[this._slice]) fill(px, py);

      // Bruit aléatoire — même quantité, même couleur, positions fraîches
      const noiseCount = this._sliceData[this._slice].length;
      for (let n = 0; n < noiseCount; n++) {
        const nx = (Math.random() * OW) | 0;
        const ny = (Math.random() * OH) | 0;
        // Ne pas écraser un pixel réel
        if (d[(ny * S * W + nx * S) * 4] === 0) fill(nx, ny);
      }

      this._ctx.putImageData(imgData, 0, 0);
      this._slice = (this._slice + 1) % this._slices;
    }

    this._rafId = requestAnimationFrame(ts => this._drawFrame(ts));
  }

  start() {
    if (this._running) return;
    this._running = true;
    this._rafId = requestAnimationFrame(ts => this._drawFrame(ts));
  }

  stop() {
    this._running = false;
    if (this._rafId) cancelAnimationFrame(this._rafId);
    this._rafId = null;
  }

  destroy() {
    this.stop();
    this._canvas.remove();
  }
}


// ---------------------------------------------------------------------------
// Exemple d'utilisation autonome (supprimer si utilisé comme module)
// ---------------------------------------------------------------------------
const DIGIT_PIXELS_443 = [[22,12],[23,12],[24,12],[44,12],[45,12],[46,12],[61,12],[62,12],[63,12],[64,12],[21,13],[22,13],[23,13],[24,13],[43,13],[44,13],[45,13],[46,13],[57,13],[58,13],[59,13],[60,13],[61,13],[62,13],[63,13],[64,13],[65,13],[66,13],[67,13],[20,14],[21,14],[22,14],[23,14],[24,14],[42,14],[43,14],[44,14],[45,14],[46,14],[55,14],[56,14],[57,14],[58,14],[59,14],[60,14],[61,14],[62,14],[63,14],[64,14],[65,14],[66,14],[67,14],[68,14],[20,15],[21,15],[22,15],[23,15],[24,15],[42,15],[43,15],[44,15],[45,15],[55,15],[56,15],[57,15],[66,15],[67,15],[68,15],[69,15],[19,16],[20,16],[21,16],[23,16],[24,16],[41,16],[42,16],[43,16],[45,16],[46,16],[67,16],[68,16],[69,16],[70,16],[18,17],[19,17],[20,17],[23,17],[24,17],[40,17],[41,17],[42,17],[45,17],[46,17],[68,17],[69,17],[70,17],[18,18],[19,18],[22,18],[23,18],[24,18],[40,18],[41,18],[45,18],[46,18],[68,18],[69,18],[70,18],[17,19],[18,19],[19,19],[22,19],[23,19],[24,19],[39,19],[40,19],[41,19],[44,19],[45,19],[46,19],[68,19],[69,19],[70,19],[16,20],[17,20],[18,20],[23,20],[24,20],[38,20],[39,20],[40,20],[44,20],[45,20],[46,20],[67,20],[68,20],[69,20],[70,20],[15,21],[16,21],[17,21],[22,21],[23,21],[24,21],[37,21],[38,21],[39,21],[44,21],[45,21],[46,21],[67,21],[68,21],[69,21],[15,22],[16,22],[22,22],[23,22],[24,22],[37,22],[38,22],[44,22],[45,22],[46,22],[65,22],[66,22],[67,22],[68,22],[14,23],[15,23],[16,23],[22,23],[23,23],[24,23],[36,23],[37,23],[38,23],[44,23],[45,23],[46,23],[58,23],[59,23],[60,23],[61,23],[62,23],[63,23],[64,23],[65,23],[66,23],[13,24],[14,24],[15,24],[22,24],[23,24],[24,24],[35,24],[36,24],[37,24],[44,24],[45,24],[46,24],[58,24],[59,24],[60,24],[61,24],[62,24],[63,24],[64,24],[65,24],[12,25],[13,25],[14,25],[22,25],[23,25],[24,25],[34,25],[35,25],[36,25],[44,25],[45,25],[46,25],[58,25],[59,25],[61,25],[62,25],[63,25],[64,25],[65,25],[66,25],[67,25],[68,25],[12,26],[13,26],[22,26],[23,26],[24,26],[34,26],[35,26],[44,26],[45,26],[46,26],[66,26],[67,26],[68,26],[69,26],[11,27],[12,27],[13,27],[22,27],[23,27],[24,27],[33,27],[34,27],[35,27],[44,27],[45,27],[46,27],[68,27],[69,27],[70,27],[10,28],[11,28],[12,28],[22,28],[23,28],[24,28],[32,28],[33,28],[34,28],[44,28],[45,28],[46,28],[68,28],[69,28],[70,28],[10,29],[11,29],[22,29],[23,29],[24,29],[32,29],[33,29],[44,29],[45,29],[46,29],[69,29],[70,29],[71,29],[9,30],[10,30],[11,30],[12,30],[13,30],[14,30],[15,30],[16,30],[17,30],[18,30],[19,30],[20,30],[21,30],[22,30],[23,30],[24,30],[25,30],[26,30],[27,30],[28,30],[31,30],[32,30],[33,30],[34,30],[35,30],[36,30],[37,30],[38,30],[39,30],[40,30],[41,30],[42,30],[43,30],[44,30],[45,30],[46,30],[47,30],[48,30],[49,30],[50,30],[69,30],[70,30],[71,30],[9,31],[10,31],[11,31],[12,31],[13,31],[14,31],[15,31],[16,31],[17,31],[18,31],[19,31],[20,31],[21,31],[22,31],[23,31],[24,31],[25,31],[26,31],[27,31],[28,31],[31,31],[32,31],[33,31],[34,31],[35,31],[36,31],[37,31],[38,31],[39,31],[40,31],[41,31],[42,31],[43,31],[44,31],[45,31],[46,31],[47,31],[48,31],[49,31],[50,31],[69,31],[70,31],[71,31],[9,32],[10,32],[11,32],[12,32],[13,32],[14,32],[15,32],[16,32],[17,32],[18,32],[19,32],[20,32],[21,32],[22,32],[23,32],[24,32],[25,32],[26,32],[27,32],[28,32],[31,32],[32,32],[33,32],[34,32],[35,32],[36,32],[37,32],[38,32],[39,32],[40,32],[41,32],[42,32],[43,32],[44,32],[45,32],[46,32],[47,32],[48,32],[49,32],[50,32],[68,32],[69,32],[70,32],[71,32],[22,33],[23,33],[24,33],[44,33],[45,33],[46,33],[68,33],[69,33],[70,33],[22,34],[23,34],[24,34],[44,34],[45,34],[46,34],[67,34],[68,34],[69,34],[70,34],[22,35],[23,35],[24,35],[44,35],[45,35],[46,35],[54,35],[55,35],[66,35],[67,35],[68,35],[69,35],[22,36],[23,36],[24,36],[44,36],[45,36],[46,36],[54,36],[55,36],[56,36],[57,36],[58,36],[59,36],[60,36],[61,36],[62,36],[63,36],[64,36],[65,36],[66,36],[67,36],[68,36],[22,37],[23,37],[24,37],[44,37],[45,37],[46,37],[54,37],[55,37],[56,37],[57,37],[58,37],[59,37],[60,37],[61,37],[62,37],[63,37],[64,37],[65,37],[66,37],[67,37],[22,38],[23,38],[24,38],[44,38],[45,38],[46,38],[58,38],[59,38],[60,38],[61,38],[62,38],[63,38],[64,38]];

document.addEventListener('DOMContentLoaded', () => {
  const captcha = new CRTCaptcha('#captcha', {
    pixels:  DIGIT_PIXELS_443,
    origW:   83,
    origH:   48,
    scale:   8,
    slices:  4,
    frameMs: 20,
    color:   [210, 255, 190],
  });
  captcha.start();
});
