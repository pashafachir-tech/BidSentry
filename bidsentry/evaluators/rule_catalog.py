"""Canonical catalog of every finding code the deterministic engine can emit.

Each rule declares:

* ``family`` – the canonical concept used for benchmarking. Labels written with
  older or alternative IDs are mapped to a family through ``aliases`` so that a
  correct detection is never scored as a miss because of naming drift.
* ``party`` – whose document the finding is about. Only ``tender_document``
  gaps can be raised in a vendor objection letter; ``bidder_evidence`` gaps are
  the bidder's own homework.
* ``critical_on_gap`` – a confirmed gap on this rule alone puts the package in
  the *Kritis* risk tier (unlimited liability, budget illegality, integrity).
* ``legal_reference`` – a *candidate* reference for reviewers. Every entry is
  marked ``PERLU_VERIFIKASI_HUKUM`` until a legal reviewer confirms the article
  against the consolidated regulation text in force on the package date.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class RuleSpec:
    code: str
    family: str
    title: str
    category: str
    party: Literal["tender_document", "bidder_evidence"]
    default_severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"
    critical_on_gap: bool = False
    legal_reference: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)


_PERPRES = "Perpres 16/2018 jo. Perpres 12/2021 jo. Perpres 46/2025 (naskah konsolidasi LKPP)"

_RULES: tuple[RuleSpec, ...] = (
    # --- Bidder evidence (administrasi penyedia) ---------------------------
    RuleSpec("ADM-NPWP", "ADM-NPWP", "Format NPWP", "Administrasi", "bidder_evidence", "MEDIUM",
             legal_reference="UU KUP dan ketentuan teknis NPWP DJP (format 15/16 digit)"),
    RuleSpec("ADM-KSWP", "ADM-KSWP", "Status KSWP/perpajakan", "Administrasi", "bidder_evidence", "MEDIUM",
             legal_reference="Ketentuan Konfirmasi Status Wajib Pajak (KSWP) DJP"),
    RuleSpec("ADM-NIB", "ADM-NIB", "Nomor Induk Berusaha (NIB)", "Administrasi", "bidder_evidence", "MEDIUM",
             legal_reference="PP 5/2021 tentang Perizinan Berusaha Berbasis Risiko"),
    RuleSpec("ADM-SBU", "ADM-SBU", "Masa berlaku SBU", "Administrasi", "bidder_evidence", "HIGH",
             legal_reference="UU 2/2017 Jasa Konstruksi jo. PP 14/2021"),
    RuleSpec("ADM-BOND", "ADM-BOND", "Nilai jaminan penawaran", "Administrasi", "bidder_evidence", "HIGH",
             legal_reference=f"{_PERPRES}, ketentuan jaminan penawaran"),
    RuleSpec("ADM-WARRANTY", "ADM-WARRANTY", "Lama garansi/jaminan", "Administrasi", "bidder_evidence", "HIGH",
             legal_reference="Ketentuan garansi pada Dokumen Pemilihan paket"),
    RuleSpec("ADM-EXPERTS", "ADM-EXPERTS", "Kualifikasi & sertifikasi tenaga ahli", "Administrasi", "bidder_evidence", "MEDIUM",
             legal_reference="Persyaratan personel inti pada Dokumen Pemilihan paket"),
    # --- Tender document red flags -----------------------------------------
    RuleSpec("ADD-CHANGE", "ADD-CHANGE", "Perubahan persyaratan adendum", "Adendum", "tender_document", "MEDIUM",
             legal_reference="Ketentuan adendum Dokumen Pemilihan (Peraturan LKPP 4/2024)"),
    RuleSpec("CON-PENALTY", "CON-PENALTY", "Klausul denda keterlambatan tanpa batas maksimum", "Kontrak", "tender_document", "HIGH",
             critical_on_gap=True,
             legal_reference=f"{_PERPRES}, ketentuan denda keterlambatan 1‰ per hari; batas akumulasi wajib dicek pada SSKK/SDP"),
    RuleSpec("CON-PENALTY-RATE", "CON-PENALTY-RATE", "Tarif denda harian di atas pembanding 1‰", "Kontrak", "tender_document", "MEDIUM",
             legal_reference=f"{_PERPRES}, ketentuan denda keterlambatan 1‰ per hari"),
    RuleSpec("SPEC-LOCKIN-CPU", "SPEC-LOCKIN", "Spesifikasi mengunci merek/arsitektur prosesor", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)", aliases=("SPEC-LOCKIN-PROC",)),
    RuleSpec("SPEC-LOCKIN-GPU", "SPEC-LOCKIN", "Spesifikasi mengunci akselerator/GPU tertentu", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)"),
    RuleSpec("SPEC-LOCKIN-MGMT", "SPEC-LOCKIN", "Spesifikasi mengunci sistem manajemen/storage vendor", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)"),
    RuleSpec("SPEC-LOCKIN-NETWORKING", "SPEC-LOCKIN", "Spesifikasi mengunci perangkat jaringan tertentu", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)"),
    RuleSpec("SPEC-LOCKIN-SOFTWARE", "SPEC-LOCKIN", "Spesifikasi mengunci perangkat lunak/database tertentu", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)"),
    RuleSpec("SPEC-BRAND-LOCKIN", "SPEC-LOCKIN", "Spesifikasi mengarah ke merek tertentu", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)"),
    RuleSpec("SPEC-AI-LOCKIN", "SPEC-LOCKIN", "Penyebutan merek (diekstrak AI, divalidasi Python)", "Spesifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 19 (penyusunan spesifikasi teknis; penyebutan merek)"),
    RuleSpec("PROC-TIMELINE-COMPRESSED", "PROC-TIMELINE", "Jadwal penawaran/masa sanggah dipersingkat", "Jadwal", "tender_document",
             legal_reference="Peraturan LKPP 4/2024 (jadwal pemilihan dan masa sanggah)",
             aliases=("PROC-TIMELINE-PREP", "PROC-TIMELINE-SANGGAH", "PROC-TIMELINE-EXPEDITED")),
    RuleSpec("PROC-AI-TIMELINE", "PROC-TIMELINE", "Jadwal dipersingkat (diekstrak AI, divalidasi Python)", "Jadwal", "tender_document",
             legal_reference="Peraturan LKPP 4/2024 (jadwal pemilihan dan masa sanggah)"),
    RuleSpec("PROC-UNREALISTIC-TIMELINE", "PROC-UNREALISTIC", "Durasi implementasi tidak realistis", "Jadwal", "tender_document",
             critical_on_gap=True,
             legal_reference=f"{_PERPRES}, Pasal 6 (prinsip bersaing dan adil); UU 5/1999 Pasal 22 hanya bila unsur terpenuhi"),
    RuleSpec("GOV-CONFLICT-INTEREST", "GOV-COI", "Benturan kepentingan / afiliasi pejabat", "Integritas", "tender_document",
             critical_on_gap=True,
             legal_reference=f"{_PERPRES}, Pasal 7 (etika pengadaan dan larangan benturan kepentingan)"),
    RuleSpec("SPEC-REGIONAL-LOCKIN", "SPEC-REGIONAL", "Persyaratan domisili/asosiasi regional diskriminatif", "Kualifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 6 (prinsip terbuka, bersaing, tidak diskriminatif)",
             aliases=("DISC-GEO-BRANCH", "DISC-GEO-DOMICILE")),
    RuleSpec("SPEC-INCUMBENT-LOCKIN", "SPEC-INCUMBENT", "Kriteria pengalaman mengarah ke inkumben", "Kualifikasi", "tender_document",
             legal_reference=f"{_PERPRES}, Pasal 6 (prinsip bersaing) dan Pasal 19"),
    RuleSpec("FIN-OVER-BUDGET", "FIN-OVER-BUDGET", "Total BoQ/HPS melebihi pagu anggaran", "Keuangan", "tender_document",
             critical_on_gap=True,
             legal_reference=f"{_PERPRES}, ketentuan penetapan HPS terhadap pagu anggaran",
             aliases=("FIN-HPS-OVER-PAGU",)),
    RuleSpec("FIN-MARKUP-RATE", "FIN-BILLING-RATE", "Billing rate tenaga ahli di atas pedoman", "Keuangan", "tender_document",
             legal_reference="Pedoman standar remunerasi konsultan (INKINDO) dan prinsip kewajaran harga",
             aliases=("FIN-BILLING-RATE",)),
    RuleSpec("FIN-DOUBLE-LICENSE", "FIN-DOUBLE-COUNT", "Duplikasi pembiayaan lisensi & pemeliharaan", "Keuangan", "tender_document",
             legal_reference="Prinsip efisiensi dan kewajaran harga pada penyusunan HPS"),
)

CATALOG: dict[str, RuleSpec] = {rule.code: rule for rule in _RULES}
_ALIASES: dict[str, str] = {alias: rule.code for rule in _RULES for alias in rule.aliases}


def get_rule(code: str) -> RuleSpec:
    """Return the rule for a finding code; numbered addendum rows share ADD-CHANGE."""
    canonical = canonical_code(code)
    if canonical in CATALOG:
        return CATALOG[canonical]
    raise KeyError(f"Finding code {code!r} is not registered in the rule catalog.")


def canonical_code(code: str) -> str:
    code = str(code or "").strip().upper()
    if code.startswith("ADD-") and code[4:].isdigit():
        return "ADD-CHANGE"
    return _ALIASES.get(code, code)


def family_of(code: str) -> str:
    """Canonical concept for benchmarking; unknown codes keep their own name."""
    canonical = canonical_code(code)
    rule = CATALOG.get(canonical)
    return rule.family if rule else canonical


def all_rules() -> list[RuleSpec]:
    return list(_RULES)


__all__ = ["CATALOG", "RuleSpec", "all_rules", "canonical_code", "family_of", "get_rule"]
