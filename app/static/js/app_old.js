let selectedPlace = null;
let latestRainProb = null;
let map = null;
let markers = {};

const placeNameEl = document.getElementById("placeName");
const recTextEl = document.getElementById("recText");
const rainTextEl = document.getElementById("rainText");
const btnAdvice = document.getElementById("btnAdvice");
const adviceBox = document.getElementById("adviceBox");
const searchInput = document.getElementById("searchInput");
const searchResults = document.getElementById("searchResults");

const chart = echarts.init(document.getElementById("chart"));

function setAdviceText(text) {
  adviceBox.textContent = text;
}

function updateChart(hours, temp, rainProb, wind) {
  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Temp(°C)", "RainProb", "Wind(m/s)"] },
    xAxis: { type: "category", data: hours.map(h => `${h}h`) },
    yAxis: [{ type: "value" }, { type: "value" }],
    series: [
      { name: "Temp(°C)", type: "line", data: temp, yAxisIndex: 0, smooth: true },
      { name: "RainProb", type: "line", data: rainProb.map(x => Math.round(x * 100)), yAxisIndex: 1, smooth: true },
      { name: "Wind(m/s)", type: "line", data: wind.map(x => (Math.round(x * 10) / 10)), yAxisIndex: 0, smooth: true },
    ]
  });
}

async function loadPlacesAndInitMap() {
  // 地图初始化（天津）
  const map = L.map("map").setView([39.0851, 117.1994], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap"
  }).addTo(map);

  const places = await fetch("/api/places").then(r => r.json());

  places.forEach(p => {
    const marker = L.marker([p.lat, p.lng]).addTo(map);
    marker.bindPopup(p.name);

    marker.on("click", async () => {
      selectedPlace = p;
      placeNameEl.textContent = p.name;
      recTextEl.textContent = "—";
      setAdviceText("正在加载趋势数据…");
      btnAdvice.disabled = true;

      const data = await fetch(`/api/weather_hourly?place_id=${encodeURIComponent(p.id)}`).then(r => r.json());
      latestRainProb = data.rain_prob?.[0] ?? 0.0;

      rainTextEl.textContent = `${Math.round(latestRainProb * 100)}%`;
      updateChart(data.hours, data.temp_c, data.rain_prob, data.wind_mps);

      setAdviceText("趋势已加载。点击“生成出行建议”。");
      btnAdvice.disabled = false;
    });
  });

  // 默认图表空状态
  updateChart([], [], [], []);
}

btnAdvice.addEventListener("click", async () => {
  if (!selectedPlace) return;

  btnAdvice.disabled = true;
  setAdviceText("AI 正在生成建议…");

  const resp = await fetch("/api/ai/travel_advice", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      place_id: selectedPlace.id,
      mode: "walk",
      rain_prob: latestRainProb
    })
  }).then(r => r.json());

  recTextEl.textContent = resp.recommendation || "—";

  const lines = [];
  lines.push(`推荐：${resp.recommendation}`);
  lines.push(`置信度：${Math.round((resp.confidence || 0) * 100)}%`);
  lines.push("");
  lines.push("风险点：");
  (resp.top_risks || []).forEach(x => lines.push(`- ${x.risk} / ${x.level}（${x.evidence}）`));
  lines.push("");
  lines.push("建议：");
  (resp.actionable_tips || []).forEach(t => lines.push(`- ${t}`));

  setAdviceText(lines.join("\n"));
  btnAdvice.disabled = false;
});

loadPlacesAndInitMap().catch(err => {
  console.error(err);
  setAdviceText("加载失败，请查看控制台报错。");
});
