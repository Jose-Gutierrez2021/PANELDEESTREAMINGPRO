document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("salesChart");
  if (!canvas || typeof Chart === "undefined") {
    return;
  }

  const formatCurrency = (value) => {
    const number = Number(value) || 0;
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: window.salesCurrency || "COP",
      maximumFractionDigits: 0
    }).format(number);
  };

  const context = canvas.getContext("2d");
  const gradient = context.createLinearGradient(0, 0, 0, 260);
  gradient.addColorStop(0, "rgba(213, 177, 94, 0.38)");
  gradient.addColorStop(0.38, "rgba(213, 177, 94, 0.12)");
  gradient.addColorStop(1, "rgba(213, 177, 94, 0.01)");

  new Chart(canvas, {
    type: "line",
    data: {
      labels: window.salesLabels || [],
      datasets: [{
        label: "Ingresos",
        data: window.salesValues || [],
        borderColor: "#d5b15e",
        backgroundColor: gradient,
        borderWidth: 2.5,
        fill: true,
        tension: 0.38,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: "#f5d98a",
        pointBorderColor: "#17150f",
        pointBorderWidth: 2,
        cubicInterpolationMode: "monotone"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: "index"
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          displayColors: false,
          backgroundColor: "rgba(16, 16, 14, 0.96)",
          borderColor: "rgba(213, 177, 94, 0.35)",
          borderWidth: 1,
          titleColor: "#d9d5c9",
          bodyColor: "#f9f3dd",
          padding: 12,
          cornerRadius: 12,
          callbacks: {
            label: (context) => ` ${formatCurrency(context.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          border: {
            display: false
          },
          ticks: {
            color: "#8d8a82",
            font: {
              family: "DM Sans",
              size: 11
            }
          }
        },
        y: {
          beginAtZero: true,
          border: {
            display: false
          },
          grid: {
            color: "rgba(255, 255, 255, 0.06)",
            drawBorder: false
          },
          ticks: {
            color: "#8d8a82",
            maxTicksLimit: 5,
            padding: 10,
            callback: (value) => formatCurrency(value)
          }
        }
      }
    }
  });
});
