let presentation = false;
try { presentation = localStorage.getItem("bidsentry-presentation") === "on"; } catch {}

const initialState = {
  // Session: { authenticated, role: "pokja" | "vendor", label, capabilities, roles }
  session: null, sessionChecked: false,
  overview: null, audits: [], selectedAuditId: null, currentAudit: null,
  query: "", riskFilter: "ALL", integrations: null, loading: true,
  activeView: "overview", reviewFilter: "ALL", expandedFindingId: null,
  reviewTab: "matrix", reviewInsightsVisited: false,
  adendumActive: true, exposureDays: 35, customReview: null, lastAuditDraft: null,
  reviewFeedback: null, crossSummaryTab: "project",
  proof: null, proofIntegrity: null, proofLoading: false, presentation,
  benchmark: null, economics: null, economicsInputs: {}, roleTransition: null,
  hideHints: false,
};

let state = { ...initialState };
const listeners = new Set();

export function getState() { return state; }
export function setState(patch, { notify = true } = {}) {
  state = { ...state, ...patch };
  if (notify) for (const listener of listeners) listener(state);
}
export function resetWorkspaceState() {
  // Clean isolation between Pokja and Vendor: nothing from the previous workspace survives.
  state = { ...initialState, session: state.session, sessionChecked: true, presentation: state.presentation, benchmark: state.benchmark, hideHints: state.hideHints };
  for (const listener of listeners) listener(state);
}
export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
export function userRole(current = state) {
  return current.session?.role || null;
}
