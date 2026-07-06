const STORAGE_KEY = 'benessere-diario';

const FOODS = [
  'pasta', 'riso', 'pane integrale',
  'pomodori', 'melanzane', 'zucchine', 'insalata', 'carota', 'peperoni',
  'stracchino', 'formaggio fresco',
  'pollo', 'tacchino', 'manzo',
  'patate', 'uova', 'yogurt magro',
  'mela', 'banana', 'pera', 'anguria', 'melone'
];

const MEALS = [
  { id: 'colazione', label: 'Colazione' },
  { id: 'spuntino1', label: 'Spuntino mattina' },
  { id: 'pranzo', label: 'Pranzo' },
  { id: 'spuntino2', label: 'Spuntino pomeriggio' },
  { id: 'cena', label: 'Cena' }
];

const ACTIVITIES = [
  { id: 'camminata', label: 'Camminata' },
  { id: 'camminata_veloce', label: 'Camminata veloce' },
  { id: 'corsa_blanda', label: 'Corsa blanda' },
  { id: 'leo_moves', label: 'Esercizi Leo Moves' }
];

const ACTIVITY_LABELS = Object.fromEntries(ACTIVITIES.map(a => [a.id, a.label]));

let currentDate = todayISO();
let saveTimeout = null;

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function loadAll() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

function saveAll(data) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function getDayData(date) {
  const all = loadAll();
  if (!all[date]) {
    all[date] = {
      meals: Object.fromEntries(MEALS.map(m => [m.id, []])),
      activities: []
    };
  }
  return all[date];
}

function formatDateIT(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  const days = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato'];
  const months = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
    'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];
  const dt = new Date(y, m - 1, d);
  return `${days[dt.getDay()]} ${d} ${months[m - 1]} ${y}`;
}

function formatDateShortIT(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  const months = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'];
  return `${d} ${months[m - 1]} ${y}`;
}

function shiftDate(iso, days) {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  dt.setDate(dt.getDate() + days);
  return dt.toISOString().slice(0, 10);
}

function weekRange(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(y, m - 1, d);
  const day = dt.getDay();
  const diffToMonday = day === 0 ? -6 : 1 - day;
  const monday = new Date(y, m - 1, d + diffToMonday);
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const fmt = (date) => date.toISOString().slice(0, 10);
  return { start: fmt(monday), end: fmt(sunday) };
}

function showSaveStatus() {
  const el = document.getElementById('save-status');
  el.textContent = 'Salvato ✓';
  el.classList.add('visible');
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => el.classList.remove('visible'), 2000);
}

function collectFormData() {
  const meals = {};
  MEALS.forEach(meal => {
    meals[meal.id] = [...document.querySelectorAll(`input[data-meal="${meal.id}"]:checked`)]
      .map(cb => cb.value);
  });

  const activities = [];
  document.querySelectorAll('.activity-row').forEach(row => {
    const type = row.querySelector('.activity-type').value;
    const duration = parseInt(row.querySelector('.activity-duration').value, 10);
    if (type && duration > 0) {
      activities.push({ type, duration });
    }
  });

  return { meals, activities };
}

function saveCurrentDay() {
  const all = loadAll();
  all[currentDate] = collectFormData();
  saveAll(all);
  showSaveStatus();
  updateStats();
  updateNoActivitiesHint();
}

function renderMeals(selectedMeals) {
  const container = document.getElementById('meals-container');
  container.innerHTML = '';

  MEALS.forEach(meal => {
    const block = document.createElement('div');
    block.className = 'meal-block';

    const title = document.createElement('h3');
    title.textContent = meal.label;
    block.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'food-grid';

    const selected = selectedMeals[meal.id] || [];

    FOODS.forEach(food => {
      const label = document.createElement('label');
      label.className = 'food-item';

      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.value = food;
      cb.dataset.meal = meal.id;
      cb.checked = selected.includes(food);
      cb.addEventListener('change', () => saveCurrentDay());

      const span = document.createElement('span');
      span.textContent = food;

      label.appendChild(cb);
      label.appendChild(span);
      grid.appendChild(label);
    });

    block.appendChild(grid);
    container.appendChild(block);
  });
}

function createActivityRow(activity = { type: 'camminata', duration: 30 }) {
  const row = document.createElement('div');
  row.className = 'activity-row';

  const select = document.createElement('select');
  select.className = 'activity-type';
  ACTIVITIES.forEach(a => {
    const opt = document.createElement('option');
    opt.value = a.id;
    opt.textContent = a.label;
    if (a.id === activity.type) opt.selected = true;
    select.appendChild(opt);
  });
  select.addEventListener('change', () => saveCurrentDay());

  const duration = document.createElement('input');
  duration.type = 'number';
  duration.className = 'activity-duration';
  duration.min = 1;
  duration.max = 300;
  duration.value = activity.duration || 30;
  duration.addEventListener('change', () => saveCurrentDay());
  duration.addEventListener('input', () => saveCurrentDay());

  const durLabel = document.createElement('span');
  durLabel.className = 'duration-label';
  durLabel.textContent = 'min';

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn-remove';
  removeBtn.textContent = '×';
  removeBtn.title = 'Rimuovi';
  removeBtn.addEventListener('click', () => {
    row.remove();
    saveCurrentDay();
    updateNoActivitiesHint();
  });

  row.appendChild(select);
  row.appendChild(duration);
  row.appendChild(durLabel);
  row.appendChild(removeBtn);

  return row;
}

function renderActivities(activities) {
  const container = document.getElementById('activities-container');
  container.innerHTML = '';

  if (activities.length === 0) {
    updateNoActivitiesHint();
    return;
  }

  activities.forEach(a => container.appendChild(createActivityRow(a)));
  updateNoActivitiesHint();
}

function updateNoActivitiesHint() {
  const hint = document.getElementById('no-activities');
  const rows = document.querySelectorAll('.activity-row');
  hint.classList.toggle('hidden', rows.length > 0);
}

function loadDay(date) {
  currentDate = date;
  document.getElementById('date-picker').value = date;
  document.getElementById('date-label').textContent = formatDateIT(date);

  const data = getDayData(date);
  renderMeals(data.meals);
  renderActivities(data.activities);
  updateStats();
}

function generateMarkdown(dates) {
  const all = loadAll();
  const sorted = dates.filter(d => all[d]).sort();

  if (sorted.length === 0) {
    return '# Diario alimentazione e attività\n\n_Nessun dato registrato._\n';
  }

  let md = '# Diario alimentazione e attività\n\n';
  md += `_Esportato il ${formatDateIT(todayISO())}_\n\n---\n\n`;

  sorted.forEach(date => {
    const day = all[date];
    md += `## ${formatDateIT(date)}\n\n`;

    MEALS.forEach(meal => {
      const items = day.meals[meal.id] || [];
      md += `### ${meal.label}\n`;
      if (items.length > 0) {
        md += items.map(f => `- ${f}`).join('\n') + '\n';
      } else {
        md += '_non registrato_\n';
      }
      md += '\n';
    });

    md += '### Attività fisica\n';
    if (day.activities && day.activities.length > 0) {
      day.activities.forEach(a => {
        md += `- **${ACTIVITY_LABELS[a.type] || a.type}**: ${a.duration} min\n`;
      });
      const totalMin = day.activities.reduce((s, a) => s + a.duration, 0);
      md += `\n_Totale: ${totalMin} min_\n`;
    } else {
      md += '_nessuna attività_\n';
    }

    md += '\n---\n\n';
  });

  return md;
}

function downloadMarkdown(content, filename) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function updateStats() {
  const all = loadAll();
  const dates = Object.keys(all).sort();
  const el = document.getElementById('stats');

  if (dates.length === 0) {
    el.textContent = 'Nessun giorno registrato.';
    return;
  }

  const first = formatDateShortIT(dates[0]);
  const last = formatDateShortIT(dates[dates.length - 1]);
  el.textContent = `${dates.length} giorn${dates.length === 1 ? 'o' : 'i'} registrati (${first} → ${last})`;
}

function init() {
  document.getElementById('btn-prev').addEventListener('click', () => {
    saveCurrentDay();
    loadDay(shiftDate(currentDate, -1));
  });

  document.getElementById('btn-next').addEventListener('click', () => {
    saveCurrentDay();
    loadDay(shiftDate(currentDate, 1));
  });

  document.getElementById('btn-today').addEventListener('click', () => {
    saveCurrentDay();
    loadDay(todayISO());
  });

  document.getElementById('date-label').addEventListener('click', () => {
    const picker = document.getElementById('date-picker');
    picker.showPicker?.() || picker.click();
  });

  document.getElementById('date-picker').addEventListener('change', (e) => {
    saveCurrentDay();
    loadDay(e.target.value);
  });

  document.getElementById('btn-save').addEventListener('click', saveCurrentDay);

  document.getElementById('btn-add-activity').addEventListener('click', () => {
    document.getElementById('activities-container').appendChild(createActivityRow());
    updateNoActivitiesHint();
    saveCurrentDay();
  });

  document.getElementById('btn-export-all').addEventListener('click', () => {
    saveCurrentDay();
    const all = loadAll();
    const md = generateMarkdown(Object.keys(all));
    downloadMarkdown(md, `diario-benessere-${todayISO()}.md`);
  });

  document.getElementById('btn-export-week').addEventListener('click', () => {
    saveCurrentDay();
    const { start, end } = weekRange(currentDate);
    const all = loadAll();
    const weekDates = Object.keys(all).filter(d => d >= start && d <= end);
    const md = generateMarkdown(weekDates);
    downloadMarkdown(md, `diario-benessere-settimana-${start}.md`);
  });

  loadDay(currentDate);
}

init();
