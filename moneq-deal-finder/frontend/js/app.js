const CATEGORIES = [
  "전체",
  "아이폰 및 갤럭시",
  "명품 가방 및 지갑",
  "명품 시계",
  "에어팟 및 헤드폰",
  "노트북 및 태블릿",
  "게임기",
  "카메라",
  "기타 중고 전자제품"
];

let selectedCategory = "전체";
let deferredPrompt = null;

function formatWon(num) {
  if (num === null || num === undefined) return "데이터 부족";
  return Number(num).toLocaleString("ko-KR") + "원";
}

function renderDealCard(deal, extraNote = null) {
  const isSample = deal.data_source_type !== "LIVE_API";
  const sourceBadge = isSample
    ? `<span class="badge badge-sample">SAMPLE / 테스트 데이터</span>`
    : `<span class="badge badge-live">LIVE API 실데이터</span>`;

  return `
    <article class="deal-card">
      <div>
        <div class="badge-row" style="margin-bottom:8px;">
          <span class="badge badge-platform">${deal.platform}</span>
          ${sourceBadge}
          <span class="badge badge-roi">ROI +${deal.profit.roi_percent}%</span>
        </div>
        <div class="deal-title">${deal.title}</div>
        <div style="font-size:0.78rem; color:var(--text-secondary); margin-top:4px;">
          ${deal.category} · 상태: ${deal.condition}
        </div>
      </div>

      <div class="price-box">
        <div>
          <div style="color:var(--text-secondary);">매입가 (시세 대비 -${deal.discount_percent}%)</div>
          <div class="mono" style="font-weight:700; font-size:0.95rem;">${formatWon(deal.price)}</div>
        </div>
        <div>
          <div style="color:var(--text-secondary);">예상 순이익</div>
          <div class="mono profit-highlight">+${formatWon(deal.profit.net_profit)}</div>
        </div>
        <div>
          <div style="color:var(--text-secondary);">동일 모델 평균 시세</div>
          <div class="mono">${formatWon(deal.market_avg_price)}</div>
        </div>
        <div>
          <div style="color:var(--text-secondary);">예상 판매가 (비용 차감 전)</div>
          <div class="mono">${formatWon(deal.profit.expected_sell_price)}</div>
        </div>
      </div>

      ${extraNote ? `<div style="font-size:0.8rem; background:rgba(0,255,157,0.06); padding:8px 10px; border-radius:8px; color:#D1FAE5;">💡 ${extraNote}</div>` : ""}

      <div class="deal-meta">
        <span>📍 ${deal.region}</span>
        <span>🕒 ${deal.posted_at}</span>
      </div>

      <div class="card-actions">
        <a href="${deal.url}" target="_blank" rel="noopener noreferrer" class="btn-primary">원본 매물 보기</a>
        <button class="btn-secondary" onclick="handleSaveDeal('${deal.platform}', '${deal.external_id}')">
          ${deal.is_saved ? "★ 저장됨" : "☆ 관심 저장"}
        </button>
        <button class="btn-secondary" onclick="prefillListing('${deal.model_name.replace(/'/g, "")}', ${deal.price})">
          판매글 생성
        </button>
      </div>
    </article>
  `;
}

async function loadBudgetRecommendations() {
  const budget = Number(document.getElementById("budgetInput").value || 500000);
  const category = document.getElementById("budgetCategorySelect").value;
  document.getElementById("kpiBudget").textContent = formatWon(budget);

  const container = document.getElementById("recommendList");
  container.innerHTML = `<p style="color:var(--text-secondary);">AI가 예산 내 고수익 매물을 계산 중입니다...</p>`;

  try {
    const recs = await window.moneqApi.recommendByBudget(budget, 5.0, category);
    document.getElementById("kpiRecCount").textContent = `${recs.length}건`;
    if (recs.length > 0) {
      const maxProfit = Math.max(...recs.map((r) => r.deal.profit.net_profit));
      const maxRoi = Math.max(...recs.map((r) => r.deal.profit.roi_percent));
      document.getElementById("kpiMaxProfit").textContent = `+${formatWon(maxProfit)}`;
      document.getElementById("kpiMaxRoi").textContent = `+${maxRoi}%`;
      container.innerHTML = recs.map((r) => renderDealCard(r.deal, `${r.reason}<br/>⚠️ ${r.caution}`)).join("");
    } else {
      document.getElementById("kpiMaxProfit").textContent = "0원";
      document.getElementById("kpiMaxRoi").textContent = "0%";
      container.innerHTML = `<div class="panel-box">입력하신 예산(${formatWon(budget)}) 이내에서 순이익이 발생하는 매물이 현재 없습니다. 예산을 상향하거나 카테고리를 전체로 변경해 보세요.</div>`;
    }
  } catch (err) {
    container.innerHTML = `<div class="panel-box" style="color:var(--danger-red);">백엔드 서버에 연결할 수 없습니다. README의 백엔드 실행 방법을 확인해 주세요. (${err.message})</div>`;
  }
}

async function loadDeals() {
  const q = document.getElementById("dealSearchInput").value.trim();
  const sortBy = document.getElementById("dealSortSelect").value;
  const container = document.getElementById("dealsList");
  try {
    const deals = await window.moneqApi.getDeals({ q, category: selectedCategory, sortBy });
    container.innerHTML = deals.length
      ? deals.slice(0, 10).map((d) => renderDealCard(d)).join("")
      : `<div class="panel-box">조건에 일치하는 매물이 없습니다.</div>`;
  } catch (err) {
    container.innerHTML = `<div class="panel-box" style="color:var(--danger-red);">매물 로드 오류: ${err.message}</div>`;
  }
}

async function loadSavedDeals() {
  const container = document.getElementById("savedDealsList");
  try {
    const deals = await window.moneqApi.getDeals({ savedOnly: true });
    container.innerHTML = deals.length
      ? deals.map((d) => renderDealCard(d)).join("")
      : `<div class="panel-box">저장된 관심 매물이 없습니다. 매물 카드에서 [☆ 관심 저장]을 눌러 추가하세요.</div>`;
  } catch (err) {
    container.innerHTML = `<div class="panel-box">오류: ${err.message}</div>`;
  }
}

async function handleSaveDeal(platform, externalId) {
  await window.moneqApi.toggleSaveDeal(platform, externalId);
  await loadBudgetRecommendations();
  await loadDeals();
  await loadSavedDeals();
}

function prefillListing(productName, buyPrice) {
  document.getElementById("listProductName").value = productName;
  document.getElementById("listBuyPrice").value = buyPrice;
  switchTab("tab-listing");
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
  document.getElementById(tabId).classList.remove("hidden");

  document.querySelectorAll(".tab-btn, .bottom-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  if (tabId === "tab-deals") loadDeals();
  if (tabId === "tab-saved") loadSavedDeals();
}

async function initApp() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById("pwaInstallBtn").classList.remove("hidden");
  });

  document.getElementById("pwaInstallBtn").addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
  });

  const catContainer = document.getElementById("categoryChips");
  catContainer.innerHTML = CATEGORIES.map(
    (c) => `<button class="chip ${c === selectedCategory ? "active" : ""}" data-cat="${c}">${c}</button>`
  ).join("");

  catContainer.addEventListener("click", (e) => {
    if (!e.target.dataset.cat) return;
    selectedCategory = e.target.dataset.cat;
    catContainer.querySelectorAll(".chip").forEach((el) => el.classList.toggle("active", el.dataset.cat === selectedCategory));
    loadDeals();
  });

  document.querySelectorAll(".tab-btn, .bottom-item").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  document.querySelectorAll("[data-budget]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-budget]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("budgetInput").value = btn.dataset.budget;
      loadBudgetRecommendations();
    });
  });

  document.getElementById("runBudgetBtn").addEventListener("click", loadBudgetRecommendations);
  document.getElementById("searchDealsBtn").addEventListener("click", loadDeals);
  document.getElementById("dealSortSelect").addEventListener("change", loadDeals);

  document.getElementById("runAnalyzeBtn").addEventListener("click", async () => {
    const q = document.getElementById("analyzeQueryInput").value.trim();
    if (!q) return;
    const box = document.getElementById("analyzeResultBox");
    box.innerHTML = `<p style="color:var(--text-secondary);">데이터 검증 및 시세 분석 중...</p>`;
    try {
      const res = await window.moneqApi.analyzeProduct(q);
      if (res.status === "INSUFFICIENT_DATA") {
        box.innerHTML = `<div class="transparency-banner">⚠️ <strong>데이터 부족:</strong> ${res.message}</div>`;
        return;
      }
      box.innerHTML = `
        <div class="analysis-grid">
          <div class="kpi-card"><div class="kpi-label">정확한 모델명</div><div style="font-weight:700; margin-top:4px;">${res.exact_model}</div></div>
          <div class="kpi-card"><div class="kpi-label">현재 최저 중고 시세</div><div class="kpi-val green">${formatWon(res.current_used_price)}</div></div>
          <div class="kpi-card"><div class="kpi-label">평균 / 중간 시세</div><div class="kpi-val">${formatWon(res.average_price)} / ${formatWon(res.median_price)}</div></div>
          <div class="kpi-card"><div class="kpi-label">예상 리셀 판매가</div><div class="kpi-val green">${formatWon(res.expected_resale_price)}</div></div>
          <div class="kpi-card"><div class="kpi-label">예상 판매 경쟁도</div><div style="font-weight:700; margin-top:4px;">${res.competition_level}</div></div>
          <div class="kpi-card"><div class="kpi-label">확인 시각 / 출처</div><div style="font-size:0.8rem; margin-top:4px;">${res.checked_at}<br/>${res.sources.join(", ")}</div></div>
        </div>
      `;
    } catch (err) {
      box.innerHTML = `<p style="color:var(--danger-red);">분석 오류: ${err.message}</p>`;
    }
  });

  document.getElementById("generateListingBtn").addEventListener("click", async () => {
    const product_name = document.getElementById("listProductName").value.trim();
    const buy_price = Number(document.getElementById("listBuyPrice").value || 0);
    if (!product_name || buy_price <= 0) {
      alert("상품명과 매입가격을 입력해 주세요.");
      return;
    }
    const box = document.getElementById("listingResultBox");
    box.innerHTML = `<p style="color:var(--text-secondary);">AI 판매글 초안 작성 중...</p>`;
    try {
      const res = await window.moneqApi.generateListing({
        product_name,
        buy_price,
        condition: document.getElementById("listCondition").value,
        included_items: document.getElementById("listItems").value,
        defects: document.getElementById("listDefects").value
      });
      box.innerHTML = `
        <div class="transparency-banner">ℹ️ ${res.publish_notice} (${res.ai_engine_mode})</div>
        <div class="kpi-card" style="margin-bottom:10px;">
          <div class="kpi-label">AI 추천 제목 &amp; 적정 판매가</div>
          <div style="font-weight:700; font-size:1rem; margin-top:4px;">${res.ai_title} — <span class="mono" style="color:var(--neon-green);">${formatWon(res.recommended_price)}</span></div>
        </div>
        ${Object.entries(res.platform_formats).map(([plat, text]) => `
          <div class="kpi-card" style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <strong>${plat} 등록 양식</strong>
              <button class="btn btn-secondary" style="padding:3px 10px; font-size:0.75rem;" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.value); alert('${plat} 양식이 복사되었습니다.');">복사하기</button>
            </div>
            <textarea rows="5" style="width:100%; font-size:0.85rem;" readonly>${text}</textarea>
          </div>
        `).join("")}
      `;
    } catch (err) {
      box.innerHTML = `<p style="color:var(--danger-red);">생성 오류: ${err.message}</p>`;
    }
  });

  const health = await window.moneqApi.checkHealth();
  const statusEl = document.getElementById("connectionStatus");
  if (health) {
    statusEl.textContent = "API 서버 정상 연결됨";
    statusEl.classList.add("live");
  } else {
    statusEl.textContent = "백엔드 미실행 (로컬 서버 필요)";
  }

  await loadBudgetRecommendations();
}

document.addEventListener("DOMContentLoaded", initApp);
