"""foot_engine — 3D 발 스캔(GLB) 추출/정리 파이프라인. 웹앱 마법사(`webapp/app.py`)가
이 패키지를 쓴다.

Quick start::

    from foot_engine import crop_foot_mesh, align_for_manual_cut, cut_and_finish_mesh

    cropped, _ = crop_foot_mesh("scan.glb")
    aligned = align_for_manual_cut(cropped, down_direction=[0, -1, 0])
    result = cut_and_finish_mesh(aligned, cut_y=0.3)
    result.mesh.export("scan_foot.glb")

모듈:
    pipeline.py     — 마법사가 직접 부르는 진입점(위 세 함수 + `FootPipelineResult`)
    texture_crop.py — 다중 뷰 피부분할 투표로 발 부위만 크롭
    align.py        — 발바닥 방향 탐지, 정렬, 절단, 스케일용 순수 기하 계산
    branch_cut.py   — 잘록해졌다 다시 넓어지는 지점을 찾아 배경 조각 분리
    finishing.py    — 배경 파편 정리 + 스무딩(구멍 메움/사포질/고곡률 완화)
    locate.py       — 국소 점 집합이 "발일 가능성"을 점수화하는 형상 휴리스틱
    crop.py         — 정점 부분집합을 안전하게 잘라내는 저수준 유틸
    skin_mask.py    — MediaPipe로 이미지에서 피부 마스크를 뽑는 유틸
    geometry.py     — PCA 축, 실측 길이 계산
"""

from __future__ import annotations

from .align import (
    DEFAULT_REFERENCE_LENGTH_MM,
    DEFAULT_TARGET_VERTICES,
    SoleDirectionCandidate,
    align_sole_down,
    cut_at_height,
    decimate_mesh,
    find_floor_contact_mask,
    find_sole_direction_candidates,
    prune_far_fragments,
    rest_on_floor,
    sole_direction_candidates_for_mesh,
    to_z_up,
)
from .finishing import finish_smooth_mesh, keep_largest_component, postprocess_mesh, smooth_boundary_loops
from .geometry import measured_length, pca_axes
from .pipeline import FootPipelineResult, align_for_manual_cut, crop_foot_mesh, cut_and_finish_mesh
from .skin_mask import load_skin_segmenter, skin_only_mask

__version__ = "0.3.0"

__all__ = [
    "__version__",
    # pipeline (마법사 진입점)
    "FootPipelineResult",
    "crop_foot_mesh",
    "align_for_manual_cut",
    "cut_and_finish_mesh",
    # align
    "DEFAULT_REFERENCE_LENGTH_MM",
    "DEFAULT_TARGET_VERTICES",
    "SoleDirectionCandidate",
    "align_sole_down",
    "cut_at_height",
    "decimate_mesh",
    "find_floor_contact_mask",
    "find_sole_direction_candidates",
    "prune_far_fragments",
    "rest_on_floor",
    "sole_direction_candidates_for_mesh",
    "to_z_up",
    # finishing
    "keep_largest_component",
    "finish_smooth_mesh",
    "smooth_boundary_loops",
    "postprocess_mesh",
    # geometry
    "measured_length",
    "pca_axes",
    # skin_mask
    "load_skin_segmenter",
    "skin_only_mask",
]
