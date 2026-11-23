/* ==========================================================================
   Květiny v rozích pozvánky se mírně pohnou, když přes ně přejede myš
   (nebo prst).

   Každý roh je obrázek otáčený kolem svého rohu stránky. Úhel řídí tlumená
   pružina (stejný princip jako vítr v louce na webu Áji a Daníka):
     - pohyb ukazatele v blízkosti rohu dá pružině impuls, který je tím
       větší, čím je ukazatel blíž a čím rychleji se pohybuje;
     - směr kývnutí je dán tím, na kterou stranu od rohu ukazatel míří
       (moment síly = vektorový součin polohy a rychlosti);
     - pružina se vrací do klidu a mírně překmitne.
   Pod prefers-reduced-motion se nehýbe nic.

   Ladění: konstanty hned níže.
   ========================================================================== */
(function () {
  'use strict';

  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var DOSAH = 340;       // px od středu květiny, kam až ukazatel působí
  var SILA = 0.0009;     // jak moc impuls rozhoupe (stupně na px pohybu)
  var MAX_UHEL = 4;    // největší výchylka ve stupních
  var TUHOST = 0.045;    // pružina: vyšší = rychleji zpět
  var TLUMENI = 0.86;    // 1 = netlumeno, nižší = rychleji se usadí

  var rohy = Array.prototype.map.call(document.querySelectorAll('.kvet[data-roh]'), function (el) {
    return { el: el, uhel: 0, rychlost: 0, stred: { x: 0, y: 0 }, hnuto: false };
  });
  if (!rohy.length) return;

  function zmerit() {
    rohy.forEach(function (r) {
      // Střed viditelné plochy bez otočení: počítáme z rozměrů, ne z rámečku
      // (ten se při otočení mění).
      var vedle = r.el.getAttribute('data-roh');
      var w = r.el.offsetWidth, h = r.el.offsetHeight;
      r.roh = {
        x: vedle.charAt(1) === 'l' ? 0 : window.innerWidth,
        y: vedle.charAt(0) === 't' ? 0 : r.el.parentNode.offsetHeight
      };
      var hero = r.el.parentNode.getBoundingClientRect();
      r.rohViewport = { x: r.roh.x, y: hero.top + r.roh.y };
      r.stred = {
        x: r.rohViewport.x + (vedle.charAt(1) === 'l' ? w / 2 : -w / 2),
        y: r.rohViewport.y + (vedle.charAt(0) === 't' ? h / 2 : -h / 2)
      };
    });
  }

  var posX = null, posY = null, bezi = false;

  function impuls(x, y, dx, dy) {
    rohy.forEach(function (r) {
      var vzdal = Math.hypot(x - r.stred.x, y - r.stred.y);
      if (vzdal > DOSAH) return;
      var vaha = 1 - vzdal / DOSAH;
      vaha *= vaha;
      // poloha ukazatele vůči rohu, ke kterému se květina otáčí
      var px = x - r.rohViewport.x, py = y - r.rohViewport.y;
      var d = Math.max(Math.hypot(px, py), 40);
      var moment = (px * dy - py * dx) / d;      // >0 = po směru hodin
      r.rychlost += moment * SILA * vaha * 60;
      r.hnuto = true;
    });
    start();
  }

  function pohyb(e) {
    var x = e.clientX, y = e.clientY;
    if (posX !== null) impuls(x, y, x - posX, y - posY);
    posX = x; posY = y;
  }

  function klik(e) {
    // ťuknutí = lehký poryv: každý roh se kývne směrem od místa dotyku
    posX = e.clientX; posY = e.clientY;
    rohy.forEach(function (r) {
      var vzdal = Math.hypot(posX - r.stred.x, posY - r.stred.y);
      if (vzdal > DOSAH * 1.4) return;
      var vaha = 1 - vzdal / (DOSAH * 1.4);
      var px = posX - r.rohViewport.x, py = posY - r.rohViewport.y;
      r.rychlost += (px >= 0 ? 1 : -1) * (py >= 0 ? 1 : -1) * vaha * 0.7;
    });
    start();
  }

  function krok() {
    var porad = false;
    rohy.forEach(function (r) {
      r.rychlost += -TUHOST * r.uhel;
      r.rychlost *= TLUMENI;
      r.uhel += r.rychlost;
      if (r.uhel > MAX_UHEL) { r.uhel = MAX_UHEL; r.rychlost *= -0.3; }
      if (r.uhel < -MAX_UHEL) { r.uhel = -MAX_UHEL; r.rychlost *= -0.3; }
      if (Math.abs(r.uhel) < 0.002 && Math.abs(r.rychlost) < 0.002) {
        r.uhel = 0; r.rychlost = 0;
      } else {
        porad = true;
      }
      r.el.style.setProperty('--uhel', r.uhel.toFixed(3) + 'deg');
    });
    if (porad) requestAnimationFrame(krok); else bezi = false;
  }

  function start() {
    if (!bezi) { bezi = true; requestAnimationFrame(krok); }
  }

  zmerit();
  window.addEventListener('resize', zmerit);
  window.addEventListener('load', zmerit);
  window.addEventListener('scroll', zmerit, { passive: true });
  document.addEventListener('pointermove', pohyb, { passive: true });
  document.addEventListener('pointerdown', klik, { passive: true });
  document.addEventListener('pointerleave', function () { posX = posY = null; });

  // Pro zkoušení z konzole / testů: window.KVETY.zatres(x, y, dx, dy)
  window.KVETY = { zatres: impuls, rohy: rohy };
})();
