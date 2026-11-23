/* Odpočet do svatby. Ukazuje dny, ne vteřiny. Zkoušení jiného dne:
   ?dnes=2027-08-10 v adrese. */
(function () {
  'use strict';

  var el = document.querySelector('.odpocet[data-datum]');
  if (!el) return;

  var cil = new Date(el.getAttribute('data-datum'));
  if (isNaN(cil)) return;

  var dnes = new Date();
  var m = /[?&]dnes=(\d{4})-(\d{2})-(\d{2})/.exec(location.search);
  if (m) dnes = new Date(+m[1], +m[2] - 1, +m[3]);

  function pulnoc(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  var dni = Math.round((pulnoc(cil) - pulnoc(dnes)) / 86400000);

  var text;
  if (dni > 14) {
    text = 'Zbývá <strong>' + dni + '</strong> dní.';
  } else if (dni > 1) {
    text = 'Už jen <strong>' + dni + '</strong> ' + (dni < 5 ? 'dny' : 'dní') + '.';
  } else if (dni === 1) {
    text = 'Už jen <strong>1</strong> den.';
  } else if (dni === 0) {
    text = '<strong>Je to dnes!</strong>';
  } else {
    text = 'Díky, že jste přijeli.';
  }

  el.querySelector('[data-text]').innerHTML = text;
  el.hidden = false;
})();
