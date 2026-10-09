(function () {
  const exerciseId = document.currentScript.dataset.exerciseId;
  const newBtn = document.getElementById('new-btn');
  const solutionBtn = document.getElementById('solution-btn');
  const problemBox = document.getElementById('problem-box');
  const diagramBox = document.getElementById('diagram-box');
  const solutionBox = document.getElementById('solution-box');
  const solutionSteps = document.getElementById('solution-steps');
  const answerBox = document.getElementById('answer-box');
  const answerContent = document.getElementById('answer-content');
  const seedLabel = document.getElementById('seed-label');
  const checkBox = document.getElementById('check-answer-box');
  const checkGridsWrap = document.getElementById('check-grids-wrap');
  const checkTableWrap = document.getElementById('check-table-wrap');
  const checkRowsEl = document.getElementById('check-answer-rows');
  const checkBtn = document.getElementById('check-answer-btn');
  const checkFeedback = document.getElementById('check-answer-feedback');

  let currentCheckAnswers = [];
  let currentCheckTable = null;
  let currentCheckGrids = [];
  let currentSeed = null;

  function recordAttempt(correct) {
    fetch('/api/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exercise_id: exerciseId, correct: correct, seed: currentSeed }),
    }).catch(() => {});
  }

  function renderMath() {
    if (window.renderMathInElement) {
      renderMathInElement(document.body, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
        ],
      });
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function inlineMd(text) {
    return escapeHtml(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+?)`/g, '<code>$1</code>');
  }

  // Supports ```fenced code blocks``` (rendered verbatim, monospace) plus
  // **bold**, `inline code`, blank-line paragraphs and single-newline <br>.
  function mdToHtml(text) {
    return text
      .split(/```/)
      .map((part, i) => {
        if (i % 2 === 1) {
          return '<pre><code>' + escapeHtml(part.trim()) + '</code></pre>';
        }
        return part
          .split(/\n\n+/)
          .filter((p) => p.trim().length)
          .map((p) => '<p>' + inlineMd(p).replace(/\n/g, '<br>') + '</p>')
          .join('');
      })
      .join('');
  }

  function updateCheckBoxVisibility() {
    const hasAny =
      currentCheckAnswers.length > 0 || !!currentCheckTable || currentCheckGrids.length > 0;
    checkBox.classList.toggle('hidden', !hasAny);
  }

  // Clickable timeline grids (rows x unit time slots, e.g. scheduling Gantt
  // charts). Clicking a cell toggles it; "Check" grades each cell against
  // grid.solution.
  function renderCheckGrids(list) {
    currentCheckGrids = list || [];
    if (!currentCheckGrids.length) {
      checkGridsWrap.innerHTML = '';
      return;
    }
    checkGridsWrap.innerHTML = currentCheckGrids
      .map((grid, gi) => {
        const header =
          '<tr><th class="grid-rowlabel"></th>' +
          Array.from({ length: grid.slots }, (_, t) => '<th class="grid-time">' + t + '</th>').join('') +
          '</tr>';
        const body = grid.rows
          .map((label, ri) => {
            const cells = Array.from({ length: grid.slots }, (_, t) =>
              '<td class="grid-cell" data-grid="' + gi + '" data-row="' + ri + '" data-col="' + t + '"></td>'
            ).join('');
            const pretty = /^P\d+$/.test(label)
              ? '$' + label.replace(/^P(\d+)$/, 'P_$1') + '$'
              : escapeHtml(label);
            const rowClass = label === 'Scheduling' ? ' class="grid-sched-row"' : '';
            return '<tr' + rowClass + '><th class="grid-rowlabel">' + pretty + '</th>' + cells + '</tr>';
          })
          .join('');
        const hint = grid.hint
          ? '<p class="check-table-hint">' + inlineMd(grid.hint) + '</p>'
          : '';
        return (
          '<div class="check-grid">' +
          '<div class="check-grid-title">' + inlineMd(grid.title) + '</div>' +
          '<div class="check-table-scroll"><table class="check-grid-table"><thead>' +
          header + '</thead><tbody>' + body + '</tbody></table></div>' +
          hint +
          '</div>'
        );
      })
      .join('');
  }

  checkGridsWrap.addEventListener('click', (e) => {
    const cell = e.target.closest('.grid-cell');
    if (!cell) return;
    cell.classList.toggle('marked');
    cell.classList.remove('g-correct', 'g-wrong', 'g-missed');
  });

  function checkGrids() {
    let allCorrect = true;
    currentCheckGrids.forEach((grid, gi) => {
      grid.solution.forEach((row, ri) => {
        row.forEach((expected, t) => {
          const cell = checkGridsWrap.querySelector(
            '.grid-cell[data-grid="' + gi + '"][data-row="' + ri + '"][data-col="' + t + '"]'
          );
          const marked = cell.classList.contains('marked');
          cell.classList.remove('g-correct', 'g-wrong', 'g-missed');
          if (expected && marked) cell.classList.add('g-correct');
          else if (!expected && marked) { cell.classList.add('g-wrong'); allCorrect = false; }
          else if (expected && !marked) { cell.classList.add('g-missed'); allCorrect = false; }
        });
      });
    });
    return allCorrect;
  }

  function renderCheckAnswers(list) {
    currentCheckAnswers = list || [];
    checkRowsEl.innerHTML = currentCheckAnswers
      .map((item, i) => {
        const unit = item.unit ? ' (' + escapeHtml(item.unit) + ')' : '';
        let control;
        if (item.type === 'text' && Array.isArray(item.options) && item.options.length) {
          const opts = item.options
            .map((o) => '<option value="' + escapeHtml(o) + '">' + escapeHtml(o) + '</option>')
            .join('');
          control =
            '<select id="check-input-' + i + '" class="check-input" data-index="' + i + '">' +
            '<option value="" selected disabled>choose…</option>' +
            opts +
            '</select>';
        } else {
          const inputType = item.type === 'number' ? 'number' : 'text';
          const step = item.type === 'number' ? ' step="any"' : '';
          control =
            '<input id="check-input-' + i + '" class="check-input" data-index="' + i + '" ' +
            'type="' + inputType + '"' + step + ' placeholder="your answer" />';
        }
        return (
          '<div class="check-row">' +
          '<label for="check-input-' + i + '">' + escapeHtml(item.label) + unit + '</label>' +
          control +
          '</div>'
        );
      })
      .join('');
  }

  function renderCheckTable(table) {
    currentCheckTable = table || null;
    if (!currentCheckTable) {
      checkTableWrap.innerHTML = '';
      return;
    }
    const headerCells = currentCheckTable.col_headers.map((h) => '<th>' + inlineMd(h) + '</th>').join('');
    const bodyRows = currentCheckTable.rows
      .map((row, ri) => {
        const cells = row.cells
          .map((val, ci) => {
            if (val === null || val === undefined) {
              return '<td class="check-table-cell given">&mdash;</td>';
            }
            return (
              '<td class="check-table-cell">' +
              '<input type="number" step="any" class="check-table-input" ' +
              'data-row="' + ri + '" data-col="' + ci + '" placeholder="?" />' +
              '</td>'
            );
          })
          .join('');
        return '<tr><th class="check-table-rowlabel">' + inlineMd(row.label) + '</th>' + cells + '</tr>';
      })
      .join('');
    const unit = currentCheckTable.cell_unit ? ' (' + escapeHtml(currentCheckTable.cell_unit) + ')' : '';
    const hint = currentCheckTable.cell_hint
      ? '<p class="check-table-hint">' + inlineMd(currentCheckTable.cell_hint) + unit + '</p>'
      : '';
    checkTableWrap.innerHTML =
      '<div class="check-table-scroll"><table class="check-table"><thead><tr><th></th>' +
      headerCells +
      '</tr></thead><tbody>' +
      bodyRows +
      '</tbody></table></div>' +
      hint;
  }

  function isCorrect(item, raw) {
    const val = (raw || '').trim();
    if (item.type === 'hex') {
      if (typeof item.value === 'string') {
        return val.toLowerCase() === item.value.toLowerCase();
      }
      let v = val.toLowerCase();
      if (v.startsWith('0x')) v = v.slice(2);
      const n = parseInt(v, 16);
      return !Number.isNaN(n) && n === item.value;
    }
    if (item.type === 'text') {
      return val.toLowerCase() === String(item.value).toLowerCase();
    }
    const got = parseFloat(val);
    return !Number.isNaN(got) && Math.abs(got - item.value) < 1e-9;
  }

  function checkAllAnswers() {
    let allCorrect = true;
    let anyChecked = false;

    if (currentCheckGrids.length) {
      anyChecked = true;
      if (!checkGrids()) allCorrect = false;
    }

    currentCheckAnswers.forEach((item, i) => {
      anyChecked = true;
      const input = checkRowsEl.querySelector('.check-input[data-index="' + i + '"]');
      const correct = isCorrect(item, input.value);
      input.classList.toggle('correct', correct);
      input.classList.toggle('incorrect', !correct);
      if (!correct) allCorrect = false;
    });

    if (currentCheckTable) {
      currentCheckTable.rows.forEach((row, ri) => {
        row.cells.forEach((val, ci) => {
          if (val === null || val === undefined) return;
          anyChecked = true;
          const input = checkTableWrap.querySelector(
            '.check-table-input[data-row="' + ri + '"][data-col="' + ci + '"]'
          );
          const got = parseFloat(input.value);
          const correct = !Number.isNaN(got) && Math.abs(got - val) < 1e-9;
          input.classList.toggle('correct', correct);
          input.classList.toggle('incorrect', !correct);
          if (!correct) allCorrect = false;
        });
      });
    }

    if (!anyChecked) return;
    checkFeedback.textContent = allCorrect
      ? 'All correct!'
      : 'Some answers are incorrect — check the highlighted fields.';
    checkFeedback.classList.toggle('correct', allCorrect);
    checkFeedback.classList.toggle('incorrect', !allCorrect);
    recordAttempt(allCorrect);
  }

  function renderExercise(ex) {
    problemBox.innerHTML = mdToHtml(ex.prompt);
    diagramBox.innerHTML = ex.diagram || '';
    solutionSteps.innerHTML =
      '<ol>' +
      ex.steps
        .map((s) => {
          const diagram = s.diagram ? '<div class="step-diagram">' + s.diagram + '</div>' : '';
          return '<li>' + mdToHtml(s.text) + diagram + '</li>';
        })
        .join('') +
      '</ol>';
    if (ex.final_answer) {
      answerContent.innerHTML = mdToHtml(ex.final_answer);
      answerBox.classList.remove('hidden');
    } else {
      answerBox.classList.add('hidden');
    }

    renderCheckAnswers(ex.check_answers);
    renderCheckTable(ex.check_table);
    renderCheckGrids(ex.check_grids);
    updateCheckBoxVisibility();
    checkFeedback.textContent = '';
    checkFeedback.classList.remove('correct', 'incorrect');

    currentSeed = ex.seed;
    solutionBox.classList.add('hidden');
    solutionBtn.textContent = 'Show Solution';
    solutionBtn.disabled = false;
    seedLabel.textContent = 'seed ' + ex.seed;
    renderMath();
  }

  async function loadNew() {
    const res = await fetch(`/api/exercise/${exerciseId}/new`);
    renderExercise(await res.json());
  }

  newBtn.addEventListener('click', loadNew);
  solutionBtn.addEventListener('click', () => {
    const hidden = solutionBox.classList.toggle('hidden');
    solutionBtn.textContent = hidden ? 'Show Solution' : 'Hide Solution';
  });
  checkBtn.addEventListener('click', checkAllAnswers);
  checkBox.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') checkAllAnswers();
  });

  loadNew();
})();
