"""DSM-5 + Wechsler/CHC age-cohort pipeline for hospital anonymized data sales.

AgeGroupDataPipeline aggregates non-diagnostic IntegratedDiagnosticModel metrics
by age cohort. All exports are fully anonymized (hashed subject ids, no free text).

Canonical contract keys (must match static/types/IntegratedDiagnosticModel.ts):
  cognitiveProfile.{g_factor,crystallized_gc,fluid_gf,working_memory_gwm,
                    processing_speed_gs,visual_processing_gv}
  clinicalProfile.{schizophrenia_index,asd_stimming_index,depression_index}
  threeRenderMetrics.{backbone_tension,cluster_density}
"""
from __future__ import annotations

import hashlib
import json
import os
import statistics
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from app.db.database import get_connection, init_db
from app.services.emotional_spectrum import to_integrated_diagnostic_model

# Age cohort buckets (inclusive ranges). Documented for hospital researchers.
# pediatric 소아 0-12 | adolescent 청소년 13-17 | young_adult 청년 18-29
# middle_adult 중장년 30-59 | older_adult 노년 60+
AGE_GROUP_RANGES: Dict[str, Tuple[int, Optional[int]]] = {
    "pediatric": (0, 12),
    "adolescent": (13, 17),
    "young_adult": (18, 29),
    "middle_adult": (30, 59),
    "older_adult": (60, None),
}

AGE_GROUP_LABELS_KO: Dict[str, str] = {
    "pediatric": "소아",
    "adolescent": "청소년",
    "young_adult": "청년",
    "middle_adult": "중장년",
    "older_adult": "노년",
}

VALID_AGE_GROUPS = frozenset(AGE_GROUP_RANGES.keys())

COGNITIVE_AXES = (
    "g_factor",
    "crystallized_gc",
    "fluid_gf",
    "working_memory_gwm",
    "processing_speed_gs",
    "visual_processing_gv",
)

CLINICAL_AXES = (
    "schizophrenia_index",
    "asd_stimming_index",
    "depression_index",
)

RENDER_AXES = (
    "backbone_tension",
    "cluster_density",
)

# Risk cohort filters (non-diagnostic thresholds for research packaging)
RISK_COHORTS = frozenset(
    {
        "any",
        "schizophrenia_spectrum",
        "high_internalizing",
        "asd_stimming",
        "depression",
    }
)

EXPORT_ROW_CAP = 500
DEFAULT_EXPORT_LIMIT = 200
PIPELINE_SCHEMA_VERSION = "1.0.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_subject_id(user_id: str) -> str:
    """Stable anonymized subject ref (no raw user_id in exports)."""
    digest = hashlib.sha256(f"age-cohort:{user_id}".encode("utf-8")).hexdigest()
    return f"anon-{digest[:16]}"


def resolve_age_group(
    *,
    age_years: Optional[int] = None,
    age_group: Optional[str] = None,
) -> Optional[str]:
    """Map age_years or explicit age_group string → canonical enum key."""
    if age_group:
        key = str(age_group).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "소아": "pediatric",
            "청소년": "adolescent",
            "청년": "young_adult",
            "중장년": "middle_adult",
            "노년": "older_adult",
            "child": "pediatric",
            "teen": "adolescent",
            "adult": "young_adult",
            "senior": "older_adult",
        }
        key = aliases.get(key, key)
        return key if key in VALID_AGE_GROUPS else None

    if age_years is None:
        return None
    try:
        years = int(age_years)
    except (TypeError, ValueError):
        return None
    if years < 0:
        return None
    for key, (lo, hi) in AGE_GROUP_RANGES.items():
        if hi is None:
            if years >= lo:
                return key
        elif lo <= years <= hi:
            return key
    return None


def age_group_metadata(age_group: str) -> Dict[str, Any]:
    lo, hi = AGE_GROUP_RANGES[age_group]
    return {
        "age_group": age_group,
        "label_ko": AGE_GROUP_LABELS_KO.get(age_group, age_group),
        "age_min": lo,
        "age_max": hi,
        "age_range_label": f"{lo}+" if hi is None else f"{lo}-{hi}",
    }


def build_integrated_metrics(
    spectrum_result: Optional[Mapping[str, Any]],
    *,
    session_id: str = "",
    patient_id: str = "",
) -> Dict[str, Any]:
    """Convert spectrum tick → IntegratedDiagnosticModel + internalizing total."""
    model = to_integrated_diagnostic_model(
        spectrum_result,
        session_id=session_id,
        patient_id=patient_id,
    )
    total = float(
        (spectrum_result or {}).get("total_internalizing_score")
        or ((model.get("internalizing_core") or {}).get("total_internalizing_score") or 0.0)
    )
    nd = (spectrum_result or {}).get("neurodevelopmental_matrix") or {}
    room = (spectrum_result or {}).get("mind_room") or {}
    return {
        "total_internalizing_score": round(total, 1),
        "cognitiveProfile": dict(model.get("cognitiveProfile") or {}),
        "clinicalProfile": dict(model.get("clinicalProfile") or {}),
        "threeRenderMetrics": dict(model.get("threeRenderMetrics") or {}),
        "room_fx": {
            "color_tone": room.get("color_tone"),
            "lighting_level": room.get("lighting_level"),
            "wall_symmetry": room.get("wall_symmetry"),
            "wall_texture": ((nd.get("three_d_room_fx") or {}).get("wall_texture")),
            "sound_muffling_factor": ((nd.get("three_d_room_fx") or {}).get("sound_muffling_factor")),
        },
        "geometry_metrics": {
            "cognitive_disorganization_score": nd.get("cognitive_disorganization_score"),
            "spectrum_mapping": dict(nd.get("spectrum_mapping") or {}),
            "backbone_tension": (model.get("threeRenderMetrics") or {}).get("backbone_tension"),
            "cluster_density": (model.get("threeRenderMetrics") or {}).get("cluster_density"),
        },
        "non_diagnostic": True,
    }


def _mean_std(values: Sequence[float]) -> Dict[str, Optional[float]]:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return {"mean": None, "stddev": None, "n": 0}
    mean = statistics.fmean(nums)
    stddev = statistics.pstdev(nums) if len(nums) > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "n": len(nums),
    }


def _matches_risk_cohort(metrics: Mapping[str, Any], risk_cohort: str) -> bool:
    key = (risk_cohort or "any").strip().lower()
    if key in ("", "any"):
        return True
    clinical = metrics.get("clinicalProfile") or {}
    total = float(metrics.get("total_internalizing_score") or 0.0)
    if key == "schizophrenia_spectrum":
        return float(clinical.get("schizophrenia_index") or 0.0) >= 40.0
    if key == "high_internalizing":
        return total >= 70.0
    if key == "asd_stimming":
        return float(clinical.get("asd_stimming_index") or 0.0) >= 50.0
    if key == "depression":
        return float(clinical.get("depression_index") or 0.0) >= 50.0
    return False


def verify_research_access(
    *,
    research_token: Optional[str] = None,
    org_id: Optional[str] = None,
) -> bool:
    """License/token gate for hospital research endpoints.

    Prefer RESEARCH_EXPORT_TOKEN (falls back to PURGE_AUDIT_TOKEN).
    When no token is configured (local/tests), require a non-empty org_id.
    """
    expected = (
        (os.getenv("RESEARCH_EXPORT_TOKEN") or "").strip()
        or (os.getenv("PURGE_AUDIT_TOKEN") or "").strip()
    )
    token = (research_token or "").strip()
    if expected:
        return bool(token) and token == expected
    return bool((org_id or "").strip())


class AgeGroupDataPipeline:
    """Near-real-time age-cohort aggregates + anonymized hospital export."""

    def ensure_ready(self) -> None:
        init_db()

    def persist_tick_metrics(
        self,
        spectrum_result: Mapping[str, Any],
        *,
        session_id: str = "",
        age_group: Optional[str] = None,
        age_years: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build denormalized metrics payload stored alongside spectrum history."""
        group = resolve_age_group(age_years=age_years, age_group=age_group)
        metrics = build_integrated_metrics(spectrum_result, session_id=session_id)
        metrics["age_group"] = group
        return metrics

    def aggregate_stats(
        self,
        *,
        age_group: Optional[str] = None,
        organization_id: Optional[str] = None,
        risk_cohort: str = "any",
    ) -> Dict[str, Any]:
        """SQL-filtered scan → mean/stddev for internalizing, ASD stimming, CHC axes.

        Uses indexed age_group / organization_id filters; metrics come from
        metrics_json (denormalized at persist time) to avoid recomputing CHC.
        """
        self.ensure_ready()
        group = resolve_age_group(age_group=age_group) if age_group else None
        if age_group and not group:
            return {
                "ok": False,
                "error": "invalid_age_group",
                "valid_age_groups": sorted(VALID_AGE_GROUPS),
                "non_diagnostic": True,
            }

        risk = (risk_cohort or "any").strip().lower()
        if risk not in RISK_COHORTS:
            return {
                "ok": False,
                "error": "invalid_risk_cohort",
                "valid_risk_cohorts": sorted(RISK_COHORTS),
                "non_diagnostic": True,
            }

        rows = self._fetch_metric_rows(
            age_group=group,
            organization_id=organization_id,
            limit=5000,
        )

        by_group: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            g = row.get("age_group")
            if not g:
                continue
            if not _matches_risk_cohort(row, risk):
                continue
            by_group.setdefault(g, []).append(row)

        cohorts: List[Dict[str, Any]] = []
        target_keys = [group] if group else sorted(VALID_AGE_GROUPS)
        for key in target_keys:
            samples = by_group.get(key, [])
            cohorts.append(self._summarize_cohort(key, samples))

        return {
            "ok": True,
            "schema_version": PIPELINE_SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "filters": {
                "age_group": group,
                "organization_id": organization_id,
                "risk_cohort": risk,
            },
            "age_group_definitions": {
                k: age_group_metadata(k) for k in sorted(VALID_AGE_GROUPS)
            },
            "cohorts": cohorts,
            "non_diagnostic": True,
            "pii_policy": "fully_anonymized",
        }

    def export_package(
        self,
        *,
        age_group: Optional[str] = None,
        risk_cohort: str = "any",
        organization_id: Optional[str] = None,
        limit: int = DEFAULT_EXPORT_LIMIT,
    ) -> Dict[str, Any]:
        """Hospital anonymized JSON package (capped for Vercel serverless)."""
        self.ensure_ready()
        group = resolve_age_group(age_group=age_group) if age_group else None
        if age_group and not group:
            return {
                "ok": False,
                "error": "invalid_age_group",
                "valid_age_groups": sorted(VALID_AGE_GROUPS),
                "non_diagnostic": True,
                "pii_policy": "fully_anonymized",
            }

        risk = (risk_cohort or "any").strip().lower()
        if risk not in RISK_COHORTS:
            return {
                "ok": False,
                "error": "invalid_risk_cohort",
                "valid_risk_cohorts": sorted(RISK_COHORTS),
                "non_diagnostic": True,
                "pii_policy": "fully_anonymized",
            }

        cap = max(1, min(int(limit or DEFAULT_EXPORT_LIMIT), EXPORT_ROW_CAP))
        rows = self._fetch_metric_rows(
            age_group=group,
            organization_id=organization_id,
            limit=min(cap * 3, 2000),
        )

        samples: List[Dict[str, Any]] = []
        for row in rows:
            if group and row.get("age_group") != group:
                continue
            if not _matches_risk_cohort(row, risk):
                continue
            samples.append(self._anonymize_row(row))
            if len(samples) >= cap:
                break

        stats = self.aggregate_stats(
            age_group=group,
            organization_id=organization_id,
            risk_cohort=risk,
        )

        return {
            "ok": True,
            "schema_version": PIPELINE_SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "non_diagnostic": True,
            "pii_policy": "fully_anonymized",
            "package_type": "hospital_age_cohort_export",
            "filters": {
                "age_group": group,
                "risk_cohort": risk,
                "organization_id": organization_id,
                "limit": cap,
            },
            "cohort_metadata": age_group_metadata(group) if group else None,
            "aggregates": stats.get("cohorts") if stats.get("ok") else [],
            "sample_count": len(samples),
            "samples": samples,
            "excluded_fields": [
                "user_id",
                "patientId",
                "display_name",
                "email",
                "message",
                "messages",
                "free_text",
                "chat_content",
            ],
        }

    def _summarize_cohort(
        self, age_group: str, samples: Sequence[Mapping[str, Any]]
    ) -> Dict[str, Any]:
        internalizing = [s.get("total_internalizing_score") for s in samples]
        asd = [
            (s.get("clinicalProfile") or {}).get("asd_stimming_index") for s in samples
        ]
        cognitive: Dict[str, Any] = {}
        for axis in COGNITIVE_AXES:
            cognitive[axis] = _mean_std(
                [(s.get("cognitiveProfile") or {}).get(axis) for s in samples]
            )
        clinical: Dict[str, Any] = {}
        for axis in CLINICAL_AXES:
            clinical[axis] = _mean_std(
                [(s.get("clinicalProfile") or {}).get(axis) for s in samples]
            )
        render: Dict[str, Any] = {}
        for axis in RENDER_AXES:
            render[axis] = _mean_std(
                [(s.get("threeRenderMetrics") or {}).get(axis) for s in samples]
            )

        return {
            **age_group_metadata(age_group),
            "n": len(samples),
            "total_internalizing_score": _mean_std(internalizing),
            "total_asd_stimming_index": _mean_std(asd),
            "cognitiveProfile": cognitive,
            "clinicalProfile": clinical,
            "threeRenderMetrics": render,
            "non_diagnostic": True,
        }

    def _anonymize_row(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        uid = str(row.get("user_id") or "")
        return {
            "subject_hash": hash_subject_id(uid) if uid else "anon-unknown",
            "session_hash": hashlib.sha256(
                f"sess:{(row.get('session_id') or '')}".encode("utf-8")
            ).hexdigest()[:12],
            "age_group": row.get("age_group"),
            "recorded_at": row.get("created_at"),
            "total_internalizing_score": row.get("total_internalizing_score"),
            "cognitiveProfile": dict(row.get("cognitiveProfile") or {}),
            "clinicalProfile": dict(row.get("clinicalProfile") or {}),
            "threeRenderMetrics": dict(row.get("threeRenderMetrics") or {}),
            "geometry_metrics": dict(row.get("geometry_metrics") or {}),
            "room_fx": dict(row.get("room_fx") or {}),
            "micro_behavior": dict(row.get("micro_behavior") or {}),
            "non_diagnostic": True,
        }

    def _fetch_metric_rows(
        self,
        *,
        age_group: Optional[str] = None,
        organization_id: Optional[str] = None,
        limit: int = 2000,
    ) -> List[Dict[str, Any]]:
        lim = max(1, min(int(limit or 2000), 5000))
        clauses: List[str] = ["metrics_json IS NOT NULL", "metrics_json != ''"]
        params: List[Any] = []
        if age_group:
            clauses.append("age_group = ?")
            params.append(age_group)
        if organization_id:
            clauses.append("organization_id = ?")
            params.append(organization_id)
        where = " AND ".join(clauses)
        sql = f"""
            SELECT id, user_id, session_id, age_group, total_score,
                   metrics_json, result_json, organization_id, created_at
            FROM emotional_spectrum_history
            WHERE {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        """
        params.append(lim)

        conn = get_connection()
        try:
            try:
                rows = conn.execute(sql, tuple(params)).fetchall()
            except Exception:
                # Pre-migration DBs without age_group/metrics_json — empty cohort.
                return []
            out: List[Dict[str, Any]] = []
            for row in rows:
                parsed = self._row_to_metrics(row)
                if parsed:
                    out.append(parsed)
            return out
        finally:
            conn.close()

    def _row_to_metrics(self, row: Any) -> Optional[Dict[str, Any]]:
        try:
            metrics = json.loads(row["metrics_json"] or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            metrics = {}
        if not metrics:
            # Fallback: recompute from result_json (legacy rows)
            try:
                result = json.loads(row["result_json"] or "{}")
            except (TypeError, ValueError, json.JSONDecodeError):
                return None
            metrics = build_integrated_metrics(
                result,
                session_id=str(row["session_id"] or ""),
            )
            metrics["age_group"] = row["age_group"] if "age_group" in row.keys() else None

        behavioral = {}
        try:
            result_doc = json.loads(row["result_json"] or "{}")
            behavioral = dict(result_doc.get("behavioralMetrics") or {})
        except (TypeError, ValueError, json.JSONDecodeError):
            behavioral = {}

        micro = {
            "hesitation_index": behavioral.get("hesitation_index"),
            "backspace_count": behavioral.get("backspace_count"),
            "word_delay_ms": behavioral.get("word_delay_ms"),
            "word_card_cancel_count": behavioral.get("word_card_cancel_count"),
        }

        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "session_id": row["session_id"],
            "age_group": row["age_group"] or metrics.get("age_group"),
            "created_at": row["created_at"],
            "organization_id": row["organization_id"],
            "total_internalizing_score": float(
                metrics.get("total_internalizing_score")
                if metrics.get("total_internalizing_score") is not None
                else (row["total_score"] or 0.0)
            ),
            "cognitiveProfile": dict(metrics.get("cognitiveProfile") or {}),
            "clinicalProfile": dict(metrics.get("clinicalProfile") or {}),
            "threeRenderMetrics": dict(metrics.get("threeRenderMetrics") or {}),
            "geometry_metrics": dict(metrics.get("geometry_metrics") or {}),
            "room_fx": dict(metrics.get("room_fx") or {}),
            "micro_behavior": micro,
        }


_PIPELINE = AgeGroupDataPipeline()


def get_age_group_pipeline() -> AgeGroupDataPipeline:
    return _PIPELINE
