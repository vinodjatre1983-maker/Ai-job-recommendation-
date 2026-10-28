const form = document.getElementById("recommendForm");
const submitButton = document.getElementById("submitButton");
const formMessage = document.getElementById("formMessage");
const resultsGrid = document.getElementById("resultsGrid");
const resultCount = document.getElementById("resultCount");
const resultsSubtitle = document.getElementById("resultsSubtitle");

const icons = {
  "AI & Data": "⌘",
  "Engineering": "⌁",
  "Technology": "⌘",
  "Cloud & DevOps": "☁",
  "Design": "✳",
  "Security": "◇"
};

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
}

async function loadStats() {
  try {
    const response = await fetch("/api/stats");
    if (!response.ok) return;
    const stats = await response.json();
    document.getElementById("jobsStat").textContent = stats.jobs;
    document.getElementById("categoriesStat").textContent = stats.categories;
    document.getElementById("searchesStat").textContent = stats.searches;
  } catch (error) {
    console.warn("Could not load app statistics.", error);
  }
}

function renderJobs(jobs) {
  if (!jobs.length) {
    resultsGrid.innerHTML = `<div class="empty-state"><div class="empty-graphic"><span>⌕</span><i></i><b></b></div><strong>No matches found yet.</strong><p>Try adding more skills or using related terms, such as “data analysis” or “web development”.</p></div>`;
    return;
  }

  const cards = jobs.map((job, index) => {
    const skills = (job.skills_list || []).slice(0, 5)
      .map(skill => `<span class="skill-tag">${escapeHTML(skill)}</span>`).join("");
    const icon = icons[job.category] || "✳";
    const score = Math.max(0, Math.min(100, Number(job.match) || 0));
    return `
      <article class="job-card">
        <div class="job-card-top">
          <div class="job-icon">${icon}</div>
          <div class="job-title-wrap">
            <h3>${escapeHTML(job.title)}</h3>
            <div class="job-meta"><span>${escapeHTML(job.category)}</span><span>·</span><span>⌖ ${escapeHTML(job.location)}</span></div>
          </div>
          <div class="job-match">
            <span class="match-number">${score}%</span>
            <span class="match-label">SIMILARITY</span>
            <span class="match-track"><span class="match-fill" style="display:block;width:${score}%"></span></span>
          </div>
        </div>
        <p class="job-description">${escapeHTML(job.description)}</p>
        <div class="skill-list">${skills}</div>
        <div class="job-card-bottom">
          <span class="experience">${escapeHTML(job.experience || "Not specified")}</span>
          <a class="apply-link" href="${escapeHTML(job.apply_url)}" target="_blank" rel="noopener noreferrer">Explore jobs ↗</a>
        </div>
      </article>`;
  }).join("");

  resultsGrid.innerHTML = cards + `<p class="match-disclaimer">Match scores indicate text similarity between your profile and this demo catalogue. They are not a guarantee of hiring, eligibility, or job availability. Sample listings use a general job-search link; verify each opening before applying.</p>`;
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  formMessage.classList.remove("show");
  formMessage.textContent = "";

  const payload = {
    skills: document.getElementById("skills").value.trim(),
    education: document.getElementById("education").value,
    location: document.getElementById("location").value.trim()
  };

  if (payload.skills.length < 2) {
    formMessage.textContent = "Add a few skills first so the system can find relevant roles.";
    formMessage.classList.add("show");
    return;
  }

  submitButton.disabled = true;
  submitButton.innerHTML = "Analyzing profile <span>…</span>";
  resultCount.textContent = "ANALYZING";
  resultsSubtitle.textContent = "Comparing your profile against the job catalogue…";

  try {
    const response = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");

    renderJobs(data.recommendations || []);
    resultCount.textContent = `${data.count} ROLES RANKED`;
    resultsSubtitle.textContent = "Ranked by profile similarity and your location preference.";
    await loadStats();
    document.getElementById("results").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    formMessage.textContent = error.message || "Could not reach the recommendation server. Is Flask running?";
    formMessage.classList.add("show");
    resultCount.textContent = "REQUEST FAILED";
    resultsSubtitle.textContent = "Please check the form and try again.";
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = 'Analyze my profile <span>→</span>';
  }
});

document.getElementById("mobileMenu").addEventListener("click", () => {
  document.getElementById("sidebar").classList.toggle("open");
});

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(link => link.classList.remove("active"));
    item.classList.add("active");
    if (window.innerWidth <= 820) document.getElementById("sidebar").classList.remove("open");
  });
});

loadStats();
