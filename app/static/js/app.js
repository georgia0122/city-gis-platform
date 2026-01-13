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
const searchLoading = document.getElementById("searchLoading");

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

async function selectPlace(p) {
  selectedPlace = p;
  placeNameEl.textContent = p.name + (p.city ? ` (${p.city})` : "");
  recTextEl.textContent = "—";
  setAdviceText("正在加载趋势数据…");
  btnAdvice.disabled = true;

  if (map) {
    map.setView([p.lat, p.lng], 13);
  }

  const data = await fetch(`/api/weather_hourly?place_id=${encodeURIComponent(p.id)}`).then(r => r.json());
  latestRainProb = data.rain_prob?.[0] ?? 0.0;

  rainTextEl.textContent = `${Math.round(latestRainProb * 100)}%`;
  updateChart(data.hours, data.temp_c, data.rain_prob, data.wind_mps);

  setAdviceText('趋势已加载。点击"生成出行建议"。');
  btnAdvice.disabled = false;
}

async function loadPlacesAndInitMap() {
  // 创建地图，禁用默认的缩放控件
  map = L.map("map", {
    zoomControl: false  // 禁用默认位置的缩放控件
  }).setView([39.0851, 117.1994], 12);

  // 手动添加缩放控件到左下角
  L.control.zoom({
    position: 'bottomleft'
  }).addTo(map);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap"
  }).addTo(map);

  const places = await fetch("/api/places").then(r => r.json());

  places.forEach(p => {
    const marker = L.marker([p.lat, p.lng]).addTo(map);
    marker.bindPopup(p.name);
    markers[p.id] = marker;

    marker.on("click", async () => {
      await selectPlace(p);
    });
  });

  updateChart([], [], [], []);
}

// 搜索功能 - 支持全球城市搜索
let searchTimeout = null;
searchInput.addEventListener("input", async (e) => {
  clearTimeout(searchTimeout);
  const query = e.target.value.trim();
  
  searchTimeout = setTimeout(async () => {
    if (!query) {
      searchResults.innerHTML = "";
      searchLoading.style.display = "none";
      return;
    }
    
    // 显示加载状态
    searchLoading.style.display = "block";
    searchResults.innerHTML = "";
    
    try {
      // 1. 先搜索预设地点
      const presetResults = await fetch(`/api/search_places?q=${encodeURIComponent(query)}`).then(r => r.json());
      
      // 2. 使用 Nominatim 搜索全球城市
      const nominatimUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=8&addressdetails=1`;
      const nominatimResponse = await fetch(nominatimUrl, {
        headers: {
          'User-Agent': 'GeoWeather Platform'
        }
      });
      const nominatimResults = await nominatimResponse.json();
      
      searchLoading.style.display = "none";
      
      // 合并结果
      const allResults = [];
      
      // 添加预设地点（优先显示）
      if (presetResults.length > 0) {
        allResults.push({
          type: 'preset',
          title: '预设地点',
          items: presetResults
        });
      }
      
      // 添加全球搜索结果
      if (nominatimResults.length > 0) {
        const globalResults = nominatimResults.map(item => ({
          id: `global_${item.place_id}`,
          name: item.display_name.split(',')[0],
          fullName: item.display_name,
          lat: parseFloat(item.lat),
          lng: parseFloat(item.lon),
          city: item.address?.city || item.address?.town || item.address?.village || '',
          country: item.address?.country || ''
        }));
        
        allResults.push({
          type: 'global',
          title: '全球搜索',
          items: globalResults
        });
      }
      
      if (allResults.length === 0) {
        searchResults.innerHTML = '<div style="padding: 8px; color: #999;">未找到匹配的地点</div>';
        return;
      }
      
      // 渲染分组结果
      searchResults.innerHTML = allResults.map(group => `
        <div style="margin-bottom: 8px;">
          <div style="padding: 4px 8px; font-size: 11px; color: #999; font-weight: 600; text-transform: uppercase;">${group.title}</div>
          ${group.items.map(p => `
            <div style="padding: 8px 12px; cursor: pointer; border-radius: 4px; transition: background 0.2s;" 
                 class="search-result-item" 
                 data-place='${JSON.stringify(p)}'>
              <div style="font-weight: 500;">${p.name}</div>
              <div style="font-size: 12px; color: #666;">${p.fullName || (p.city ? p.city : '') + (p.country ? ' ' + p.country : '')}</div>
            </div>
          `).join('')}
        </div>
      `).join('');
      
      // 添加点击事件
      document.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('mouseenter', () => {
          item.style.background = '#f3f4f6';
        });
        item.addEventListener('mouseleave', () => {
          item.style.background = '';
        });
        item.addEventListener('click', async () => {
          const place = JSON.parse(item.dataset.place);
          await selectPlace(place);
          searchInput.value = '';
          searchResults.innerHTML = '';
        });
      });
    } catch (error) {
      console.error('Search error:', error);
      searchLoading.style.display = "none";
      searchResults.innerHTML = '<div style="padding: 8px; color: #ef4444;">搜索失败，请稍后重试</div>';
    }
  }, 500); // 增加到500ms防抖，减少API请求
});

btnAdvice.addEventListener("click", async () => {
  if (!selectedPlace) return;

  btnAdvice.disabled = true;
  setAdviceText("🤔 正在生成建议…");

  try {
    const resp = await fetch("/api/ai_analysis", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        place_id: selectedPlace.id,
        place_name: selectedPlace.name,
        city: selectedPlace.city
      })
    }).then(r => r.json());

    if (resp.error) {
      setAdviceText(`❌ 分析失败: ${resp.error}`);
      btnAdvice.disabled = false;
      return;
    }

    const analysis = resp.analysis;
    const analysisMethod = resp.analysis_method || "rule";  // 获取分析方法
    
    recTextEl.textContent = analysis.recommendation || "—";

    const methodLabel = analysisMethod === "ai" ? "🤖 AI 分析" : "📊 规则分析";
    const methodNote = analysisMethod === "ai" ? "" : " (AI 已降级)";
    
    // 推荐等级的样式
    let recEmoji = "✈️";
    if (analysis.recommendation === "AVOID") {
      recEmoji = "❌";
    } else if (analysis.recommendation === "CAUTION") {
      recEmoji = "⚠️";
    } else if (analysis.recommendation === "GO") {
      recEmoji = "✅";
    }
    
    const lines = [];
    
    // ===== 第一部分：出行建议（顶部突出显示）=====
    lines.push(`${recEmoji} 出行建议: ${analysis.recommendation}${methodNote}`);
    
    // 最佳时间（出行建议下方）
    if (analysis.optimal_time) {
      lines.push(`⏰ 最佳时间段: ${analysis.optimal_time}`);
    }
    
    // 分析方法和置信度
    const confidenceEmoji = analysis.confidence_score >= 0.8 ? "✅" : (analysis.confidence_score >= 0.6 ? "👍" : "📌");
    lines.push(`${confidenceEmoji} 分析方法: ${methodLabel} | 置信度: ${Math.round(analysis.confidence_score * 100)}%`);
    
    lines.push(""); // 空行
    
    // ===== 第二部分：综合评价 =====
    lines.push(`📝 评价: ${analysis.summary}`);
    lines.push(""); // 空行
    
    // ===== 第三部分：建议 =====
    if (analysis.suggestions && analysis.suggestions.length > 0) {
      lines.push("💡 行动建议:");
      analysis.suggestions.forEach((s, idx) => {
        const num = idx + 1;
        lines.push(`   ${num}. ${s}`);
      });
      lines.push(""); // 空行
    }
    
    // ===== 第四部分：风险评估 =====
    if (analysis.risks && analysis.risks.length > 0) {
      lines.push("⚠️ 风险评估:");
      analysis.risks.forEach(risk => {
        const severityEmoji = {
          'HIGH': '🔴',
          'MEDIUM': '🟡',
          'LOW': '🟢'
        }[risk.severity] || '◯';
        lines.push(`   ${severityEmoji} ${risk.risk_type} (${risk.severity})`);
        lines.push(`      └─ ${risk.evidence}`);
      });
    }

    setAdviceText(lines.join("\n"));
  } catch (error) {
    console.error('Analysis error:', error);
    setAdviceText(`❌ 分析失败: ${error.message}`);
  }

  btnAdvice.disabled = false;
});

// 加载预警信息统计
async function loadAlertStats() {
  try {
    const alerts = await fetch('/api/alerts').then(r => r.json());
    const activeAlerts = alerts.filter(a => a.status === 'active');
    const alertCountEl = document.getElementById('alertCount');
    
    if (activeAlerts.length > 0) {
      alertCountEl.textContent = `当前有 ${activeAlerts.length} 条活跃预警，点击查看详情`;
    } else {
      alertCountEl.textContent = '暂无活跃预警，点击查看历史记录';
    }
  } catch (error) {
    console.error('Failed to load alerts:', error);
    document.getElementById('alertCount').textContent = '点击查看预警信息';
  }
}

loadPlacesAndInitMap().catch(err => {
  console.error(err);
  setAdviceText("加载失败，请查看控制台报错。");
});

// 加载预警统计
loadAlertStats();
