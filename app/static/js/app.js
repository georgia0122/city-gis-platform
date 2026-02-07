let selectedPlace = null;
let latestRainProb = null;
let map = null;
let markers = {};
let userLocationMarker = null;
let userLocationCircle = null;

const placeNameEl = document.getElementById("placeName");
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

// 初始显示提示
setAdviceText("🔄 正在自动获取您的位置并生成 AI 出行建议...");

function updateChart(hours, temp, rainProb, wind, uvIndex) {
  // 确保数据是数组，防止报错
  const hArr = Array.isArray(hours) ? hours : [];
  const tArr = Array.isArray(temp) ? temp : [];
  const rArr = Array.isArray(rainProb) ? rainProb : [];
  const wArr = Array.isArray(wind) ? wind : [];
  const uvArr = Array.isArray(uvIndex) ? uvIndex : [];

  chart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["Temp(°C)", "RainProb", "Wind(m/s)", "UV指数"] },
    xAxis: { type: "category", data: hArr.map(h => `${h}h`) },
    yAxis: [{ type: "value" }, { type: "value" }],
    series: [
      { name: "Temp(°C)", type: "line", data: tArr, yAxisIndex: 0, smooth: true },
      { name: "RainProb", type: "line", data: rArr.map(x => Math.round(x * 100)), yAxisIndex: 1, smooth: true },
      { name: "Wind(m/s)", type: "line", data: wArr.map(x => (Math.round(x * 10) / 10)), yAxisIndex: 0, smooth: true },
      { name: "UV指数", type: "line", data: uvArr, yAxisIndex: 0, smooth: true, lineStyle: { color: '#f59e0b' }, itemStyle: { color: '#f59e0b' } },
    ]
  });
}

async function selectPlace(p) {
  try {
    selectedPlace = p;

    // 安全检查：确保DOM元素存在
    if (!placeNameEl || !rainTextEl || !btnAdvice) {
      throw new Error('页面元素未正确加载，请刷新页面');
    }

    placeNameEl.textContent = p.name + (p.city ? ` (${p.city})` : "");
    setAdviceText("正在加载趋势数据…");
    btnAdvice.disabled = true;

    if (map) {
      map.setView([p.lat, p.lng], 13);
    }

    // 记录用户查询
    try {
      await fetch('/api/record-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location: p.name })
      });
    } catch (error) {
      console.log('Failed to record query:', error);
    }

    // 同时发送 ID 和坐标，增强兼容性
    const url = `/api/weather_hourly?place_id=${encodeURIComponent(p.id)}&lat=${p.lat}&lng=${p.lng}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    latestRainProb = data.rain_prob?.[0] ?? 0.0;

    // 更新雨概率显示（带颜色提示）
    const rainPercent = Math.round(latestRainProb * 100);
    let rainColor = '#10b981'; // 绿色 - 低
    let rainDesc = '';
    if (rainPercent > 70) {
      rainColor = '#ef4444'; // 红色 - 高
      rainDesc = '高';
    } else if (rainPercent > 40) {
      rainColor = '#f59e0b'; // 橙色 - 中
      rainDesc = '中等';
    } else {
      rainDesc = '低';
    }
    rainTextEl.innerHTML = `<span style="color: ${rainColor}; font-weight: 600;">${rainPercent}%</span> <span style="font-size: 11px; color: #6b7280;">(${rainDesc})</span>`;
    
    // 更新UV指数显示（带颜色提示）
    const uvTextEl = document.getElementById("uvText");
    if (uvTextEl && data.current_uv !== undefined) {
      const uvValue = data.current_uv;
      let uvColor = '#10b981'; // 绿色 - 低
      let uvDesc = '低';
      
      if (uvValue >= 11) {
        uvColor = '#dc2626'; // 深红 - 极高
        uvDesc = '极高';
      } else if (uvValue >= 8) {
        uvColor = '#ef4444'; // 红色 - 很高
        uvDesc = '很高';
      } else if (uvValue >= 6) {
        uvColor = '#f59e0b'; // 橙色 - 高
        uvDesc = '高';
      } else if (uvValue >= 3) {
        uvColor = '#fbbf24'; // 黄色 - 中等
        uvDesc = '中等';
      }
      
      uvTextEl.innerHTML = `<span style="color: ${uvColor}; font-weight: 600;">${uvValue.toFixed(1)}</span> <span style="font-size: 11px; color: #6b7280;">(${uvDesc})</span>`;
    }
    
    // 更新防晒建议
    const sunProtectionEl = document.getElementById("sunProtection");
    if (sunProtectionEl && data.sun_protection) {
      const sp = data.sun_protection;
      sunProtectionEl.innerHTML = `
        <div style="padding: 12px; background: ${sp.color}22; border-left: 4px solid ${sp.color}; border-radius: 4px; margin-top: 8px;">
          <div style="font-weight: 600; color: ${sp.color}; margin-bottom: 4px;">☀️ ${sp.level} (当前 ${data.current_uv.toFixed(1)} / 最高 ${data.max_uv.toFixed(1)})</div>
          <div style="font-size: 13px; color: #333;">${sp.advice}</div>
        </div>
      `;
    }
    
    updateChart(data.hours, data.temp_c, data.rain_prob, data.wind_mps, data.uv_index);

    setAdviceText('趋势已加载。点击"生成出行建议"。');
    btnAdvice.disabled = false;
  } catch (error) {
    console.error('Select place error:', error);
    setAdviceText(`❌ 加载失败: ${error.message}`);
    updateChart([], [], [], [], []);
    btnAdvice.disabled = true;
  }
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

  // 主图层（OSM）+ 失败时自动切换到 Carto CDN
  const primaryTile = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap",
  });

  const fallbackTile = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19,
    subdomains: "abcd",
    attribution: "© OpenStreetMap, © CARTO"
  });

  primaryTile.on('tileerror', () => {
    if (map.hasLayer(primaryTile)) {
      map.removeLayer(primaryTile);
      fallbackTile.addTo(map);
      console.warn('OSM tile load failed, switched to Carto CDN');
    }
  });

  primaryTile.addTo(map);

  const places = await fetch("/api/places").then(r => r.json());

  places.forEach(p => {
    const marker = L.marker([p.lat, p.lng]).addTo(map);
    marker.bindPopup(p.name);
    markers[p.id] = marker;

    marker.on("click", async () => {
      await selectPlace(p);
    });
  });

  updateChart([], [], [], [], []);
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
        city: selectedPlace.city,
        lat: selectedPlace.lat,
        lng: selectedPlace.lng
      })
    }).then(r => r.json());

    if (resp.error) {
      setAdviceText(`❌ 分析失败: ${resp.error}`);
      btnAdvice.disabled = false;
      return;
    }

    const analysis = resp.analysis;
    const analysisMethod = resp.analysis_method || "rule";  // 获取分析方法
    
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
    const response = await fetch('/api/alerts');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const alerts = await response.json();

    // 确保返回的是数组
    if (!Array.isArray(alerts)) {
      console.warn('Alerts API returned non-array data:', alerts);
      throw new Error('Invalid alerts data format');
    }

    const activeAlerts = alerts.filter(a => a.status === 'active');
    const alertCountEl = document.getElementById('alertCount');

    if (activeAlerts.length > 0) {
      alertCountEl.textContent = `当前有 ${activeAlerts.length} 条活跃预警，点击查看详情`;
    } else {
      alertCountEl.textContent = '暂无活跃预警，点击查看历史记录';
    }
  } catch (error) {
    console.error('Failed to load alerts:', error);
    const alertCountEl = document.getElementById('alertCount');
    if (alertCountEl) {
      alertCountEl.textContent = '点击查看预警信息';
    }
  }
}

loadPlacesAndInitMap().catch(err => {
  console.error(err);
  setAdviceText("加载失败，请查看控制台报错。");
});

// 加载预警统计
loadAlertStats();

// ========== 自动定位功能 ==========

// 自动定位用户（页面加载时调用）
async function autoLocateUser() {
  const locationStatus = document.getElementById('locationStatus');
  const locateBtn = document.getElementById('locateBtn');
  
  // 检查浏览器是否支持定位
  if (!navigator.geolocation) {
    locationStatus.textContent = '您的浏览器不支持定位功能';
    locationStatus.style.color = '#666';
    return;
  }
  
  // 显示正在定位的状态
  locationStatus.textContent = '正在自动获取您的位置...';
  locationStatus.style.color = '#4285f4';
  if (locateBtn) {
    locateBtn.disabled = true;
    locateBtn.innerHTML = '📍 定位中...';
  }
  
  try {
    // 尝试获取位置
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      });
    });
    
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    const accuracy = position.coords.accuracy;
    
    // 移除之前的用户位置标记
    if (userLocationMarker) {
      map.removeLayer(userLocationMarker);
    }
    if (userLocationCircle) {
      map.removeLayer(userLocationCircle);
    }
    
    // 添加精度圆圈
    userLocationCircle = L.circle([lat, lng], {
      radius: accuracy,
      color: '#4285f4',
      fillColor: '#4285f4',
      fillOpacity: 0.15,
      weight: 1
    }).addTo(map);
    
    // 添加用户位置标记
    userLocationMarker = L.marker([lat, lng], {
      icon: createUserLocationIcon(),
      zIndexOffset: 1000
    }).addTo(map);
    
    // 反向地理编码获取地址
    locationStatus.textContent = '正在获取地址信息...';
    const geocodeResult = await reverseGeocode(lat, lng);
    const address = formatAddress(geocodeResult);
    
    // 获取简短的地区名称
    const shortAddress = geocodeResult?.address?.district || 
                         geocodeResult?.address?.suburb || 
                         geocodeResult?.address?.city || 
                         geocodeResult?.address?.town || 
                         '当前位置';
    
    // 绑定弹出窗口
    const popupContent = `
      <div style="min-width: 200px;">
        <div style="font-weight: 600; color: #4285f4; margin-bottom: 8px;">📍 您的当前位置</div>
        <div style="font-size: 13px; color: #333; margin-bottom: 6px;">${address}</div>
        <div style="font-size: 11px; color: #999;">
          坐标: ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
          精度: ±${Math.round(accuracy)}米
        </div>
      </div>
    `;
    userLocationMarker.bindPopup(popupContent).openPopup();
    
    // 移动地图到用户位置
    map.setView([lat, lng], 15);
    
    // 更新状态显示
    locationStatus.innerHTML = `<span style="color: #22c55e;">✓</span> 已定位到 ${shortAddress}`;
    locationStatus.style.color = '#333';
    
    // 创建一个地点对象用于天气查询
    const userPlace = {
      id: `user_location_${Date.now()}`,
      name: '我的位置',
      fullName: address,
      lat: lat,
      lng: lng,
      city: geocodeResult?.address?.city || geocodeResult?.address?.town || geocodeResult?.address?.village || shortAddress,
      country: geocodeResult?.address?.country || ''
    };
    
    // 点击标记时选择该位置
    userLocationMarker.on('click', async () => {
      await selectPlace(userPlace);
    });
    
    // 自动加载天气趋势数据
    placeNameEl.textContent = `我的位置 (${shortAddress})`;
    await selectPlace(userPlace);
    
    // 自动触发 AI 分析生成建议
    locationStatus.textContent = '正在生成 AI 出行建议...';
    await triggerAIAnalysis();
    
    // 更新最终状态
    locationStatus.innerHTML = `<span style="color: #22c55e;">✓</span> ${shortAddress} - AI 建议已生成`;
    
  } catch (error) {
    console.error('Auto location error:', error);
    let errorMsg = '';
    
    switch (error.code) {
      case error.PERMISSION_DENIED:
        errorMsg = '❌ 您拒绝了位置访问权限';
        break;
      case error.POSITION_UNAVAILABLE:
        errorMsg = '❌ 无法获取位置信息';
        break;
      case error.TIMEOUT:
        errorMsg = '❌ 定位超时，请点击按钮重试';
        break;
      default:
        errorMsg = `❌ 自动定位失败`;
    }
    
    locationStatus.textContent = errorMsg;
    locationStatus.style.color = '#ef4444';
    
    // 定位失败时，显示默认提示
    setAdviceText('自动定位失败，请点击"定位我的位置"按钮手动定位，或搜索/点击地图上的地点查看天气。');
  } finally {
    if (locateBtn) {
      locateBtn.disabled = false;
      locateBtn.innerHTML = '📍 定位我的位置';
    }
  }
}

// ========== 用户手动定位功能 ==========
let isLocating = false;

// 创建自定义的用户位置图标
function createUserLocationIcon() {
  return L.divIcon({
    className: 'user-location-marker',
    html: `
      <div style="
        width: 20px;
        height: 20px;
        background: #4285f4;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        position: relative;
      ">
        <div style="
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13]
  });
}

// 反向地理编码获取地址
async function reverseGeocode(lat, lng) {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1&accept-language=zh`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'GeoWeather Platform'
      }
    });
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Reverse geocode error:', error);
    return null;
  }
}

// 格式化地址显示
function formatAddress(geocodeResult) {
  if (!geocodeResult || !geocodeResult.address) {
    return '未知地址';
  }
  
  const addr = geocodeResult.address;
  const parts = [];
  
  // 按优先级添加地址组件
  if (addr.road) parts.push(addr.road);
  if (addr.house_number) parts.push(addr.house_number + '号');
  if (addr.neighbourhood) parts.push(addr.neighbourhood);
  if (addr.suburb) parts.push(addr.suburb);
  if (addr.district) parts.push(addr.district);
  if (addr.city || addr.town || addr.village) {
    parts.push(addr.city || addr.town || addr.village);
  }
  if (addr.state || addr.province) parts.push(addr.state || addr.province);
  if (addr.country) parts.push(addr.country);
  
  return parts.length > 0 ? parts.join(', ') : geocodeResult.display_name || '未知地址';
}

// 获取用户位置（手动点击按钮时调用）
async function getUserLocation() {
  const locateBtn = document.getElementById('locateBtn');
  const locationStatus = document.getElementById('locationStatus');
  
  if (isLocating) return;
  
  if (!navigator.geolocation) {
    locationStatus.textContent = '❌ 您的浏览器不支持定位功能';
    locationStatus.style.color = '#ef4444';
    return;
  }
  
  isLocating = true;
  locateBtn.disabled = true;
  locateBtn.innerHTML = '📍 定位中...';
  locationStatus.textContent = '正在获取您的位置...';
  locationStatus.style.color = '#4285f4';
  
  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      });
    });
    
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    const accuracy = position.coords.accuracy;
    
    // 移除之前的用户位置标记
    if (userLocationMarker) {
      map.removeLayer(userLocationMarker);
    }
    if (userLocationCircle) {
      map.removeLayer(userLocationCircle);
    }
    
    // 添加精度圆圈
    userLocationCircle = L.circle([lat, lng], {
      radius: accuracy,
      color: '#4285f4',
      fillColor: '#4285f4',
      fillOpacity: 0.15,
      weight: 1
    }).addTo(map);
    
    // 添加用户位置标记
    userLocationMarker = L.marker([lat, lng], {
      icon: createUserLocationIcon(),
      zIndexOffset: 1000
    }).addTo(map);
    
    // 反向地理编码获取地址
    locationStatus.textContent = '正在获取地址信息...';
    const geocodeResult = await reverseGeocode(lat, lng);
    const address = formatAddress(geocodeResult);
    
    // 获取简短的地区名称
    const shortAddress = geocodeResult?.address?.district || 
                         geocodeResult?.address?.suburb || 
                         geocodeResult?.address?.city || 
                         geocodeResult?.address?.town || 
                         '当前位置';
    
    // 绑定弹出窗口
    const popupContent = `
      <div style="min-width: 200px;">
        <div style="font-weight: 600; color: #4285f4; margin-bottom: 8px;">📍 您的当前位置</div>
        <div style="font-size: 13px; color: #333; margin-bottom: 6px;">${address}</div>
        <div style="font-size: 11px; color: #999;">
          坐标: ${lat.toFixed(6)}, ${lng.toFixed(6)}<br>
          精度: ±${Math.round(accuracy)}米
        </div>
      </div>
    `;
    userLocationMarker.bindPopup(popupContent).openPopup();
    
    // 移动地图到用户位置
    map.setView([lat, lng], 15);
    
    // 创建一个地点对象用于天气查询
    const userPlace = {
      id: `user_location_${Date.now()}`,
      name: '我的位置',
      fullName: address,
      lat: lat,
      lng: lng,
      city: geocodeResult?.address?.city || geocodeResult?.address?.town || geocodeResult?.address?.village || shortAddress,
      country: geocodeResult?.address?.country || ''
    };
    
    // 点击标记时选择该位置
    userLocationMarker.on('click', async () => {
      await selectPlace(userPlace);
    });
    
    // 自动加载天气趋势数据
    placeNameEl.textContent = `我的位置 (${shortAddress})`;
    await selectPlace(userPlace);
    
    // 自动触发 AI 分析生成建议
    locationStatus.textContent = '正在生成 AI 出行建议...';
    await triggerAIAnalysis();
    
    // 更新最终状态
    locationStatus.innerHTML = `<span style="color: #22c55e;">✓</span> ${shortAddress} - AI 建议已生成`;
    
  } catch (error) {
    console.error('Geolocation error:', error);
    let errorMsg = '定位失败';
    
    switch (error.code) {
      case error.PERMISSION_DENIED:
        errorMsg = '❌ 您拒绝了位置访问权限';
        break;
      case error.POSITION_UNAVAILABLE:
        errorMsg = '❌ 无法获取位置信息';
        break;
      case error.TIMEOUT:
        errorMsg = '❌ 定位超时，请重试';
        break;
      default:
        errorMsg = `❌ 定位失败: ${error.message}`;
    }
    
    locationStatus.textContent = errorMsg;
    locationStatus.style.color = '#ef4444';
  } finally {
    isLocating = false;
    locateBtn.disabled = false;
    locateBtn.innerHTML = '📍 定位我的位置';
  }
}

// 触发 AI 分析的函数（复用 btnAdvice 的逻辑）
async function triggerAIAnalysis() {
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
        city: selectedPlace.city,
        lat: selectedPlace.lat,
        lng: selectedPlace.lng
      })
    }).then(r => r.json());

    if (resp.error) {
      setAdviceText(`❌ 分析失败: ${resp.error}`);
      btnAdvice.disabled = false;
      return;
    }

    const analysis = resp.analysis;
    const analysisMethod = resp.analysis_method || "rule";
    
    const methodLabel = analysisMethod === "ai" ? "🤖 AI 分析" : "📊 规则分析";
    const methodNote = analysisMethod === "ai" ? "" : " (AI 已降级)";
    
    let recEmoji = "✈️";
    if (analysis.recommendation === "AVOID") {
      recEmoji = "❌";
    } else if (analysis.recommendation === "CAUTION") {
      recEmoji = "⚠️";
    } else if (analysis.recommendation === "GO") {
      recEmoji = "✅";
    }
    
    const lines = [];
    
    lines.push(`${recEmoji} 出行建议: ${analysis.recommendation}${methodNote}`);
    
    if (analysis.optimal_time) {
      lines.push(`⏰ 最佳时间段: ${analysis.optimal_time}`);
    }
    
    const confidenceEmoji = analysis.confidence_score >= 0.8 ? "✅" : (analysis.confidence_score >= 0.6 ? "👍" : "📌");
    lines.push(`${confidenceEmoji} 分析方法: ${methodLabel} | 置信度: ${Math.round(analysis.confidence_score * 100)}%`);
    
    lines.push("");
    
    lines.push(`📝 评价: ${analysis.summary}`);
    lines.push("");
    
    if (analysis.suggestions && analysis.suggestions.length > 0) {
      lines.push("💡 行动建议:");
      analysis.suggestions.forEach((s, idx) => {
        const num = idx + 1;
        lines.push(`   ${num}. ${s}`);
      });
      lines.push("");
    }
    
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
}

// 绑定定位按钮事件
document.getElementById('locateBtn')?.addEventListener('click', getUserLocation);
