(function () {
  var CURRENT_KEY = 'exam-prep-current-semester';
  var SIDEBAR_KEY = 'exam-prep-sidebar-collapsed';
  var EXPANDED_KEY = 'exam-prep-expanded-semesters';

  function readStored(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  function writeStored(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* ignore */ }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var layout = document.getElementById('home-layout');
    var sidebarToggle = document.getElementById('sidebar-toggle');
    var picker = document.getElementById('current-semester');
    var nodes = document.querySelectorAll('.semester-node');
    var links = document.querySelectorAll('.semester-link');
    var cards = document.querySelectorAll('.subject-card');
    var heading = document.getElementById('semester-heading');
    var empty = document.getElementById('no-subjects');

    var options = Array.prototype.map.call(picker.options, function (o) { return o.value; });
    var stored = readStored(CURRENT_KEY);
    var current = options.indexOf(stored) !== -1 ? stored : picker.dataset.default;
    picker.value = current;

    // Whole sidebar: collapse to a thin rail.
    function setSidebarCollapsed(collapsed) {
      layout.classList.toggle('sidebar-collapsed', collapsed);
      sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
      var label = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
      sidebarToggle.setAttribute('aria-label', label);
      sidebarToggle.title = label;
    }

    sidebarToggle.addEventListener('click', function () {
      var collapsed = !layout.classList.contains('sidebar-collapsed');
      setSidebarCollapsed(collapsed);
      writeStored(SIDEBAR_KEY, collapsed ? '1' : '0');
    });

    setSidebarCollapsed(readStored(SIDEBAR_KEY) === '1');

    // Semester folders: expand/collapse like a file explorer.
    var expanded;
    try { expanded = JSON.parse(readStored(EXPANDED_KEY)); } catch (e) { expanded = null; }
    if (!Array.isArray(expanded)) expanded = [current];

    function setExpanded(node, open) {
      node.classList.toggle('expanded', open);
      node.querySelector('.semester-chevron').setAttribute('aria-expanded', String(open));
      var sem = node.dataset.semester;
      var i = expanded.indexOf(sem);
      if (open && i === -1) expanded.push(sem);
      if (!open && i !== -1) expanded.splice(i, 1);
      writeStored(EXPANDED_KEY, JSON.stringify(expanded));
    }

    nodes.forEach(function (node) {
      setExpanded(node, expanded.indexOf(node.dataset.semester) !== -1);
      node.querySelector('.semester-chevron').addEventListener('click', function () {
        setExpanded(node, !node.classList.contains('expanded'));
      });
    });

    document.getElementById('expand-all').addEventListener('click', function () {
      nodes.forEach(function (node) { setExpanded(node, true); });
    });
    document.getElementById('collapse-all').addEventListener('click', function () {
      nodes.forEach(function (node) { setExpanded(node, false); });
    });

    // The sidebar browses other semesters; the picker sets the persisted default.
    function show(semester) {
      var visible = 0;
      cards.forEach(function (card) {
        var match = card.dataset.semester === semester;
        card.hidden = !match;
        if (match) visible++;
      });
      links.forEach(function (link) {
        link.classList.toggle('active', link.dataset.semester === semester);
        link.classList.toggle('is-current', link.dataset.semester === current);
      });
      heading.textContent = 'Semester ' + semester;
      empty.hidden = visible > 0;
    }

    picker.addEventListener('change', function () {
      current = picker.value;
      writeStored(CURRENT_KEY, current);
      show(current);
    });

    nodes.forEach(function (node) {
      node.querySelector('.semester-link').addEventListener('click', function () {
        show(node.dataset.semester);
        setExpanded(node, true);
      });
    });

    show(current);
  });
})();
