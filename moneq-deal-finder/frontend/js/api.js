class MoneqApiClient {
  constructor() {
    this.baseUrl = window.MONEQ_CONFIG.API_BASE_URL;
    this.isBackendConnected = false;
  }

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/api/health`);
      if (!res.ok) throw new Error('Health check failed');
      this.isBackendConnected = true;
      return await res.json();
    } catch (e) {
      this.isBackendConnected = false;
      return null;
    }
  }

  async getDeals({ q = '', category = '전체', sortBy = 'profit', savedOnly = false } = {}) {
    const params = new URLSearchParams({
      q,
      category,
      sort_by: sortBy,
      saved_only: String(savedOnly)
    });
    const res = await fetch(`${this.baseUrl}/api/deals?${params.toString()}`);
    if (!res.ok) throw new Error('매물 조회 실패');
    return await res.json();
  }

  async toggleSaveDeal(platform, externalId) {
    const res = await fetch(
      `${this.baseUrl}/api/deals/${encodeURIComponent(platform)}/${encodeURIComponent(externalId)}/save`,
      { method: 'POST' }
    );
    if (!res.ok) throw new Error('관심 매물 저장 실패');
    return await res.json();
  }

  async analyzeProduct(query) {
    const res = await fetch(`${this.baseUrl}/api/analyze?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error('시세 분석 실패');
    return await res.json();
  }

  async recommendByBudget(budget, minRoiPercent = 8.0, category = '전체') {
    const res = await fetch(`${this.baseUrl}/api/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        budget: Number(budget),
        min_roi_percent: Number(minRoiPercent),
        category
      })
    });
    if (!res.ok) throw new Error('예산 기반 추천 실패');
    return await res.json();
  }

  async generateListing(payload) {
    const res = await fetch(`${this.baseUrl}/api/listing/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('판매글 생성 실패');
    return await res.json();
  }
}

window.moneqApi = new MoneqApiClient();
