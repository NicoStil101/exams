(function () {
  const listEl = document.getElementById('progress-list');
  const totalsEl = document.getElementById('totals-chart');

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function timeAgo(iso) {
    if (!iso) return 'never';
    const then = new Date(iso);
    const mins = Math.floor((Date.now() - then.getTime()) / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + ' min ago';
    const hours = Math.floor(mins / 60);
    if (hours < 24) return hours + ' hour' + (hours === 1 ? '' : 's') + ' ago';
    const days = Math.floor(hours / 24);
    if (days < 30) return days + ' day' + (days === 1 ? '' : 's') + ' ago';
    return then.toLocaleDateString();
  }

  function renderBar(item) {
    if (item.total === 0) {
      return '<div class="progress-bar-track empty"><span class="progress-empty-label">not attempted yet</span></div>';
    }
    const correctPct = (item.correct / item.total) * 100;
    const wrongPct = 100 - correctPct;
    let segments = '';
    if (item.correct > 0) {
      segments +=
        '<div class="progress-seg correct" style="width:' +
        correctPct +
        '%" title="Correct: ' +
        item.correct +
        '"></div>';
    }
    if (item.wrong > 0) {
      segments +=
        '<div class="progress-seg wrong" style="width:' +
        wrongPct +
        '%" title="Wrong: ' +
        item.wrong +
        '"></div>';
    }
    return '<div class="progress-bar-track">' + segments + '</div>';
  }

  function renderByCategory(items) {
    const byCategory = {};
    const order = [];
    items.forEach((item) => {
      if (!byCategory[item.category]) {
        byCategory[item.category] = [];
        order.push(item.category);
      }
      byCategory[item.category].push(item);
    });

    listEl.innerHTML = order
      .map((cat) => {
        const rows = byCategory[cat]
          .map((item) => {
            const accuracy = item.total ? Math.round((item.correct / item.total) * 100) + '%' : '—';
            return (
              '<div class="progress-row">' +
              '<div class="progress-title">' +
              escapeHtml(item.title) +
              '</div>' +
              renderBar(item) +
              '<div class="progress-meta">' +
              '<span class="progress-total">' +
              item.total +
              ' total</span>' +
              '<span class="progress-accuracy">' +
              accuracy +
              '</span>' +
              '<span class="progress-last">' +
              timeAgo(item.last_attempt) +
              '</span>' +
              '</div>' +
              '</div>'
            );
          })
          .join('');
        return '<div class="progress-category"><h3>' + escapeHtml(cat) + '</h3>' + rows + '</div>';
      })
      .join('');
  }

  function renderTotalsBar(item) {
    if (item.total === 0) {
      return '<div class="totals-bar-track"><div class="progress-empty-label" style="padding-left:8px;">not attempted yet</div></div>';
    }
    const correctPct = (item.correct / item.total) * 100;
    const wrongPct = 100 - correctPct;
    let segments = '';
    if (item.correct > 0) {
      segments +=
        '<div class="totals-seg correct" style="width:' +
        correctPct +
        '%" title="Correct: ' +
        item.correct +
        '"><span class="totals-seg-label" data-min-width="' +
        item.correct +
        '">' +
        item.correct +
        '</span></div>';
    }
    if (item.wrong > 0) {
      segments +=
        '<div class="totals-seg wrong" style="width:' +
        wrongPct +
        '%" title="Wrong: ' +
        item.wrong +
        '"><span class="totals-seg-label">' +
        item.wrong +
        '</span></div>';
    }
    return '<div class="totals-bar-track">' + segments + '</div>';
  }

  function renderTotalsChart(items) {
    const sorted = items.slice().sort((a, b) => {
      if (b.total !== a.total) return b.total - a.total;
      return a.title.localeCompare(b.title);
    });

    totalsEl.innerHTML = sorted
      .map((item) => {
        return (
          '<div class="totals-row">' +
          '<div class="progress-title">' +
          escapeHtml(item.title) +
          '</div>' +
          renderTotalsBar(item) +
          '<div class="totals-tip">' +
          item.total +
          '</div>' +
          '</div>'
        );
      })
      .join('');

    // Measure-then-hide: a label that doesn't comfortably fit its segment
    // is dropped (the tooltip + legend still carry the value), never clipped.
    totalsEl.querySelectorAll('.totals-seg-label').forEach((label) => {
      const seg = label.parentElement;
      if (label.scrollWidth > seg.clientWidth - 6) {
        label.style.display = 'none';
      }
    });
  }

  fetch('/api/progress')
    .then((res) => res.json())
    .then((items) => {
      renderTotalsChart(items);
      renderByCategory(items);
    })
    .catch(() => {
      totalsEl.textContent = 'Could not load progress.';
      listEl.textContent = 'Could not load progress.';
    });
})();
