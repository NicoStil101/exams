(function () {
  const grid = document.getElementById('log-grid');
  const monthLabel = document.getElementById('log-month-label');
  const prevBtn = document.getElementById('log-prev');
  const nextBtn = document.getElementById('log-next');
  const todayBtn = document.getElementById('log-today');
  const dayHeading = document.getElementById('log-day-heading');
  const dayEntriesEl = document.getElementById('log-day-entries');
  const dayExamsEl = document.getElementById('log-day-exams');
  const form = document.getElementById('log-add-form');
  const subjectInput = document.getElementById('log-subject');
  const topicInput = document.getElementById('log-topic');
  const notesInput = document.getElementById('log-notes');
  const subjectOptions = document.getElementById('log-subject-options');
  const assessGroup = document.getElementById('log-assess-group');
  const examForm = document.getElementById('log-exam-form');
  const examSubjectInput = document.getElementById('log-exam-subject');
  const examLabelInput = document.getElementById('log-exam-label');

  let selectedAssessment = 'yellow';

  const MONTH_LABELS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
  ];

  const today = new Date();
  let viewMonth = new Date(today.getFullYear(), today.getMonth(), 1);
  let selectedDate = fmtDate(today);
  let entriesByDate = {};
  let examsByDate = {};

  function pad2(n) { return String(n).padStart(2, '0'); }
  function fmtDate(d) { return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()); }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function hashSubject(subject) {
    let h = 0;
    for (let i = 0; i < subject.length; i++) {
      h = (h * 31 + subject.charCodeAt(i)) >>> 0;
    }
    return (h % 8) + 1;
  }

  function subjectColor(subject) {
    return 'var(--log-cat-' + hashSubject(subject) + ')';
  }

  function assessmentColor(assessment) {
    if (assessment === 'red') return 'var(--status-bad)';
    if (assessment === 'green') return 'var(--status-good)';
    return 'var(--status-warn)';
  }

  function mondayOnOrBefore(d) {
    const day = d.getDay(); // 0 = Sun ... 6 = Sat
    const diff = (day + 6) % 7; // days since Monday
    const out = new Date(d);
    out.setDate(d.getDate() - diff);
    return out;
  }

  async function loadSubjects() {
    try {
      const res = await fetch('/api/log/subjects');
      const subjects = await res.json();
      subjectOptions.innerHTML = subjects.map((s) => '<option value="' + escapeHtml(s) + '"></option>').join('');
    } catch (e) {
      /* non-fatal: autocomplete just stays empty */
    }
  }

  async function loadMonth() {
    const gridStart = mondayOnOrBefore(viewMonth);
    const gridEnd = new Date(gridStart);
    gridEnd.setDate(gridStart.getDate() + 41);
    const startStr = fmtDate(gridStart);
    const endStr = fmtDate(gridEnd);

    const [entriesRes, examsRes] = await Promise.all([
      fetch(`/api/log?start=${startStr}&end=${endStr}`),
      fetch(`/api/exams?start=${startStr}&end=${endStr}`),
    ]);
    const entries = await entriesRes.json();
    const exams = await examsRes.json();

    entriesByDate = {};
    entries.forEach((e) => {
      (entriesByDate[e.date] = entriesByDate[e.date] || []).push(e);
    });
    examsByDate = {};
    exams.forEach((ex) => {
      (examsByDate[ex.date] = examsByDate[ex.date] || []).push(ex);
    });

    renderGrid(gridStart);
    renderDayPanel();
  }

  function renderGrid(gridStart) {
    monthLabel.textContent = MONTH_LABELS[viewMonth.getMonth()] + ' ' + viewMonth.getFullYear();
    const todayStr = fmtDate(today);
    const cells = [];
    for (let i = 0; i < 42; i++) {
      const d = new Date(gridStart);
      d.setDate(gridStart.getDate() + i);
      const dateStr = fmtDate(d);
      const inMonth = d.getMonth() === viewMonth.getMonth();
      const dayEntries = entriesByDate[dateStr] || [];
      const dayExams = examsByDate[dateStr] || [];
      const chips = dayEntries
        .slice(0, 8)
        .map((e) => (
          '<span class="log-chip" style="background:' + assessmentColor(e.assessment) + '" ' +
          'title="' + escapeHtml(e.subject) + ': ' + escapeHtml(e.topic) + '"></span>'
        ))
        .join('');
      const examBadge = dayExams.length
        ? '<span class="log-exam-badge" title="Exam: ' + escapeHtml(dayExams.map((ex) => ex.subject || ex.label || 'exam').join(', ')) + '">&#127891;</span>'
        : '';
      const classes = [
        'log-day',
        inMonth ? '' : 'other-month',
        dateStr === todayStr ? 'today' : '',
        dateStr === selectedDate ? 'selected' : '',
      ].filter(Boolean).join(' ');
      cells.push(
        '<button type="button" class="' + classes + '" data-date="' + dateStr + '">' +
        examBadge +
        '<span class="log-day-num">' + d.getDate() + '</span>' +
        '<span class="log-chip-row">' + chips + '</span>' +
        '</button>'
      );
    }
    grid.innerHTML = cells.join('');
    grid.querySelectorAll('.log-day').forEach((cell) => {
      cell.addEventListener('click', () => {
        selectedDate = cell.dataset.date;
        renderGrid(gridStart);
        renderDayPanel();
      });
    });
  }

  function renderDayPanel() {
    const d = new Date(selectedDate + 'T00:00:00');
    dayHeading.textContent = d.toLocaleDateString(undefined, {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    });

    const exams = examsByDate[selectedDate] || [];
    dayExamsEl.innerHTML = exams
      .map((ex) => (
        '<div class="log-exam-entry">' +
        '<button type="button" class="log-entry-delete" data-id="' + ex.id + '" data-type="exam" aria-label="Delete exam">&times;</button>' +
        '&#127891; <strong>Exam</strong>' +
        (ex.subject ? ': ' + escapeHtml(ex.subject) : '') +
        (ex.label ? ' &mdash; ' + escapeHtml(ex.label) : '') +
        '</div>'
      ))
      .join('');
    dayExamsEl.querySelectorAll('.log-entry-delete').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await fetch('/api/exams/' + btn.dataset.id, { method: 'DELETE' });
        await loadMonth();
      });
    });

    const entries = entriesByDate[selectedDate] || [];
    if (!entries.length) {
      dayEntriesEl.innerHTML = '<p class="log-empty">Nothing logged yet.</p>';
      return;
    }
    dayEntriesEl.innerHTML = entries
      .map((e) => (
        '<div class="log-entry assess-' + e.assessment + '">' +
        '<button type="button" class="log-entry-delete" data-id="' + e.id + '" data-type="log" aria-label="Delete entry">&times;</button>' +
        '<div class="log-entry-subject">' +
        '<span class="log-chip" style="background:' + subjectColor(e.subject) + '"></span>' +
        escapeHtml(e.subject) +
        '</div>' +
        '<div class="log-entry-topic">' + escapeHtml(e.topic) + '</div>' +
        (e.notes ? '<div class="log-entry-notes">' + escapeHtml(e.notes) + '</div>' : '') +
        '</div>'
      ))
      .join('');
    dayEntriesEl.querySelectorAll('.log-entry-delete').forEach((btn) => {
      btn.addEventListener('click', async () => {
        await fetch('/api/log/' + btn.dataset.id, { method: 'DELETE' });
        await loadMonth();
      });
    });
  }

  assessGroup.querySelectorAll('.log-assess-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      selectedAssessment = btn.dataset.value;
      assessGroup.querySelectorAll('.log-assess-btn').forEach((b) => b.classList.toggle('active', b === btn));
    });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const subject = subjectInput.value.trim();
    const topic = topicInput.value.trim();
    const notes = notesInput.value.trim();
    if (!subject || !topic) return;
    await fetch('/api/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: selectedDate, subject, topic, assessment: selectedAssessment, notes }),
    });
    topicInput.value = '';
    notesInput.value = '';
    await loadSubjects();
    await loadMonth();
  });

  examForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const subject = examSubjectInput.value.trim();
    const label = examLabelInput.value.trim();
    await fetch('/api/exams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: selectedDate, subject, label }),
    });
    examSubjectInput.value = '';
    examLabelInput.value = '';
    await loadMonth();
  });

  prevBtn.addEventListener('click', () => {
    viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1);
    loadMonth();
  });
  nextBtn.addEventListener('click', () => {
    viewMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1);
    loadMonth();
  });
  todayBtn.addEventListener('click', () => {
    viewMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    selectedDate = fmtDate(today);
    loadMonth();
  });

  loadSubjects();
  loadMonth();
})();
