let eosChart = null;

const EOS_META = {
  ideal_gas: { badge: "badge-ig", color: "#06b6d4", formula: "PVm = RT" },
  vdw: { badge: "badge-vdw", color: "#f59e0b", formula: "(P + a/Vm²)(Vm − b) = RT" },
  srk: { badge: "badge-srk", color: "#22c55e", formula: "P = RT/(Vm−b) − a(T)/[Vm(Vm+b)]" },
  pr: { badge: "badge-pr", color: "#7c3aed", formula: "P = RT/(Vm−b) − a(T)/[Vm(Vm+b)+b(Vm−b)]" }
};

function chartTheme() {
  const isLight = document.documentElement.dataset.theme === "light";
  return {
    grid: isLight ? "rgba(15, 23, 42, 0.08)" : "rgba(148, 163, 184, 0.12)",
    tick: isLight ? "#64748b" : "#8da0ba",
    text: isLight ? "#0f172a" : "#f8fbff",
    zLine: isLight ? "#0f172a" : "#f8fbff",
    zIdeal: isLight ? "#0891b2" : "#06b6d4",
    tooltipBg: isLight ? "rgba(255,255,255,0.98)" : "rgba(8,17,31,0.96)",
    tooltipBorder: isLight ? "rgba(15,23,42,0.14)" : "rgba(148,163,184,0.16)"
  };
}

function updateEosChartTheme() {
  if (!eosChart) return;
  const theme = chartTheme();
  eosChart.data.datasets[1].borderColor = theme.zLine;
  eosChart.data.datasets[1].backgroundColor = theme.zLine;
  eosChart.data.datasets[2].borderColor = theme.zIdeal;
  eosChart.options.plugins.legend.labels.color = theme.text;
  eosChart.options.plugins.tooltip.backgroundColor = theme.tooltipBg;
  eosChart.options.plugins.tooltip.borderColor = theme.tooltipBorder;
  eosChart.options.plugins.tooltip.titleColor = theme.text;
  eosChart.options.plugins.tooltip.bodyColor = theme.text;
  eosChart.options.scales.x.ticks.color = theme.tick;
  eosChart.options.scales.x.grid.color = theme.grid;
  eosChart.options.scales.yVm.ticks.color = theme.tick;
  eosChart.options.scales.yVm.grid.color = theme.grid;
  eosChart.options.scales.yVm.title.color = theme.tick;
  eosChart.options.scales.yZ.ticks.color = theme.tick;
  eosChart.options.scales.yZ.title.color = theme.tick;
  eosChart.update();
}

function deviationClass(pct) {
  const a = Math.abs(pct);
  if (a < 2) return "dev-good";
  if (a < 10) return "dev-warn";
  return "dev-bad";
}

function interpretZ(z) {
  if (z > 1.01) return "répulsion";
  if (z < 0.99) return "attraction";
  return "quasi-idéal";
}

function baseScales() {
  const theme = chartTheme();
  return {
    x: {
      ticks: { color: theme.tick },
      grid: { color: theme.grid }
    }
  };
}

async function calculate() {
  const gas = document.getElementById("gas").value;
  const T = parseFloat(document.getElementById("temp").value);
  const P = parseFloat(document.getElementById("pres").value);

  document.getElementById("loading").style.display = "flex";
  document.getElementById("best-eos-card").style.display = "none";
  document.getElementById("eos-cards").style.display = "none";
  document.getElementById("results-card").style.display = "none";
  document.getElementById("chart-card").style.display = "none";

  let data;
  try {
    const resp = await fetch("/api/eos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gas, T, P })
    });
    if (!resp.ok) throw new Error("Impossible de lancer le calcul.");
    data = await resp.json();
    if (data.error) throw new Error(data.error);
  } catch (error) {
    alert("Erreur : " + error.message);
    document.getElementById("loading").style.display = "none";
    return;
  }

  document.getElementById("loading").style.display = "none";

  const order = ["ideal_gas", "vdw", "srk", "pr"].filter(key => data[key]);
  const vmIdeal = data.ideal_gas ? data.ideal_gas.Vm * 1000 : 1;
  const best = data.best_eos;

  if (best) {
    const bestMeta = EOS_META[best.key] || { color: "#f8fbff", badge: "" };
    const bestCard = document.getElementById("best-eos-card");
    bestCard.innerHTML = `
      <div class="best-eos-copy">
        <span class="tag">Best EOS</span>
        <h2>${best.label}</h2>
        <p>Pour ce fluide et ces conditions, <strong>${best.label}</strong> est la meilleure EOS recommandee.</p>
        <p class="best-eos-reason">${best.reason}</p>
      </div>
      <div class="best-eos-metrics">
        <div>
          <span>Confiance</span>
          <strong>${best.confidence}</strong>
        </div>
        <div>
          <span>Tr</span>
          <strong>${best.Tr.toFixed(3)}</strong>
        </div>
        <div>
          <span>Pr</span>
          <strong>${best.Pr.toFixed(3)}</strong>
        </div>
        <div>
          <span>Z</span>
          <strong style="color:${bestMeta.color}">${best.Z.toFixed(4)}</strong>
        </div>
      </div>`;
    bestCard.style.borderColor = `${bestMeta.color}55`;
    bestCard.style.display = "grid";
  }

  const cardsEl = document.getElementById("eos-cards");
  cardsEl.innerHTML = "";

  order.forEach(key => {
    const res = data[key];
    const meta = EOS_META[key];
    const deviation = ((res.Vm * 1000 - vmIdeal) / vmIdeal) * 100;

    cardsEl.innerHTML += `
      <div class="eos-info-card" style="border-color:${meta.color}33">
        <div class="eos-name"><span class="badge ${meta.badge}">${res.label}</span></div>
        <div class="eos-formula">${meta.formula}</div>
        <div class="eos-z" style="color:${meta.color}">${res.Z.toFixed(4)}</div>
        <div style="margin-top:10px;color:var(--text-soft);font-size:0.9rem">
          Vm = ${(res.Vm * 1000).toFixed(4)} L/mol
        </div>
        <div style="margin-top:6px;color:var(--text-muted);font-size:0.82rem">
          Écart = ${deviation > 0 ? "+" : ""}${deviation.toFixed(2)}%
        </div>
      </div>`;
  });
  cardsEl.style.display = "grid";

  const tbody = document.getElementById("results-body");
  tbody.innerHTML = "";

  order.forEach(key => {
    const res = data[key];
    const meta = EOS_META[key];
    const deviation = ((res.Vm * 1000 - vmIdeal) / vmIdeal) * 100;
    tbody.innerHTML += `
      <tr>
        <td><span class="badge ${meta.badge}">${res.label}</span></td>
        <td>${(res.Vm * 1000).toFixed(5)}</td>
        <td>${res.Z.toFixed(5)}</td>
        <td class="${deviationClass(deviation)}">${deviation > 0 ? "+" : ""}${deviation.toFixed(2)}%</td>
        <td>${interpretZ(res.Z)}</td>
      </tr>`;
  });
  document.getElementById("results-card").style.display = "block";

  const labels = order.map(key => data[key].label);
  const vmValues = order.map(key => Number((data[key].Vm * 1000).toFixed(5)));
  const zValues = order.map(key => Number(data[key].Z.toFixed(5)));
  const colors = order.map(key => EOS_META[key].color);
  const theme = chartTheme();

  if (eosChart) eosChart.destroy();
  eosChart = new Chart(document.getElementById("eosChart"), {
    data: {
      labels,
      datasets: [
        {
          type: "bar",
          label: "Vm (L/mol)",
          data: vmValues,
          borderRadius: 10,
          backgroundColor: colors.map(color => `${color}66`),
          borderColor: colors,
          borderWidth: 1.5,
          yAxisID: "yVm"
        },
        {
          type: "line",
          label: "Z",
          data: zValues,
          borderColor: theme.zLine,
          backgroundColor: theme.zLine,
          borderWidth: 3,
          pointRadius: 5,
          pointHoverRadius: 6,
          yAxisID: "yZ",
          tension: 0.35
        },
        {
          type: "line",
          label: "Z idéal",
          data: labels.map(() => 1),
          borderColor: theme.zIdeal,
          borderDash: [6, 6],
          pointRadius: 0,
          borderWidth: 2,
          yAxisID: "yZ"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: theme.text,
            usePointStyle: true,
            padding: 18
          }
        },
        tooltip: {
          backgroundColor: theme.tooltipBg,
          borderColor: theme.tooltipBorder,
          borderWidth: 1,
          titleColor: theme.text,
          bodyColor: theme.text
        }
      },
      scales: {
        ...baseScales(),
        yVm: {
          position: "left",
          ticks: { color: theme.tick },
          grid: { color: theme.grid },
          title: { display: true, text: "Vm (L/mol)", color: theme.tick }
        },
        yZ: {
          position: "right",
          ticks: { color: theme.tick },
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Z", color: theme.tick }
        }
      }
    }
  });

  document.getElementById("chart-card").style.display = "block";
}

function reset() {
  document.getElementById("temp").value = "300";
  document.getElementById("pres").value = "10";
  document.getElementById("best-eos-card").style.display = "none";
  document.getElementById("eos-cards").style.display = "none";
  document.getElementById("results-card").style.display = "none";
  document.getElementById("chart-card").style.display = "none";
  if (eosChart) {
    eosChart.destroy();
    eosChart = null;
  }
}

window.addEventListener("eos-theme-change", updateEosChartTheme);

// Exporter la fonction pour la mise à jour du thème
window.updateEosChartTheme = updateEosChartTheme;