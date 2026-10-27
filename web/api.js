const API_ROOT = "/api";

async function request(path, options = {}) {
  const timeoutSignal = AbortSignal.timeout(options.timeout ?? 30000);
  try {
    const response = await fetch(`${API_ROOT}${path}`, {
      ...options,
      signal: options.signal ? AbortSignal.any([options.signal, timeoutSignal]) : timeoutSignal,
      headers: { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers },
    });
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
