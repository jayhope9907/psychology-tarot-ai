"""Now You See Me — 11-Prop Stealth Unconscious Mapping Engine (v5.1).

게임형 마술 소품(11종) 상호작용에서 나오는 행동/생체 프록시 신호를
CHC 지능 프로파일 + 임상 스펙트럼 참고 지표로 환산하고, 4인의 호스멘
페르소나 중 하나로 요약한다.

TS 계약(동일 계수/동일 결과): ``static/types/CompleteStealthUnconsciousEngine.ts``

주의: 모든 산출물은 비진단 웰니스 참고 지표(non_diagnostic)이며 의료 진단을
대체하지 않는다.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

PROP_TYPES: List[str] = [
    "RAIN_DROP",  # 1. 물방울 (주파수 동기화)
    "WATER_TANK",  # 2. 수조 (수쇄 탈출 QTE)
    "CARD_STEALTH",  # 3. 카드 (레이저 스텔스 패스)
    "CHAMBER_BOX",  # 4. 상자 (차원 반전)
    "MIRROR_SHADOW",  # 5. 미러 (가짜 잔상 관조)
    "ROULETTE_DIAL",  # 6. 루렛 (시선 유도 미스디렉션)
    "PERSONA_MASK",  # 7. 페르소나 마스크 (변장 및 미세표정)
    "SLEIGHT_PALMING",  # 8. 손놀림 (미세 제스처/터치 압력)
    "MENTAL_PRIMING",  # 9. 멘탈리즘 (암시 수용성/무의식 프라이밍)
    "HOLOGRAM_REALITY",  # 10. 홀로그램 (지각적 현실 검증력)
    "INTERPERSONAL_SYNC",  # 11. 인터랙션 동기화 (대인 인지 동기화)
]

HORSEMEN_PERSONAS: List[str] = [
    "DANIEL_ATLAS",
    "MERRITT_MCKINNEY",
    "JACK_WILDER",
    "HENLEY_REEVES",
]

# 고유 프롭 N개 이상이어야 각성(페르소나)을 final로 확정. 미만은 provisional.
FINAL_MIN_PROPS = 8

PROP_CATALOG: List[Dict[str, Any]] = [
    {
        "prop": "RAIN_DROP",
        "order": 1,
        "label_ko": "물방울 (주파수 동기화)",
        "movie_cue": "빗방울 사이를 멈춰 세우는 스트로보 타이밍",
        "payload_fields": ["strobePrecisionDeltaPx", "tremorVector"],
        "targets": ["ocdRigidityScore", "panicAnxietyIndex", "Gv"],
    },
    {
        "prop": "WATER_TANK",
        "order": 2,
        "label_ko": "수조 (수쇄 탈출 QTE)",
        "movie_cue": "쇠사슬 수조 탈출 — 압박 하 작업기억",
        "payload_fields": ["qteLatencyMs", "panicStimmingCount"],
        "targets": ["panicAnxietyIndex", "asdStimmingRate", "Gwm"],
    },
    {
        "prop": "CARD_STEALTH",
        "order": 3,
        "label_ko": "카드 (레이저 스텔스 패스)",
        "movie_cue": "레이저 격자 사이로 카드를 흘려 보내기",
        "payload_fields": ["stealthPassLatencyMs", "trajectoryAccuracyRatio"],
        "targets": ["Gs", "Gv"],
    },
    {
        "prop": "CHAMBER_BOX",
        "order": 4,
        "label_ko": "상자 (차원 반전)",
        "movie_cue": "상자 내부의 차원이 뒤집히는 재구성 퍼즐",
        "payload_fields": ["rigidPatternRepeatCount", "dimensionReconstructTimeSec"],
        "targets": ["cognitiveFlexibility", "Gc"],
    },
    {
        "prop": "MIRROR_SHADOW",
        "order": 5,
        "label_ko": "미러 (가짜 잔상 관조)",
        "movie_cue": "거울 속 잔상을 쫓지 않고 바라보기",
        "payload_fields": ["illusionChasingClicks", "idleAcceptanceDurationMs"],
        "targets": ["dissociationScore", "personaIdentityFluidity"],
    },
    {
        "prop": "ROULETTE_DIAL",
        "order": 6,
        "label_ko": "루렛 (시선 유도 미스디렉션)",
        "movie_cue": "미스디렉션 미끼를 참아내는 시선 통제",
        "payload_fields": ["misdirectionBaitClicks", "entropyRandomnessIndex"],
        "targets": ["impulsivityMisdirection", "Gc"],
    },
    {
        "prop": "PERSONA_MASK",
        "order": 7,
        "label_ko": "페르소나 마스크 (변장/미세표정)",
        "movie_cue": "군중 속 미세표정을 읽어 마스크를 맞추기",
        "payload_fields": ["microExpressionScanLatencyMs", "maskMatchAccuracyRatio"],
        "targets": ["empathyTheoryOfMind", "Gc"],
    },
    {
        "prop": "SLEIGHT_PALMING",
        "order": 8,
        "label_ko": "손놀림 (미세 제스처/터치 압력)",
        "movie_cue": "손안에서 사라지는 팜링 궤적",
        "payload_fields": ["gestureCurvatureVariance", "touchPressureInstability"],
        "targets": ["fineMotorControlIndex", "Gs"],
    },
    {
        "prop": "MENTAL_PRIMING",
        "order": 9,
        "label_ko": "멘탈리즘 (암시 수용성/프라이밍)",
        "movie_cue": "무대 암시가 선택을 앞질러 심어지는 순간",
        "payload_fields": ["primingBiasAcceptanceRatio", "decisionHesitationMs"],
        "targets": ["hypnoticSuggestibility", "Gc"],
    },
    {
        "prop": "HOLOGRAM_REALITY",
        "order": 10,
        "label_ko": "홀로그램 (지각적 현실 검증력)",
        "movie_cue": "홀로그램 무대에서 실체와 허상을 가르기",
        "payload_fields": [
            "distortionIllusionChasingClicks",
            "perceptualRealityTestingScore",
        ],
        "targets": ["perceptualDefusionIndex", "Gv"],
    },
    {
        "prop": "INTERPERSONAL_SYNC",
        "order": 11,
        "label_ko": "인터랙션 동기화 (대인 인지 동기화)",
        "movie_cue": "네 명의 호스멘이 한 박자로 움직이는 합",
        "payload_fields": ["interpersonalSyncDeltaMs", "socialAdaptabilityRatio"],
        "targets": ["interpersonalSynchrony", "Gwm"],
    },
]


def _num(payload: Mapping[str, Any], key: str, default: float) -> float:
    value = payload.get(key)
    if value is None:
        return float(default)
    try:
        out = float(value)
    except (TypeError, ValueError):
        return float(default)
    if math.isnan(out) or math.isinf(out):
        return float(default)
    return out


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def normalize_prop(prop: Any) -> Optional[str]:
    """Accept ``rain_drop`` / ``RAIN-DROP`` / ``RAIN_DROP`` shapes."""
    if not prop:
        return None
    token = str(prop).strip().upper().replace("-", "_").replace(" ", "_")
    return token if token in PROP_TYPES else None


class Master11PropEvaluator:
    """소품별 원시 payload → 지표 환산기 (TS Master11PropEvaluator 동일 계수)."""

    def evaluate_rain_drop(self, p: Mapping[str, Any]) -> Dict[str, float]:
        delta = _num(p, "strobePrecisionDeltaPx", 10.0)
        tremor = p.get("tremorVector") or {}
        if not isinstance(tremor, Mapping):
            tremor = {}
        tx = _num(tremor, "x", 0.0)
        ty = _num(tremor, "y", 0.0)
        tz = _num(tremor, "z", 0.0)
        euclidean_tremor = math.sqrt(tx**2 + ty**2 + tz**2)
        return {
            "ocdRigidity": _clamp(100.0 - delta * 8.5),
            "panicAnxiety": _clamp(euclidean_tremor * 18.2),
            "gvContribution": _clamp(100.0 - delta * 4.2),
        }

    def evaluate_water_tank(self, p: Mapping[str, Any]) -> Dict[str, float]:
        qte_latency = _num(p, "qteLatencyMs", 1200.0)
        stimming = _num(p, "panicStimmingCount", 0.0)
        gwm_score = 100.0 * math.exp(-0.0018 * max(0.0, qte_latency - 150.0))
        return {
            "panicIndex": _clamp(stimming * 9.5),
            "stimmingRate": max(0.0, stimming),
            "gwmContribution": _clamp(gwm_score),
        }

    def evaluate_card_stealth(self, p: Mapping[str, Any]) -> Dict[str, float]:
        latency = _num(p, "stealthPassLatencyMs", 900.0)
        accuracy = _num(p, "trajectoryAccuracyRatio", 0.5)
        gs_score = 100.0 * math.exp(-0.0022 * max(0.0, latency - 120.0))
        return {
            "gsContribution": _clamp(gs_score),
            "gvContribution": _clamp(accuracy * 100.0),
        }

    def evaluate_chamber_box(self, p: Mapping[str, Any]) -> Dict[str, float]:
        repeats = _num(p, "rigidPatternRepeatCount", 0.0)
        sec = _num(p, "dimensionReconstructTimeSec", 40.0)
        return {
            "cognitiveFlexibility": _clamp(100.0 - (repeats * 14.5 + sec * 1.8)),
            "gcContribution": _clamp(95.0 - repeats * 9.0),
        }

    def evaluate_mirror_shadow(self, p: Mapping[str, Any]) -> Dict[str, float]:
        chasing_clicks = _num(p, "illusionChasingClicks", 0.0)
        idle_time = _num(p, "idleAcceptanceDurationMs", 0.0)
        return {
            "dissociationScore": _clamp(chasing_clicks * 16.5),
            "realityTestingScore": _clamp((idle_time / 3000.0) * 100.0),
        }

    def evaluate_roulette_dial(self, p: Mapping[str, Any]) -> Dict[str, float]:
        bait_clicks = _num(p, "misdirectionBaitClicks", 0.0)
        entropy = _num(p, "entropyRandomnessIndex", 0.5)
        return {
            "impulsivityIndex": _clamp(bait_clicks * 22.0 + (1.0 - entropy) * 30.0),
            "gcContribution": _clamp(entropy * 100.0),
        }

    def evaluate_persona_mask(self, p: Mapping[str, Any]) -> Dict[str, float]:
        scan_latency = _num(p, "microExpressionScanLatencyMs", 1000.0)
        accuracy = _num(p, "maskMatchAccuracyRatio", 0.5)
        empathy = accuracy * 100.0 * math.exp(-0.001 * max(0.0, scan_latency - 200.0))
        return {
            "empathyTheoryOfMind": _clamp(empathy),
            "gcContribution": _clamp(empathy),
        }

    def evaluate_sleight_palming(self, p: Mapping[str, Any]) -> Dict[str, float]:
        curvature = _num(p, "gestureCurvatureVariance", 0.5)
        pressure_instability = _num(p, "touchPressureInstability", 0.4)
        fine_motor = max(0.0, 100.0 - (curvature * 40.0 + pressure_instability * 50.0))
        return {
            "fineMotorControlIndex": _clamp(fine_motor),
            "gsContribution": _clamp(fine_motor),
        }

    def evaluate_mental_priming(self, p: Mapping[str, Any]) -> Dict[str, float]:
        suggestibility = _num(p, "primingBiasAcceptanceRatio", 0.5)
        hesitation = _num(p, "decisionHesitationMs", 1000.0)
        return {
            "hypnoticSuggestibility": _clamp(suggestibility * 100.0),
            "gcContribution": _clamp(
                100.0 * math.exp(-0.001 * max(0.0, hesitation - 300.0))
            ),
        }

    def evaluate_hologram_reality(self, p: Mapping[str, Any]) -> Dict[str, float]:
        chasing_clicks = _num(p, "distortionIllusionChasingClicks", 0.0)
        base_testing_score = _num(p, "perceptualRealityTestingScore", 50.0)
        reality_testing = max(0.0, base_testing_score - chasing_clicks * 12.0)
        return {
            "perceptualDefusionIndex": _clamp(reality_testing),
            "gvContribution": _clamp(reality_testing),
        }

    def evaluate_interpersonal_sync(self, p: Mapping[str, Any]) -> Dict[str, float]:
        delta_ms = _num(p, "interpersonalSyncDeltaMs", 500.0)
        adaptability = _num(p, "socialAdaptabilityRatio", 0.5)
        synchro = adaptability * 100.0 * math.exp(-0.002 * max(0.0, delta_ms - 50.0))
        return {
            "interpersonalSynchrony": _clamp(synchro),
            "gwmContribution": _clamp(synchro),
        }


def default_chc_profile() -> Dict[str, float]:
    return {"Gv": 50.0, "Gs": 50.0, "Gwm": 50.0, "Gc": 50.0}


def default_clinical_profile() -> Dict[str, float]:
    return {
        "ocdRigidityScore": 0.0,
        "panicAnxietyIndex": 0.0,
        "asdStimmingRate": 0.0,
        "dissociationScore": 0.0,
        "cognitiveFlexibility": 50.0,
        "impulsivityMisdirection": 0.0,
        "empathyTheoryOfMind": 50.0,
        "personaIdentityFluidity": 50.0,
        "fineMotorControlIndex": 50.0,
        "hypnoticSuggestibility": 50.0,
        "perceptualDefusionIndex": 50.0,
        "interpersonalSynchrony": 50.0,
    }


class FullUnconsciousEngine:
    """11-프롭 스텔스 무의식 매핑 오케스트레이터."""

    def __init__(
        self,
        *,
        chc: Optional[Mapping[str, Any]] = None,
        clinical: Optional[Mapping[str, Any]] = None,
        ingested_props: Optional[Iterable[str]] = None,
    ) -> None:
        self.evaluator = Master11PropEvaluator()
        self.chc: Dict[str, float] = default_chc_profile()
        self.clinical: Dict[str, float] = default_clinical_profile()
        if chc:
            for key in self.chc:
                if key in chc:
                    self.chc[key] = _clamp(_num(chc, key, self.chc[key]))
        if clinical:
            for key in self.clinical:
                if key in clinical:
                    self.clinical[key] = _num(clinical, key, self.clinical[key])
        self.ingested_props: Set[str] = set()
        for prop in ingested_props or []:
            token = normalize_prop(prop)
            if token:
                self.ingested_props.add(token)
        self.ingest_count = 0

    def _blend_chc(self, key: str, value: float) -> None:
        self.chc[key] = _clamp((self.chc[key] + float(value)) / 2.0)

    def ingest_biomarker(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """단일 프롭 raw payload를 집계에 반영. 알 수 없는 프롭은 무시."""
        prop = normalize_prop((payload or {}).get("prop"))
        if not prop:
            return {"ok": False, "reason": "unknown_prop", "prop": (payload or {}).get("prop")}

        p = dict(payload or {})
        self.ingested_props.add(prop)
        self.ingest_count += 1
        cli = self.clinical

        if prop == "RAIN_DROP":
            res = self.evaluator.evaluate_rain_drop(p)
            cli["ocdRigidityScore"] = res["ocdRigidity"]
            cli["panicAnxietyIndex"] = (cli["panicAnxietyIndex"] + res["panicAnxiety"]) / 2.0
            self._blend_chc("Gv", res["gvContribution"])
        elif prop == "WATER_TANK":
            res = self.evaluator.evaluate_water_tank(p)
            cli["panicAnxietyIndex"] = (cli["panicAnxietyIndex"] + res["panicIndex"]) / 2.0
            cli["asdStimmingRate"] = res["stimmingRate"]
            self._blend_chc("Gwm", res["gwmContribution"])
        elif prop == "CARD_STEALTH":
            res = self.evaluator.evaluate_card_stealth(p)
            self._blend_chc("Gs", res["gsContribution"])
            self._blend_chc("Gv", res["gvContribution"])
        elif prop == "CHAMBER_BOX":
            res = self.evaluator.evaluate_chamber_box(p)
            cli["cognitiveFlexibility"] = res["cognitiveFlexibility"]
            self._blend_chc("Gc", res["gcContribution"])
        elif prop == "MIRROR_SHADOW":
            res = self.evaluator.evaluate_mirror_shadow(p)
            cli["dissociationScore"] = res["dissociationScore"]
            # 잔상을 쫓지 않고 관조한 시간 → 페르소나 관찰 유연성
            cli["personaIdentityFluidity"] = (
                cli["personaIdentityFluidity"] + res["realityTestingScore"]
            ) / 2.0
        elif prop == "ROULETTE_DIAL":
            res = self.evaluator.evaluate_roulette_dial(p)
            cli["impulsivityMisdirection"] = res["impulsivityIndex"]
            self._blend_chc("Gc", res["gcContribution"])
        elif prop == "PERSONA_MASK":
            res = self.evaluator.evaluate_persona_mask(p)
            cli["empathyTheoryOfMind"] = res["empathyTheoryOfMind"]
            self._blend_chc("Gc", res["gcContribution"])
        elif prop == "SLEIGHT_PALMING":
            res = self.evaluator.evaluate_sleight_palming(p)
            cli["fineMotorControlIndex"] = res["fineMotorControlIndex"]
            self._blend_chc("Gs", res["gsContribution"])
        elif prop == "MENTAL_PRIMING":
            res = self.evaluator.evaluate_mental_priming(p)
            cli["hypnoticSuggestibility"] = res["hypnoticSuggestibility"]
            self._blend_chc("Gc", res["gcContribution"])
        elif prop == "HOLOGRAM_REALITY":
            res = self.evaluator.evaluate_hologram_reality(p)
            cli["perceptualDefusionIndex"] = res["perceptualDefusionIndex"]
            self._blend_chc("Gv", res["gvContribution"])
        else:  # INTERPERSONAL_SYNC
            res = self.evaluator.evaluate_interpersonal_sync(p)
            cli["interpersonalSynchrony"] = res["interpersonalSynchrony"]
            self._blend_chc("Gwm", res["gwmContribution"])

        return {"ok": True, "prop": prop, "evaluated": res}

    def ingest_many(self, payloads: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        accepted: List[str] = []
        rejected: List[Any] = []
        for payload in payloads or []:
            outcome = self.ingest_biomarker(payload)
            if outcome.get("ok"):
                accepted.append(str(outcome.get("prop")))
            else:
                rejected.append(outcome.get("prop"))
        return {"accepted": accepted, "rejected": rejected}

    def get_progress(self) -> Dict[str, Any]:
        ingested = [p for p in PROP_TYPES if p in self.ingested_props]
        remaining = [p for p in PROP_TYPES if p not in self.ingested_props]
        unique = len(ingested)
        is_final = unique >= FINAL_MIN_PROPS
        return {
            "ingested": ingested,
            "remaining": remaining,
            "ingestCount": self.ingest_count,
            "uniquePropCount": unique,
            "requiredForFinal": FINAL_MIN_PROPS,
            "completionRatio": round(unique / len(PROP_TYPES), 4),
            "assessmentStatus": "final" if is_final else "provisional",
            "awakeningLocked": not is_final,
        }

    def snapshot(self) -> Dict[str, Any]:
        """재개(resume) 가능한 집계 상태."""
        return {
            "chcProfile": {k: round(v, 4) for k, v in self.chc.items()},
            "clinicalProfile": {k: round(v, 4) for k, v in self.clinical.items()},
            "ingestedProps": [p for p in PROP_TYPES if p in self.ingested_props],
        }

    def finalize_persona_assessment(self) -> Dict[str, Any]:
        gv = self.chc["Gv"]
        gs = self.chc["Gs"]
        gwm = self.chc["Gwm"]
        gc = self.chc["Gc"]
        cli = self.clinical
        progress = self.get_progress()
        is_final = not progress.get("awakeningLocked", True)

        persona = "DANIEL_ATLAS"
        title = "환영의 통제자 (Illusion Architect)"
        quote = "가장 완벽한 환상은 통제되고 있다는 감각 그 자체입니다."

        if cli["perceptualDefusionIndex"] > 75 and gv > 80:
            persona = "DANIEL_ATLAS"
            title = "현실 검증의 설계자 (Master Reality-Architect)"
            quote = "외부의 인지적 자극과 정보 왜곡 속에서도 명확한 실체를 꿰뚫어 보는 자입니다."
        elif cli["interpersonalSynchrony"] > 75 and cli["empathyTheoryOfMind"] > 70:
            persona = "MERRITT_MCKINNEY"
            title = "공감과 동기화의 멘탈리스트 (Synchro Mentalist)"
            quote = "상대의 언어와 찰나의 타이밍을 완벽하게 읽어내어 대인적 동기화를 이룹니다."
        elif cli["fineMotorControlIndex"] > 80 and gs > 75:
            persona = "JACK_WILDER"
            title = "초감각 손놀림 마술사 (Sleight Master)"
            quote = "Always be the fastest in the room. 당신의 속도는 의식을 능가합니다."
        else:
            persona = "HENLEY_REEVES"
            title = "탈출의 아티스트 (Escape Artist)"
            quote = "가장 깊은 압박 속에서도 스스로 빠져나올 열쇠를 찾아냅니다."

        if not is_final:
            remaining = int(progress.get("requiredForFinal") or FINAL_MIN_PROPS) - int(
                progress.get("uniquePropCount") or 0
            )
            title = f"이어가는 중 · {title}"
            quote = (
                f"부담 없이 {max(0, remaining)}장만 더 만져 보시면 그림이 더 또렷해져요. "
                f"지금 결의 이름은 {persona} 쪽에 가깝게 보여요. " + quote
            )

        clinical_ide_output = _render_clinical_ide(
            persona, title, self.chc, cli, progress=progress
        )

        result: Dict[str, Any] = {
            "persona": persona,
            "title": title,
            "awakeningQuote": quote,
            "assessmentStatus": progress.get("assessmentStatus"),
            "awakeningLocked": bool(progress.get("awakeningLocked")),
            "stats": {
                "spatialControl": round(gv),
                "sleightSpeed": round(gs),
                "escapeResilience": round(gwm),
                "mindReading": round(gc),
                "personaDisguise": round(
                    (cli["empathyTheoryOfMind"] + cli["personaIdentityFluidity"]) / 2.0
                ),
                "mentalSuggestibility": round(cli["hypnoticSuggestibility"]),
                "perceptualRealityTesting": round(cli["perceptualDefusionIndex"]),
                "interpersonalSynergy": round(cli["interpersonalSynchrony"]),
            },
            "chcProfile": {
                "Gv": round(gv),
                "Gs": round(gs),
                "Gwm": round(gwm),
                "Gc": round(gc),
            },
            "clinicalProfile": {k: round(v, 2) for k, v in cli.items()},
            "clinicalIDEOutput": clinical_ide_output,
            "progress": progress,
            "non_diagnostic": True,
        }
        return result


def _flag(value: float, threshold: float, high: str, low: str) -> str:
    return high if value > threshold else low


def _render_clinical_ide(
    persona: str,
    title: str,
    chc: Mapping[str, float],
    cli: Mapping[str, float],
    progress: Optional[Mapping[str, Any]] = None,
) -> str:
    gv = float(chc["Gv"])
    gs = float(chc["Gs"])
    gwm = float(chc["Gwm"])
    gc = float(chc["Gc"])
    prog = dict(progress or {})
    status = str(prog.get("assessmentStatus") or "provisional").upper()
    unique = int(prog.get("uniquePropCount") or 0)
    needed = int(prog.get("requiredForFinal") or FINAL_MIN_PROPS)
    return f"""
[CLINICAL IDE :: STEALTH PARSING REPORT]
------------------------------------------------------------------
TIMESTAMP           : {datetime.now(timezone.utc).isoformat()}
SESSION TARGET      : USER_UNCONSCIOUS_VECTOR
ASSESSMENT STATUS   : {status} ({unique}/{needed} props for final awakening)
ASSIGNED PERSONA    : {persona} ({title})
------------------------------------------------------------------
[CHC INTELLIGENCE PROFILE]
- Gv (Spatial Processing)         : {gv:.2f} / 100
- Gs (Processing Speed)           : {gs:.2f} / 100
- Gwm (Working Memory)            : {gwm:.2f} / 100
- Gc (Crystallized / Social)      : {gc:.2f} / 100

[DSM / CLINICAL SPECTRUM METRICS]
- OCD Rigidity Index              : {cli['ocdRigidityScore']:.2f} [{_flag(cli['ocdRigidityScore'], 60, 'HIGH', 'NORMAL')}]
- Somatic Panic / Tremor          : {cli['panicAnxietyIndex']:.2f} [{_flag(cli['panicAnxietyIndex'], 50, 'ELEVATED', 'STABLE')}]
- ASD Motor Stimming Rate         : {cli['asdStimmingRate']:.0f} CPM
- Dissociation / Reality Score    : {100.0 - float(cli['dissociationScore']):.2f}% [REALITY_TESTING]
- Misdirection Impulsivity        : {cli['impulsivityMisdirection']:.2f} [{_flag(cli['impulsivityMisdirection'], 55, 'HIGH_SUSCEPTIBILITY', 'STABLE')}]
- Fine Motor Precision            : {cli['fineMotorControlIndex']:.2f} [SLEIGHT_CONTROL]
- Hypnotic Suggestibility         : {cli['hypnoticSuggestibility']:.2f} [PRIMING_BIAS]
- Perceptual Reality Testing      : {cli['perceptualDefusionIndex']:.2f} [{_flag(cli['perceptualDefusionIndex'], 70, 'HIGH_REALITY_TESTING', 'SUSCEPTIBLE')}]
- Interpersonal Synchrony Rate    : {cli['interpersonalSynchrony']:.2f} [COGNITIVE_SYNCHRONY]
------------------------------------------------------------------
[DISCLAIMER] non-diagnostic wellness proxy — 의료 진단 대체 아님.
------------------------------------------------------------------"""


def evaluate_biomarker_stream(
    payloads: Iterable[Mapping[str, Any]],
    *,
    chc: Optional[Mapping[str, Any]] = None,
    clinical: Optional[Mapping[str, Any]] = None,
    ingested_props: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """원시 payload 스트림 → 최종 페르소나 결과 (상태 재개 지원)."""
    engine = FullUnconsciousEngine(chc=chc, clinical=clinical, ingested_props=ingested_props)
    intake = engine.ingest_many(payloads)
    result = engine.finalize_persona_assessment()
    result["intake"] = intake
    result["snapshot"] = engine.snapshot()
    return result


def to_integrated_diagnostic_model_from_persona(
    result: Optional[Mapping[str, Any]],
    *,
    session_id: str = "",
    patient_id: str = "",
) -> Dict[str, Any]:
    """11-프롭 결과 → IntegratedDiagnosticModel (MindNetwork3D `setDiagnostic()` 입력).

    CHC 0~100 지표를 표준점수(0~150) 축으로 확장하고, 해리/고착 지표를
    3D 렌더 힌트(파편화 점선, 고착 노드 밀집)로 매핑한다.
    """
    doc = dict(result or {})
    chc = dict(doc.get("chcProfile") or {})
    cli = dict(doc.get("clinicalProfile") or {})

    gv = _clamp(_num(chc, "Gv", 50.0))
    gs = _clamp(_num(chc, "Gs", 50.0))
    gwm = _clamp(_num(chc, "Gwm", 50.0))
    gc = _clamp(_num(chc, "Gc", 50.0))

    dissociation = _clamp(_num(cli, "dissociationScore", 0.0))
    defusion = _clamp(_num(cli, "perceptualDefusionIndex", 50.0))
    ocd = _clamp(_num(cli, "ocdRigidityScore", 0.0))
    stimming_rate = max(0.0, _num(cli, "asdStimmingRate", 0.0))
    flexibility = _clamp(_num(cli, "cognitiveFlexibility", 50.0))
    panic = _clamp(_num(cli, "panicAnxietyIndex", 0.0))

    def _clamp150(x: float) -> float:
        return max(0.0, min(150.0, float(x)))

    g_factor = _clamp150(((gv + gs + gwm + gc) / 4.0) * 1.5)
    schizophrenia_index = _clamp(dissociation * 0.6 + (100.0 - defusion) * 0.4)
    asd_stimming_index = _clamp(ocd * 0.5 + min(100.0, stimming_rate * 9.5) * 0.5)
    depression_index = _clamp((100.0 - flexibility) * 0.5 + panic * 0.5)
    backbone_tension = _clamp((g_factor / 150.0) * 100.0 * (1.0 - schizophrenia_index / 200.0))
    cluster_density = _clamp(asd_stimming_index * 0.7 + schizophrenia_index * 0.3)

    return {
        "sessionId": session_id or "",
        "patientId": patient_id or "",
        "cognitiveProfile": {
            "g_factor": round(g_factor, 1),
            "crystallized_gc": round(_clamp150(gc * 1.5), 1),
            "fluid_gf": round(_clamp150(((gv + gwm) / 2.0) * 1.5), 1),
            "working_memory_gwm": round(_clamp150(gwm * 1.5), 1),
            "processing_speed_gs": round(_clamp150(gs * 1.5), 1),
            "visual_processing_gv": round(_clamp150(gv * 1.5), 1),
        },
        "clinicalProfile": {
            "schizophrenia_index": round(schizophrenia_index, 1),
            "asd_stimming_index": round(asd_stimming_index, 1),
            "depression_index": round(depression_index, 1),
        },
        "threeRenderMetrics": {
            "backbone_tension": round(backbone_tension, 1),
            "cluster_density": round(cluster_density, 1),
        },
        "source": "stealth_unconscious_engine",
        "non_diagnostic": True,
    }


def get_prop_catalog() -> Dict[str, Any]:
    """11-프롭 카탈로그 (게임 UI / 임상 IDE 툴바용)."""
    return {
        "engine": "CompleteStealthUnconsciousEngine",
        "version": "5.1",
        "count": len(PROP_CATALOG),
        "props": [dict(item) for item in PROP_CATALOG],
        "personas": list(HORSEMEN_PERSONAS),
        "chc_axes": ["Gv", "Gs", "Gwm", "Gc"],
        "final_min_props": FINAL_MIN_PROPS,
        "game_route": "/stealth-props",
        "non_diagnostic": True,
    }


def verify_stealth_entitlement(
    *,
    license_key: Optional[str] = None,
    require_license: bool = False,
) -> Dict[str, Any]:
    """라이선스 게이트. 키가 없으면 B2C 개방(ok), 키가 있으면 feature 검증.

    ``require_license=True``(기관 이력 등)일 때는 키가 필수.
    """
    key = (license_key or "").strip()
    if not key:
        if require_license:
            return {"ok": False, "reason": "license_required"}
        return {"ok": True, "via": "consumer_open"}

    try:
        from app.services.association_licensing import feature_enabled
        from app.services.license_store import validate_license

        lic = validate_license(key)
        if not lic.get("valid"):
            return {"ok": False, "reason": "license_invalid"}
        ent = lic.get("entitlements") or {}
        if not (
            feature_enabled("stealth_unconscious_engine", ent)
            or feature_enabled("mind_network_3d", ent)
        ):
            return {"ok": False, "reason": "stealth_unconscious_not_entitled"}
        return {
            "ok": True,
            "via": "license",
            "org_id": lic.get("org_id"),
            "license_type": (ent.get("tier_id") or "B2B_licensed"),
            "entitlements": ent,
        }
    except Exception:
        return {"ok": False, "reason": "license_check_failed"}
