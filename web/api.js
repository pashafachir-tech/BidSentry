const API_ROOT = "/api";

let currentAuthToken = "";

export function setAuthToken(token) {
  currentAuthToken = (token || "").trim();
}

export function getAuthToken() {
  return currentAuthToken;
}

async function request(path, options = {}) {
  const timeoutSignal = AbortSignal.timeout(options.timeout ?? 30000);
  const headers = {
    Accept: "application/json",
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(currentAuthToken ? { Authorization: `Bearer ${currentAuthToken}` } : {}),
    ...options.headers,
  };
  try {
    const response = await fetch(`${API_ROOT}${path}`, {
      ...options,
      signal: options.signal ? AbortSignal.any([options.signal, timeoutSignal]) : timeoutSignal,
      headers,
    });
    if (response.status === 401) {
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("bidsentry:auth-required", { detail: { path } }));
      }
      const body = await response.json().catch(() => null);
      throw new Error(body?.error?.message || "Token akses tidak valid atau belum diberikan (401).");
    }
    const body = await response.json().catch(() => null);
    if (!response.ok) throw new Error(body?.error?.message || `Permintaan gagal (${response.status}).`);
    return body?.data;
  } catch (error) {
    if (error.name === "AbortError" || error.name === "TimeoutError") throw new Error("Waktu tunggu habis. Periksa koneksi server.");
    throw error;
  }
}

export const api = {
  health: () => request("/health"),
  overview: () => request("/overview"),
  audits: ({ q = "", risk = "ALL" } = {}) => request(`/audits?${new URLSearchParams({ q, risk })}`),
  getAudit: (auditId) => request(`/audit?${new URLSearchParams({ audit_id: auditId })}`),
  deleteAudit: (auditId) => request(`/audits?${new URLSearchParams({ audit_id: auditId })}`, { method: "DELETE" }),
  evaluateAudit: (input) => request("/v1/audit/evaluate", { method: "POST", body: JSON.stringify(input), timeout: 60000 }),
  createAudit: (input) => request("/v1/audit/evaluate", { method: "POST", body: JSON.stringify(input), timeout: 60000 }),
  createSanggahan: (input) => request("/v1/audit/sanggahan-doc", { method: "POST", body: JSON.stringify(input), timeout: 60000 }),
  reviewFeedback: (auditId = "") => request(`/review-feedback${auditId ? `?${new URLSearchParams({ audit_id: auditId })}` : ""}`),
  recordFindingReview: (input) => request("/review-feedback", { method: "POST", body: JSON.stringify(input) }),
  extractDocument: (file) => request(`/documents/extract?${new URLSearchParams({ filename: file.name })}`, {
    method: "POST", body: file, headers: { "Content-Type": "application/octet-stream" }, timeout: 60000,
  }),
  dispatch: (input) => request("/dispatch", { method: "POST", body: JSON.stringify(input), timeout: 60000 }),
  integrationSettings: () => request("/settings/integrations"),
  testIntegrations: () => request("/settings/integrations/test", { timeout: 60000 }),
  saveIntegrationSettings: (input) => request("/settings/integrations", { method: "PUT", body: JSON.stringify(input) }),
  exportWorkbook: (input) => request("/export/workbook", { method: "POST", body: JSON.stringify(input), timeout: 60000 }),
};
