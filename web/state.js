const initialState = {
  overview: null, audits: [], selectedAuditId: null, currentAudit: null,
  query: "", riskFilter: "ALL", integrations: null, loading: true,
  activeView: "overview", reviewFilter: "ALL", expandedFindingId: null,
  reviewTab: "matrix", reviewInsightsVisited: false,
  adendumActive: true, exposureDays: 35, customReview: null, lastAuditDraft: null,
  reviewFeedback: null, userPerspective: "pokja", crossSummaryTab: "project",
};

let state = { ...initialState };
const listeners = new Set();

export function getState() { return state; }
export function setState(patch, { notify = true } = {}) {
  state = { ...state, ...patch };
  if (notify) for (const listener of listeners) listener(state);
}
export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
