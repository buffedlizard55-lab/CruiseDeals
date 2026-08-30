/* CruiseDeals table controller — vanilla JS, data from data/cruises.json */
(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };
  var DATA_URL = 'data/cruises.json';

  function fmtDate(d) {
    if (!d || !/^\d{4}-\d{2}-\d{2}$/.test(d)) return '—';
    return new Date(d + 'T12:00:00').toLocaleDateString('en-US',
      { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
  }
  function shortDate(d) {
    if (!d || !/^\d{4}-\d{2}-\d{2}$/.test(d)) return '—';
    return new Date(d + 'T12:00:00').toLocaleDateString('en-US',
      { month: 'short', day: 'numeric' });
  }
  function moneyNum(s) {
    var n = parseFloat(String(s).replace(/[^0-9.]/g, ''));
    return isNaN(n) ? Infinity : n;
  }
  function nights(dur) {
    var m = /(\d+)/.exec(dur || '');
    return m ? parseInt(m[1], 10) : 0;
  }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function stateOf(r) {
    if (r.status.indexOf('OUT OF WINDOW') === 0) return 'out';
    if (r.status.indexOf('REVIEW') === 0) return 'review';
    if (r.status.indexOf('SCHEDULE INDEX') === 0) return 'review';
    if (r.status.indexOf('NEW ') === 0) return 'new';
    return 'ok';
  }

  function rowHtml(r) {
    var st = stateOf(r);
    var cls = st === 'out' ? 'out' : (st === 'review' ? 'review' : '');
    var tag =
      st === 'out' ? '<span class="tag tag-out">OUT OF WINDOW</span>' :
      st === 'review' ? '<span class="tag tag-review">REVIEW</span>' :
      st === 'new' ? '<span class="tag tag-new">NEW · VERIFIED</span>' :
      '<span class="tag tag-ok">SCHEDULE + SNAPSHOT</span>';

    var cur = r.price_currency === 'GBP' ? '£' : '$';
    var priceTxt = r.price === 'Not published' ? r.price
      : cur + String(r.price).replace(/^[£$]/, '');

    var flightCell = r.flight_out_date
      ? '<div class="t-price">' + esc(r.flight_cost_2) + '</div>' +
        '<span class="t-note">' + esc(r.flight_route) + '<br>' +
        'Fly out ' + shortDate(r.flight_out_date) + ' · back ' + shortDate(r.flight_return_date) + '</span>' +
        '<div class="t-links">' +
        '<a href="' + esc(r.flight_search_url) + '" target="_blank" rel="noopener">Google Flights (exact dates) ↗</a>' +
        '<a href="' + esc(r.flight_source_url) + '" target="_blank" rel="noopener">Route average source ↗</a></div>'
      : '<span class="t-note">' + esc(r.flight_cost_2) + '<br>' + esc(r.flight_source) + '</span>';

    var warnTitle = esc(r.verification_note || '');

    return '<tr class="' + cls + '" title="' + warnTitle + '">' +
      '<td class="t-id">' + esc(r.id) + '</td>' +
      '<td><div class="t-name">' + esc(r.name) + '</div><span class="t-sub">' + esc(r.line) + '</span></td>' +
      '<td><div class="t-date">' + fmtDate(r.date) + '</div><span class="t-sub">' + esc(r.port) + '</span></td>' +
      '<td>' + esc(r.duration) + '</td>' +
      '<td class="t-stops">' + esc(r.stops) + '</td>' +
      '<td><div class="t-price">' + esc(priceTxt) + '</div><span class="t-note">' + esc(r.price_note) + (r.price_currency === 'GBP' ? ' · GBP — not USD' : '') + '</span></td>' +
      '<td>' + flightCell + '</td>' +
      '<td><div class="t-total">' + esc(r.trip_total_2) + '</div><span class="t-note">' + esc(r.trip_total_note) + '</span></td>' +
      '<td class="t-promo">' + esc(r.promo) + '</td>' +
      '<td><div class="t-links">' +
        '<a href="' + esc(r.official) + '" target="_blank" rel="noopener">Official line page ↗</a>' +
        '<a href="' + esc(r.source_url) + '" target="_blank" rel="noopener">Schedule-index source ↗</a></div></td>' +
      '<td>' + tag + '</td>' +
    '</tr>';
  }

  function loadJson(url) {
    return fetch(url).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + url);
      return res.json();
    });
  }

  Promise.all([loadJson(DATA_URL), loadJson('data/scope_audit.json')])
    .then(function (result) { init(result[0], result[1]); })
    .catch(function (e) {
      $('count-hint').textContent = 'Data failed to load (' + e.message + '). Use the CSV download links above.';
    });

  function init(data, audit) {
    $('audit-rows').innerHTML = audit.map(function (r) {
      var statusClass = r.status === 'RESULTS INCLUDED' ? 'audit-pass' :
        (r.status === 'OUT OF SCOPE' ? 'audit-out' : 'audit-neutral');
      return '<tr><td><b>' + esc(r.cruise_line) + '</b></td>' +
        '<td>' + esc(r.west_coast_result) + '</td>' +
        '<td><span class="audit-status ' + statusClass + '">' + esc(r.status) + '</span></td>' +
        '<td class="audit-note">' + esc(r.notes) + '</td>' +
        '<td><a href="' + esc(r.official_review_link) + '" target="_blank" rel="noopener">Official search ↗</a></td></tr>';
    }).join('');
    // summary stats
    var inWin = data.filter(function (r) { return stateOf(r) !== 'out'; });
    var newRows = data.filter(function (r) { return stateOf(r) === 'new'; });
    var flagged = data.filter(function (r) { return stateOf(r) === 'review'; });
    var priced = inWin.filter(function (r) { return moneyNum(r.trip_total_2) !== Infinity; });
    var cheapest = priced.sort(function (a, b) { return moneyNum(a.trip_total_2) - moneyNum(b.trip_total_2); })[0];
    $('stat-sailings').textContent = inWin.length;
    $('stat-new').textContent = newRows.length;
    $('stat-cheapest').textContent = cheapest ? cheapest.trip_total_2 : '—';
    $('stat-flagged').textContent = flagged.length;

    // flag panel
    $('flags-list').innerHTML = flagged.map(function (r) {
      return '<li><code>' + esc(r.id) + '</code> — <b>' + esc(r.status) + '</b><br>' + esc(r.verification_note) + '</li>';
    }).join('') || '<li>No flags.</li>';

    // filter options
    ['line', 'port'].forEach(function (key) {
      var el = $('f-' + key);
      var vals = data.map(function (r) { return r[key]; })
        .filter(function (v, i, a) { return v && a.indexOf(v) === i; }).sort();
      vals.forEach(function (v) {
        var o = document.createElement('option'); o.value = v; o.textContent = v; el.appendChild(o);
      });
    });

    ['q', 'f-line', 'f-port', 'f-dur', 'f-state', 'f-sort'].forEach(function (id) {
      $(id).addEventListener('input', render);
    });

    function applyFilters(r, q, line, port, dur, state) {
      var st = stateOf(r);
      if (state === 'in' && st === 'out') return false;
      if (state === 'new' && st !== 'new') return false;
      if (state === 'review' && st !== 'review') return false;
      if (state === 'priced' && (st === 'out' || moneyNum(r.price) === Infinity)) return false;
      if (line && r.line !== line) return false;
      if (port && r.port !== port) return false;
      if (dur) {
        var n = nights(r.duration);
        if (dur === 'short' && !(n >= 2 && n <= 4)) return false;
        if (dur === 'mid' && !(n >= 5 && n <= 7)) return false;
        if (dur === 'long' && !(n >= 8 && n <= 13)) return false;
        if (dur === 'epic' && !(n >= 14)) return false;
      }
      if (q) {
        var hay = (r.id + ' ' + r.name + ' ' + r.line + ' ' + r.port + ' ' + r.stops +
          ' ' + r.duration + ' ' + r.price + ' ' + r.promo).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    }

    function applySort(list, mode) {
      var c = list.slice();
      if (mode === 'cruise-asc') c.sort(function (a, b) { return moneyNum(a.price) - moneyNum(b.price); });
      else if (mode === 'trip-asc') c.sort(function (a, b) { return moneyNum(a.trip_total_2) - moneyNum(b.trip_total_2); });
      else if (mode === 'dur-asc') c.sort(function (a, b) { return nights(a.duration) - nights(b.duration) || (a.date < b.date ? -1 : 1); });
      else c.sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : (a.id < b.id ? -1 : 1); });
      return c;
    }

    function render() {
      var q = $('q').value.trim().toLowerCase();
      var list = applySort(data.filter(function (r) {
        return applyFilters(r, q, $('f-line').value, $('f-port').value, $('f-dur').value, $('f-state').value);
      }), $('f-sort').value);
      $('rows').innerHTML = list.map(rowHtml).join('');
      $('empty').hidden = list.length > 0;
      $('count-hint').textContent = list.length + ' of ' + data.length + ' rows';
    }
    render();
  }
})();
