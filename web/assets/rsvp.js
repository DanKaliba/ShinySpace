/* ==========================================================================
   Potvrzení účasti

   Web je statický, žádný backend tu není — formulář proto
   odesílá rovnou do Google Formuláře a odpovědi padají do Sheetu.

   Bez JS to funguje taky: formulář se normálně odešle a prohlížeč skončí
   na googlovské stránce s poděkováním. Ošklivé, ale odpověď dorazí.
   S JS míří odeslání do schovaného <iframe>, takže návštěvník zůstane na
   stránce a poděkování ukážeme ve vlastním designu.

   Čemu se nedá vyhnout: prohlížeč kvůli pravidlům pro cizí domény
   neprozradí, co Google odpověděl. Událost load na iframu znamená jen
   „něco se vrátilo", ne „uloženo". Pro jistotu je pod formulářem věta, ať nám napíšou.
   ========================================================================== */

(function () {
  'use strict';

  var formular = document.getElementById('rsvp');
  if (!formular) return;

  var dekujeme = document.getElementById('rsvp-dekujeme');
  var chyba = document.getElementById('rsvp-chyba');
  var tlacitko = formular.querySelector('button[type="submit"]');

  var TEXTY = {
    nenapojeny: 'Formulář ještě není napojený — napište nám prosím.',
    nahled: 'Náhled: formulář zatím neodesílá, chybí ID Google Formuláře (viz README).',
    odesilam: 'Odesílám…',
    odeslat: 'Odeslat',
    selhalo: 'Odeslání se nepovedlo. Zkuste to prosím znovu, nebo nám napište.'
  };

  function text(klic) { return TEXTY[klic]; }

  /* ---------- Nevyplněná adresa formuláře ----------
     Dokud v action zůstane zástupný text, odesílání by tiše mizelo
     v prázdnu. To je horší než žádný formulář — chybějící potvrzení
     účasti se pozná až podle prázdných židlí. Radši ho schovat. */

  var nenapojeny = formular.getAttribute('action').indexOf('__ID_FORMULARE__') !== -1;
  var mistni = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname) || location.protocol === 'file:' ||
               /[?&]nahled/.test(location.search);

  if (nenapojeny && !mistni) {
    formular.hidden = true;
    if (chyba) {
      chyba.hidden = false;
      chyba.textContent = text('nenapojeny');
      formular.parentNode.insertBefore(chyba, formular.nextSibling);
    }
    if (window.console) {
      console.warn('rsvp.js: v index.html není doplněná adresa Google Formuláře ' +
                   'ani ID polí (entry.*). Formulář je proto schovaný.');
    }
    return;
  }

  // Lokální náhled bez napojeného formuláře: formulář je vidět, ale neodešle se.
  if (nenapojeny) {
    formular.addEventListener('submit', function (e) {
      e.preventDefault();
      chyba.hidden = false;
      chyba.textContent = text('nahled');
    });
  }

  /* ---------- Pole, která nedávají smysl při omluvě ---------- */

  var jenPriUcasti = Array.prototype.slice.call(
    formular.querySelectorAll('.jen-pri-ucasti'));
  var prepinaceUcasti = Array.prototype.slice.call(
    formular.querySelectorAll('[data-ucast]'));

  function prekreslit() {
    var prijedou = true;
    prepinaceUcasti.forEach(function (p) {
      if (p.checked) prijedou = p.getAttribute('data-ucast') === 'ano';
    });
    jenPriUcasti.forEach(function (pole) {
      pole.hidden = !prijedou;
      // Schované pole by se jinak odeslalo taky (třeba výchozí „V penzionu“
      // u omluvy) — vypnuté pole formulář neposílá.
      Array.prototype.forEach.call(pole.querySelectorAll('input, textarea, select'), function (vstup) {
        vstup.disabled = !prijedou;
      });
    });
  }

  prepinaceUcasti.forEach(function (p) {
    p.addEventListener('change', prekreslit);
  });
  prekreslit();

  /* ---------- Odeslání do schovaného rámu ---------- */

  var ram = document.createElement('iframe');
  ram.name = 'rsvp-cil';
  ram.hidden = true;
  ram.setAttribute('aria-hidden', 'true');
  ram.setAttribute('tabindex', '-1');
  formular.parentNode.appendChild(ram);

  // Teprve teď, když rám existuje: bez JS zůstane target prázdný
  // a formulář se odešle klasickou cestou.
  formular.target = 'rsvp-cil';

  var odeslano = false;
  var hlidac;

  function hotovo() {
    clearTimeout(hlidac);
    formular.hidden = true;
    if (chyba) chyba.hidden = true;
    if (dekujeme) {
      dekujeme.hidden = false;
      // Přesunout fokus, aby odečítač obrazovky poděkování oznámil.
      dekujeme.setAttribute('tabindex', '-1');
      dekujeme.focus();
    }
  }

  function selhalo() {
    odeslano = false;
    tlacitko.disabled = false;
    tlacitko.textContent = text('odeslat');
    if (chyba) {
      chyba.hidden = false;
      chyba.textContent = text('selhalo');
    }
  }

  ram.addEventListener('load', function () {
    // Rám se načte i hned po vložení do stránky, ještě před odesláním.
    if (odeslano) hotovo();
  });

  formular.addEventListener('submit', function (e) {
    if (e.defaultPrevented) return;
    odeslano = true;
    tlacitko.disabled = true;
    tlacitko.textContent = text('odesilam');
    if (chyba) chyba.hidden = true;

    // Kdyby se rám nikdy nenačetl (spadlá síť, blokovaný Google),
    // ať tlačítko nezůstane navždy šedé.
    hlidac = setTimeout(selhalo, 12000);
  });
})();
