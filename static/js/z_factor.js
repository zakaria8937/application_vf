let zChart = null;

const Z_GRID = "rgba(148, 163, 184, 0.12)";
const Z_TEXT = "#f8fbff";
const Z_TICK = "#8da0ba";

function statCard(label, value, note) {
  return `
    <div class="stat-card">
      <span class="stat-label">${label}</span>
      <div class="stat-num">${value}</div>
      <div class="stat-note">${note}</div>
    </div>`;
}

async function loadZ() {
  const gas = document.getElementById("gas").value;
  const T = parseFloat(document.getElementById("temp").value);

  document.getElementById("loading").style.display = "flex";
  document.getElementById("chart-card").style.display = "none";
  document.getElementById("z-summary").style.display = "none";

  let data;
  try {
    const resp = await fetch("/api/z-curve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gas, T })
    });
    if (!resp.ok) throw new Error("Impossible de calculer Z.");
    data = await resp.json();
    if (data.error) throw new Error(data.error);
  } catch (error) {
    alert("Erreur : " + error.message);
    document.getElementById("loading").style.display = "none";
    return;
  }

  document.getElementById("loading").style.display = "none";

  const points = data.P.map((p, i) => ({ x: p, y: data.Z[i] }));
  const minZ = Math.min(...data.Z);
  const maxZ = Math.max(...data.Z);
  const closestIndex = data.Z.reduce((bestIndex, value, index, arr) => {
    return Math.abs(value - 1) < Math.abs(arr[bestIndex] - 1) ? index : bestIndex;
  }, 0);

  const summary = document.getElementById("z-summary");
  summary.innerHTML = [
    statCard("Z min", minZ.toFixed(3), "zone la plus compressible"),
    statCard("Z max", maxZ.toFixed(3), "zone la moins compressible"),
    statCard("Plus proche de 1", `${data.P[closestIndex].toFixed(1)} bar`, "comportement quasi-idéal")
  ].join("");
  summary.style.display = "grid";

  if (zChart) zChart.destroy();
  zChart = new Chart(document.getElementById("zChart"), {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Z (Peng-Robinson)",
          data: points,
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.16)",
          showLine: true,
          pointRadius: 0,
          tension: 0.32,
          fill: true,
          borderWidth: 3
        },
        {
          label: "Z idéal",
          data: [{ x: data.P[0], y: 1 }, { x: data.P[data.P.length - 1], y: 1 }],
          borderColor: "#06b6d4",
          borderDash: [7, 7],
          showLine: true,
          pointRadius: 0,
          borderWidth: 1.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: Z_TEXT,
            usePointStyle: true,
            padding: 18
          }
        },
        tooltip: {
          backgroundColor: "rgba(8,17,31,0.96)",
          borderColor: "rgba(148,163,184,0.16)",
          borderWidth: 1,
          titleColor: Z_TEXT,
          bodyColor: Z_TEXT
        }
      },
      scales: {
        x: {
          title: { display: true, text: "Pression P (bar)", color: Z_TICK },
          ticks: { color: Z_TICK },
          grid: { color: Z_GRID }
        },
        y: {
          title: { display: true, text: "Facteur Z", color: Z_TICK },
          ticks: { color: Z_TICK },
          grid: { color: Z_GRID }
        }
      }
    }
  });

  document.getElementById("chart-card").style.display = "block";
}

// Exporter les fonctions pour la mise à jour du thème
window.updateZChartTheme = updateZChartTheme;