// static/js/isotherms.js - Version avec support du thème

let isoCharts = [];

const EOS_ORDER = ["Gaz Parfait", "Van der Waals", "SRK", "Peng-Robinson"];
const TEMP_COLORS = ["#1d4ed8", "#dc2626", "#16a34a", "#f97316"];

// Fonction pour obtenir les couleurs du thème actuel
function getIsothermTheme() {
    const isLight = document.documentElement.dataset.theme === "light";
    return {
        textColor: isLight ? "#1f2937" : "#f8fbff",
        gridColor: isLight ? "rgba(0, 0, 0, 0.1)" : "rgba(148, 163, 184, 0.2)",
        axisColor: isLight ? "#374151" : "#94a3b8",
        titleColor: isLight ? "#111827" : "#f1f5f9",
        tooltipBg: isLight ? "rgba(255,255,255,0.98)" : "rgba(8,17,31,0.96)",
        tooltipBorder: isLight ? "rgba(0,0,0,0.1)" : "rgba(148,163,184,0.2)",
        tooltipText: isLight ? "#111827" : "#f8fbff",
        backgroundColor: isLight ? "#ffffff" : "#0d1728",
        borderColor: isLight ? "#e5e7eb" : "#1f2937"
    };
}

// Fonction pour mettre à jour tous les graphiques isothermes
function updateAllIsothermCharts() {
    const theme = getIsothermTheme();
    
    isoCharts.forEach(chart => {
        if (!chart) return;
        
        // Mettre à jour les couleurs des axes
        if (chart.options.scales?.x) {
            chart.options.scales.x.title.color = theme.titleColor;
            chart.options.scales.x.ticks.color = theme.axisColor;
            chart.options.scales.x.grid.color = theme.gridColor;
            if (chart.options.scales.x.title) {
                chart.options.scales.x.title.color = theme.titleColor;
            }
        }
        
        if (chart.options.scales?.y) {
            chart.options.scales.y.title.color = theme.titleColor;
            chart.options.scales.y.ticks.color = theme.axisColor;
            chart.options.scales.y.grid.color = theme.gridColor;
            if (chart.options.scales.y.title) {
                chart.options.scales.y.title.color = theme.titleColor;
            }
        }
        
        // Mettre à jour la légende
        if (chart.options.plugins?.legend) {
            chart.options.plugins.legend.labels.color = theme.textColor;
        }
        
        // Mettre à jour le tooltip
        if (chart.options.plugins?.tooltip) {
            chart.options.plugins.tooltip.backgroundColor = theme.tooltipBg;
            chart.options.plugins.tooltip.borderColor = theme.tooltipBorder;
            chart.options.plugins.tooltip.titleColor = theme.tooltipText;
            chart.options.plugins.tooltip.bodyColor = theme.tooltipText;
        }
        
        chart.update();
    });
}

// Supprimer tous les graphiques
function destroyIsoCharts() {
    isoCharts.forEach(chart => {
        if (chart) chart.destroy();
    });
    isoCharts = [];
}

// Extraire la température du label
function parseTemperature(label) {
    const match = label.match(/T=(\d+(?:\.\d+)?)K/);
    return match ? Number(match[1]) : null;
}

// Formater la formule chimique
function formatGasFormula(formula) {
    return (formula || "").replace(/(\d+)/g, "<sub>$1</sub>");
}

// Relation température critique
function tempRelation(T, Tc) {
    if (!Number.isFinite(Tc)) return "";
    if (Math.abs(T - Tc) <= 2) return "(Tc)";
    if (T < Tc) return "(< Tc)";
    return T >= Tc * 1.35 ? "(>> Tc)" : "(> Tc)";
}

// Titre du graphique
function chartTitle(eosName, gasInfo) {
    const formula = formatGasFormula(gasInfo?.formula || "");
    const suffix = formula ? ` pour ${formula}` : "";
    return `Isothermes de ${eosName}${suffix}`;
}

// Charger les isothermes
async function loadIsotherms() {
    const gas = document.getElementById("gas").value;
    const T1 = parseFloat(document.getElementById("t1").value);
    const T2 = parseFloat(document.getElementById("t2").value);
    const T3 = parseFloat(document.getElementById("t3").value);
    const T4 = parseFloat(document.getElementById("t4").value);
    const vmMin = parseFloat(document.getElementById("vmMin").value);
    const vmMax = parseFloat(document.getElementById("vmMax").value);
    const pMax = parseFloat(document.getElementById("pMax").value);

    document.getElementById("loading").style.display = "flex";
    document.getElementById("iso-grid").style.display = "none";

    let data;
    try {
        const resp = await fetch("/api/isotherms", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ gas, temperatures: [T1, T2, T3, T4], vmMin, vmMax })
        });
        if (!resp.ok) throw new Error("Impossible de generer les courbes.");
        data = await resp.json();
        if (data.error) throw new Error(data.error);
    } catch (error) {
        alert("Erreur : " + error.message);
        document.getElementById("loading").style.display = "none";
        return;
    }

    document.getElementById("loading").style.display = "none";
    destroyIsoCharts();

    const grid = document.getElementById("iso-grid");
    grid.innerHTML = "";

    const temperatures = [...new Set(data.datasets.map(ds => parseTemperature(ds.label)).filter(Boolean))];
    const xMin = Number.isFinite(vmMin) ? vmMin : data.Vm_range?.[0] || 0.2;
    const xMax = Number.isFinite(vmMax) ? vmMax : data.Vm_range?.[1] || 3;
    const yMax = Number.isFinite(pMax) ? pMax : 100;
    const Tc = Number(data.gas?.Tc);
    
    const theme = getIsothermTheme();

    EOS_ORDER.forEach(eosName => {
        const datasets = data.datasets
            .filter(ds => ds.label.startsWith(eosName))
            .map(ds => {
                const temp = parseTemperature(ds.label);
                const colorIndex = temperatures.indexOf(temp) % TEMP_COLORS.length;
                const color = TEMP_COLORS[colorIndex];
                return {
                    ...ds,
                    label: `T = ${temp} K ${tempRelation(temp, Tc)}`,
                    borderColor: color,
                    backgroundColor: color,
                    borderWidth: 2.5,
                    showLine: true,
                    fill: false,
                    tension: 0.15,
                    pointRadius: 0,
                    pointHoverRadius: 4
                };
            });

        if (!datasets.length) return;

        const card = document.createElement("div");
        card.className = "card chart-panel iso-report-card";
        card.style.background = theme.backgroundColor;
        card.style.borderColor = theme.borderColor;
        card.innerHTML = `
            <div class="card-head">
                <h2 style="color: ${theme.textColor};">${eosName}</h2>
                <span class="tag">${datasets.length} courbes</span>
            </div>
            <div class="iso-title" style="color: ${theme.titleColor};">${chartTitle(eosName, data.gas)}</div>
            <div class="chart-container small iso-chart-container"><canvas></canvas></div>`;

        grid.appendChild(card);
        const ctx = card.querySelector("canvas");

        const chart = new Chart(ctx, {
            type: "scatter",
            data: { datasets },
            options: {
                showLine: true,
                responsive: true,
                maintainAspectRatio: false,
                layout: { 
                    padding: { top: 8, right: 12, bottom: 4, left: 4 } 
                },
                plugins: {
                    legend: {
                        position: "top",
                        align: "end",
                        labels: {
                            color: theme.textColor,
                            boxWidth: 42,
                            boxHeight: 2,
                            usePointStyle: false,
                            padding: 14,
                            font: { size: 13, weight: "bold" }
                        }
                    },
                    tooltip: {
                        backgroundColor: theme.tooltipBg,
                        borderColor: theme.tooltipBorder,
                        borderWidth: 1,
                        titleColor: theme.tooltipText,
                        bodyColor: theme.tooltipText,
                        callbacks: {
                            label(context) {
                                return `${context.dataset.label}: P=${context.parsed.y.toFixed(2)} bar, Vm=${context.parsed.x.toFixed(2)} L/mol`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: "linear",
                        min: xMin,
                        max: xMax,
                        title: {
                            display: true,
                            text: "Volume molaire Vm (L/mol)",
                            color: theme.titleColor,
                            font: { size: 16, weight: "bold" }
                        },
                        ticks: {
                            color: theme.axisColor,
                            stepSize: 0.2,
                            font: { size: 12 }
                        },
                        grid: { color: theme.gridColor },
                        border: { color: theme.axisColor }
                    },
                    y: {
                        min: 0,
                        max: yMax,
                        title: {
                            display: true,
                            text: "Pression P (bar)",
                            color: theme.titleColor,
                            font: { size: 16, weight: "bold" }
                        },
                        ticks: {
                            color: theme.axisColor,
                            stepSize: Math.max(10, yMax / 5),
                            font: { size: 12 }
                        },
                        grid: { color: theme.gridColor },
                        border: { color: theme.axisColor }
                    }
                }
            }
        });

        isoCharts.push(chart);
    });

    grid.style.display = "grid";
}

// Exporter les fonctions pour une utilisation globale
window.loadIsotherms = loadIsotherms;