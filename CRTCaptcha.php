<?php
/**
 * CRTCaptcha — Captcha par persistance rétinienne
 *
 * Principe : le texte n'apparaît jamais en entier dans aucune frame.
 * Chaque frame = tranche de pixels réels + bruit aléatoire régénéré côté JS.
 * Indéchiffrable par OCR ou IA sur capture statique.
 *
 * Prérequis : extension GD (php-gd)
 *
 * Usage basique :
 *   <?php
 *   require 'CRTCaptcha.php';
 *   $captcha = new CRTCaptcha('443');          // texte à afficher
 *   $captcha->render();                         // affiche le <canvas> + <script>
 *
 * Usage avancé :
 *   $captcha = new CRTCaptcha('A3F9', [
 *     'scale'    => 8,            // agrandissement pixel (défaut 8)
 *     'slices'   => 4,            // tranches par cycle   (défaut 4)
 *     'frameMs'  => 20,           // ms par frame         (défaut 20)
 *     'color'    => [210,255,190],// couleur phosphore RGB (défaut vert)
 *     'font'     => 5,            // police GD 1-5        (défaut 5)
 *     'id'       => 'my-captcha', // id du canvas HTML    (défaut auto)
 *   ]);
 *   $captcha->render();
 *
 * Validation (côté serveur) :
 *   $captcha->storeInSession();                 // stocke le texte en session
 *   CRTCaptcha::validateSession($_POST['answer']); // true/false
 */

class CRTCaptcha
{
    private string $text;
    private array  $options;
    private array  $pixels = [];
    private int    $origW;
    private int    $origH;

    public function __construct(string $text, array $options = [])
    {
        $this->text    = strtoupper($text);
        $this->options = array_merge([
            'scale'   => 8,
            'slices'  => 4,
            'frameMs' => 20,
            'color'   => [210, 255, 190],
            'font'    => 5,
            'id'      => 'crt-captcha-' . substr(md5(uniqid()), 0, 6),
        ], $options);

        $this->_generatePixels();
    }

    // -----------------------------------------------------------------------
    // Génère la liste des pixels "allumés" du texte via GD
    // -----------------------------------------------------------------------
    private function _generatePixels(): void
    {
        if (!extension_loaded('gd')) {
            throw new \RuntimeException('CRTCaptcha nécessite l\'extension GD (php-gd).');
        }

        $font    = $this->options['font'];
        $padding = 4;

        // Mesure le texte
        $bbox = imagettfbbox(0, 0, '', $this->text); // fallback si pas de TTF
        $charW = imagefontwidth($font);
        $charH = imagefontheight($font);
        $textW = strlen($this->text) * $charW;
        $textH = $charH;

        $this->origW = $textW + $padding * 2;
        $this->origH = $textH + $padding * 2;

        // Crée une image temporaire
        $img = imagecreate($this->origW, $this->origH);
        $bg  = imagecolorallocate($img, 255, 255, 255); // blanc = fond
        $fg  = imagecolorallocate($img, 0,   0,   0  ); // noir  = texte

        imagestring($img, $font, $padding, $padding, $this->text, $fg);

        // Extrait les pixels noirs (texte)
        $this->pixels = [];
        for ($y = 0; $y < $this->origH; $y++) {
            for ($x = 0; $x < $this->origW; $x++) {
                $idx = imagecolorat($img, $x, $y);
                $rgb = imagecolorsforindex($img, $idx);
                $lum = ($rgb['red'] + $rgb['green'] + $rgb['blue']) / 3;
                if ($lum < 128) {
                    $this->pixels[] = [$x, $y];
                }
            }
        }

        imagedestroy($img);
    }

    // -----------------------------------------------------------------------
    // Affiche le HTML + JS inline
    // -----------------------------------------------------------------------
    public function render(): void
    {
        echo $this->getHTML();
    }

    public function getHTML(): string
    {
        $id      = htmlspecialchars($this->options['id']);
        $scale   = (int)$this->options['scale'];
        $slices  = (int)$this->options['slices'];
        $frameMs = (int)$this->options['frameMs'];
        $color   = array_map('intval', $this->options['color']);
        $origW   = $this->origW;
        $origH   = $this->origH;
        $W       = $origW * $scale;
        $H       = $origH * $scale;

        $pixelsJson = json_encode($this->pixels, JSON_THROW_ON_ERROR);
        $colorJson  = json_encode($color);

        return <<<HTML
<canvas id="{$id}"
        width="{$W}"
        height="{$H}"
        style="image-rendering:pixelated;display:block;"
        aria-label="Captcha visuel — lisez les caractères affichés"></canvas>
<script>
(function () {
  var canvas   = document.getElementById('{$id}');
  var ctx      = canvas.getContext('2d');
  var pixels   = {$pixelsJson};
  var color    = {$colorJson};
  var origW    = {$origW}, origH = {$origH};
  var S        = {$scale};
  var W        = {$W},     H     = {$H};
  var N_SLICES = {$slices};
  var FRAME_MS = {$frameMs};
  var N        = pixels.length;
  var perSlice = Math.ceil(N / N_SLICES);
  var slice    = 0;
  var slices   = [];
  var lastTime = 0;
  var R = color[0], G = color[1], B = color[2];

  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = (Math.random() * (i + 1)) | 0;
      var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  function rebuild() {
    var order = shuffle(Array.from({length: N}, function(_, i){ return i; }));
    slices = [];
    for (var s = 0; s < N_SLICES; s++) {
      slices.push(order.slice(s * perSlice, (s + 1) * perSlice).map(function(i){ return pixels[i]; }));
    }
  }

  function fill(d, px, py) {
    var x0 = px * S, y0 = py * S;
    for (var dy = 0; dy < S; dy++) {
      for (var dx = 0; dx < S; dx++) {
        var idx = ((y0 + dy) * W + (x0 + dx)) * 4;
        d[idx] = R; d[idx+1] = G; d[idx+2] = B;
      }
    }
  }

  function frame(ts) {
    if (ts - lastTime >= FRAME_MS) {
      lastTime = ts;
      if (slice === 0) rebuild();

      var img = ctx.createImageData(W, H);
      var d   = img.data;
      for (var i = 3; i < d.length; i += 4) d[i] = 255;

      var cur = slices[slice];
      for (var p = 0; p < cur.length; p++) fill(d, cur[p][0], cur[p][1]);

      // Bruit aléatoire — régénéré à chaque cycle, même couleur, positions uniques
      for (var n = 0; n < cur.length; n++) {
        var nx = (Math.random() * origW) | 0;
        var ny = (Math.random() * origH) | 0;
        if (d[(ny * S * W + nx * S) * 4] === 0) fill(d, nx, ny);
      }

      ctx.putImageData(img, 0, 0);
      slice = (slice + 1) % N_SLICES;
    }
    requestAnimationFrame(frame);
  }

  rebuild();
  requestAnimationFrame(frame);
}());
</script>
HTML;
    }

    // -----------------------------------------------------------------------
    // Helpers session pour validation
    // -----------------------------------------------------------------------
    public function storeInSession(string $key = 'crt_captcha_answer'): void
    {
        if (session_status() === PHP_SESSION_NONE) session_start();
        $_SESSION[$key] = $this->text;
    }

    public static function validateSession(
        string $userAnswer,
        string $key = 'crt_captcha_answer'
    ): bool {
        if (session_status() === PHP_SESSION_NONE) session_start();
        if (empty($_SESSION[$key])) return false;
        $valid = strtoupper(trim($userAnswer)) === $_SESSION[$key];
        unset($_SESSION[$key]); // usage unique
        return $valid;
    }

    // Accesseurs utiles
    public function getText():   string { return $this->text; }
    public function getPixels(): array  { return $this->pixels; }
    public function getOrigW():  int    { return $this->origW; }
    public function getOrigH():  int    { return $this->origH; }
}
HTML;
    }
}
