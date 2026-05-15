// Sameer's Buy Buddy — frontend logic
const $ = (id) => document.getElementById(id);
let chart = null;

async function runSearch() {
  const query = $("query").value.trim();
  if (!query) return;

  const status = $("status");
  status.hidden = false;
  status.textContent = "Scraping stores… this can take ~20s ⏳";

  // Hide previous results while loading
  $("results").hidden = true;
  $("historySection").hidden = true;
  $("recoSection").hidden = true;

  try {
    const res = await fetch("/api/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Request failed");

    renderCards(data.results);
    renderChart(data.history);
    renderReco(data.recommendation);

    status.hidden = true;
  } catch (err) {
    status.textContent = "Error: " + err.message;
  }
}

function renderCards(results) {
  const container = $("cards");
  container.innerHTML = "";
  results.forEach((r) => {
    const card = document.createElement("div");
    card.className = "card";
    const priceHtml = r.price
      ? `<div class="price">₹${r.price.toLocaleString("en-IN")}</div>`
      : `<div class="price na">Unavailable</div>`;
    const linkHtml = r.link
      ? `<a href="${r.link}" target="_blank" rel="noopener">View →</a>`
      : "";
    card.innerHTML = `
      <div class="src">${r.source || "Store"}</div>
      <div class="title">${r.title || "—"}</div>
      ${priceHtml}
      ${linkHtml}
    `;
    container.appendChild(card);
  });
  $("results").hidden = false;
}

function renderChart(history) {
  if (!history || history.length === 0) {
    $("historySection").hidden = true;
    return;
  }
  $("historySection").hidden = false;
  const labels = history.map((h) => h.day);
  const data = history.map((h) => h.price);

  if (chart) chart.destroy();
  const ctx = $("historyChart").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Lowest price (₹)",
        data,
        borderColor: "#ffd23f",
        backgroundColor: "rgba(255, 210, 63, 0.2)",
        borderWidth: 3,
        tension: 0.3,
        pointRadius: 4,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#f4f4ff" } } },
      scales: {
        x: { ticks: { color: "#9aa0c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#9aa0c7" }, grid: { color: "rgba(255,255,255,0.05)" } },
      },
    },
  });
}

function renderReco(text) {
  if (!text) return;
  $("recoText").textContent = text;
  $("recoSection").hidden = false;
}

document.addEventListener("DOMContentLoaded", () => {
  $("searchBtn").addEventListener("click", runSearch);
  $("query").addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSearch();
  });
});
