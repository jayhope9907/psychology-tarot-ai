"""학회·협회 라이선스 모델."""
from __future__ import annotations

from enum import Enum


class AssociationDiscipline(str, Enum):
    """학회 유형 — 각각 다른 임상·교육 렌즈."""

    COUNSELING = "counseling_society"  # 상담학회: 사례·관계·상담 프로세스
    PSYCHOLOGY = "psychology_society"  # 심리학회: 측정·연구·심리데이터
    PSYCHIATRY = "psychiatry_society"  # 정신의학회: DSM 스크리닝·정신병리 위험(비진단)
    CLINICAL_PSYCH_TRAINEE = "clinical_psych_trainee"  # 임상심리 수련: 검사·사례·슈퍼비전
    MH_SOCIAL_WORK = "mh_social_work_trainee"  # 정신보건사회복지사 수련: 사례관리·지역사회
    INTEGRATIVE = "integrative_society"  # 통합: 3영역 혼합
    FAITH_COUNSELING = "faith_counseling_society"  # 기독교·목회상담 학회


class LicenseTier(str, Enum):
    """B2B 구독 등급."""

    CHAPTER = "chapter"  # 지부·동호회
    SOCIETY = "society"  # 학회 본회
    FEDERATION = "federation"  # 연합·대학·병원·교육원
    INSTITUTE = "institute"  # 연구·플랫폼 파트너


class OrgMemberRole(str, Enum):
    MEMBER = "member"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"
