const state = {
  jobs: [],
  activeSources: new Set(),
  activeCategories: new Set(),
  search: "",
  newOnly: false,
  sort: "first_seen",
};

const els = {
  meta: document.getElementById("meta"),
  search: document.getElementById("search"),
  sourceFilters: document.getElementById("source-filters"),
  categoryFilters: document.getElementById("category-filters"),
  newOnly: document.getElementById("new-only"),
  sort: document.getElementById("sort"),
  results: document.getElementById("results"),
  rowTemplate: document.getElementById("row-template"),
};

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function daysAgo(dateStr) {
  if (!dateStr) return "";
  const then = new Date(dateStr);
  if (isNaN(then)) return "";
  const diffDays = Math.round((Date.now() - then.getTime()) / 86400000);
  if (diffDays <= 0) return "today";
  if (diffDays === 1) return "1 day ago";
  return `${diffDays} days ago`;
}

async function loadJobs() {
  try {
    const res = await fetch("../data/jobs.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.jobs = await res.json();
  } catch (err) {
    els.meta.textContent = `Could not load data/jobs.json (${err.message}). Serve this folder with a local web server, e.g. "python3 -m http.server" from the project root, then open dashboard/index.html through it.`;
    state.jobs = [];
  }
  buildChipGroup(els.categoryFilters, "category", state.jobs.map((j) => j.category || "Other"), state.activeCategories);
  buildChipGroup(els.sourceFilters, "source", state.jobs.map((j) => j.source), state.activeSources);
  render();
}

function buildChipGroup(container, field, values, activeSet) {
  const unique = [...new Set(values)].sort();
  unique.forEach((v) => activeSet.add(v));
  container.innerHTML = "";
  unique.forEach((value) => {
    const chip = document.createElement("span");
    chip.className = "filter-chip active";
    chip.textContent = value.replace(/^github:/, "").replace(/_/g, " ");
    chip.dataset[field] = value;
    chip.addEventListener("click", () => {
      if (activeSet.has(value)) {
        activeSet.delete(value);
        chip.classList.remove("active");
      } else {
        activeSet.add(value);
        chip.classList.add("active");
      }
      render();
    });
    container.appendChild(chip);
  });
}

function filteredJobs() {
  const q = state.search.trim().toLowerCase();
  const today = todayStr();

  let jobs = state.jobs.filter(
    (j) => state.activeSources.has(j.source) && state.activeCategories.has(j.category || "Other")
  );

  if (state.newOnly) {
    jobs = jobs.filter((j) => j.first_seen === today);
  }

  if (q) {
    jobs = jobs.filter((j) =>
      [j.title, j.company, j.location].some((f) => (f || "").toLowerCase().includes(q))
    );
  }

  jobs.sort((a, b) => {
    if (state.sort === "company") return (a.company || "").localeCompare(b.company || "");
    const av = a[state.sort] || "";
    const bv = b[state.sort] || "";
    return bv.localeCompare(av);
  });

  return jobs;
}

function render() {
  const jobs = filteredJobs();
  const today = todayStr();
  const newCount = state.jobs.filter((j) => j.first_seen === today).length;

  els.meta.textContent = `${state.jobs.length} active US postings tracked · ${newCount} new today · showing ${jobs.length}`;

  els.results.innerHTML = "";

  if (jobs.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = state.jobs.length === 0
      ? "No data yet. Run scripts/fetch_jobs.py (or wait for the daily GitHub Action) then reload."
      : "No postings match the current filters.";
    els.results.appendChild(empty);
    return;
  }

  const frag = document.createDocumentFragment();
  jobs.forEach((job) => {
    const node = els.rowTemplate.content.cloneNode(true);
    const card = node.querySelector(".job-card");
    if (job.first_seen === today) card.classList.add("is-new");

    const titleEl = node.querySelector(".job-title");
    titleEl.textContent = job.title;
    titleEl.href = job.url || "#";

    node.querySelector(".job-company").textContent = job.company || "";
    node.querySelector(".job-category").textContent = job.category || "Other";
    node.querySelector(".job-location").textContent = job.location || "Location n/a";
    node.querySelector(".job-source").textContent = (job.source || "").replace(/^github:/, "").replace(/_/g, " ");
    node.querySelector(".job-date").textContent = `found ${daysAgo(job.first_seen)}`;

    frag.appendChild(node);
  });
  els.results.appendChild(frag);
}

els.search.addEventListener("input", (e) => {
  state.search = e.target.value;
  render();
});
els.newOnly.addEventListener("change", (e) => {
  state.newOnly = e.target.checked;
  render();
});
els.sort.addEventListener("change", (e) => {
  state.sort = e.target.value;
  render();
});

loadJobs();
