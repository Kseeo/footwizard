"""GNN 하중 변형 예측 -- hplAI 저장소의 glb_preprocess/api_server.py(상시 실행,
모델을 메모리에 캐시해둔 GNN API 서버)에 HTTP로 요청한다.

예전엔 매 요청마다 build_dataset.py -> predict.py -> export_glb.py를 별도
subprocess 3개로 띄웠는데, predict.py 쪽만 torch/PyTorch Geometric/wandb
import에 매번 ~10초가 들어서(실제 추론 자체는 ~0.1-0.3초) 전체가 느렸다.
api_server.py는 모델을 프로세스 안에 캐시해두고 계속 떠 있어서, 그 ~10초를
서버 시작 시점(또는 그 모델의 첫 요청)에 딱 한 번만 낸다 -- 그래서 여기서도
subprocess 대신 그 서버를 호출하는 쪽으로 바꿨다. GNN_API_URL 환경변수로
주소를 바꿀 수 있다 (기본 http://127.0.0.1:5052, 이 머신 기준).

torch 자체는 이제 이 프로세스(footwizard, foot_modeling conda env)에 전혀
안 들어온다 -- requests로 호출만 한다."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import requests
import trimesh

GNN_API_URL = os.environ.get("GNN_API_URL", "http://127.0.0.1:5052")

SMOOTH_DEFAULTS = {"lamb": 0.5, "iterations": 10, "floor_percentile": 0.5}


class GnnPredictError(RuntimeError):
    def __init__(self, message: str, log: str = ""):
        super().__init__(message)
        self.log = log


def list_checkpoints() -> list[dict]:
    """모델 선택 드롭다운용 -- api_server.py의 MODEL_REGISTRY를 그대로 가져온다
    (checkpoints_local/*.pt를 직접 스캔하던 예전 방식 대신, api_server.py가
    실제로 서빙하는 모델과 항상 일치하도록 그쪽을 단일 출처로 삼는다)."""
    try:
        r = requests.get(f"{GNN_API_URL}/health", timeout=10)
        r.raise_for_status()
        models = r.json().get("models", [])
    except requests.RequestException as e:
        raise GnnPredictError(f"GNN 서버({GNN_API_URL})에 연결할 수 없습니다: {e}")
    return [
        {"id": m["key"], "label": m["label"] + ("" if m.get("found") else " (checkpoint 없음)")}
        for m in models
    ]


def _write_progress(progress_path: Path | None, step: str, message: str) -> None:
    """진행상황을 job 폴더에 JSON 한 파일로 남긴다 -- 프론트엔드가 메인 요청이
    끝나길 기다리는 동안 별도로 폴링해서 "지금 어느 단계인지" 보여줄 수 있게.
    원자적으로 쓰기 위해 임시파일에 쓰고 rename(같은 파일시스템에서 원자적)."""
    if progress_path is None:
        return
    tmp = progress_path.with_suffix(progress_path.suffix + ".tmp")
    tmp.write_text(json.dumps({"step": step, "message": message}), encoding="utf-8")
    tmp.replace(progress_path)


def predict(
    input_glb: Path,
    out_dir: Path,
    checkpoint: str,
    target_faces: int | None = None,
    smooth: bool = True,
    lamb: float | None = None,
    iterations: int | None = None,
    floor_percentile: float | None = None,
    progress_path: Path | None = None,
) -> dict:
    """input_glb를 예측해 out_dir에 5_gnn_predicted.glb(및 smooth=True면
    5_gnn_smoothed.glb)를 쓴다. checkpoint는 list_checkpoints()가 돌려준 id
    (api_server.py MODEL_REGISTRY 키, 예: "graphormer_roll2")."""
    _write_progress(progress_path, "uploading", "GNN 서버로 전송하는 중...")

    lamb = SMOOTH_DEFAULTS["lamb"] if lamb is None else lamb
    iterations = SMOOTH_DEFAULTS["iterations"] if iterations is None else iterations
    floor_percentile = SMOOTH_DEFAULTS["floor_percentile"] if floor_percentile is None else floor_percentile

    data = {
        "model": checkpoint,
        "smooth": "true" if smooth else "false",
        "lamb": lamb, "iterations": iterations, "floor_percentile": floor_percentile,
        "format": "json",
    }
    if target_faces is not None:
        data["target_faces"] = target_faces

    _write_progress(progress_path, "predict", "GNN 서버에서 예측하는 중...")
    try:
        with open(input_glb, "rb") as f:
            r = requests.post(
                f"{GNN_API_URL}/predict", files={"file": (input_glb.name, f)}, data=data, timeout=300,
            )
    except requests.RequestException as e:
        raise GnnPredictError(f"GNN 서버({GNN_API_URL})에 연결할 수 없습니다: {e}")

    try:
        payload = r.json()
    except ValueError:
        raise GnnPredictError(f"GNN 서버 응답을 해석할 수 없습니다 (HTTP {r.status_code})", r.text[:4000])
    if not r.ok:
        raise GnnPredictError(payload.get("error", f"HTTP {r.status_code}"), payload.get("log", ""))

    _write_progress(progress_path, "saving", "결과를 저장하는 중...")
    out_dir.mkdir(parents=True, exist_ok=True)

    predicted_name = "5_gnn_predicted.glb"
    predicted_bytes = base64.b64decode(payload["predicted"])
    (out_dir / predicted_name).write_bytes(predicted_bytes)
    predicted_mesh = trimesh.load(out_dir / predicted_name, force="mesh", process=False)

    result = {
        "checkpoint": checkpoint,
        "predicted_file": predicted_name,
        "predicted_n_vertices": len(predicted_mesh.vertices),
        "predicted_n_faces": len(predicted_mesh.faces),
        "smoothed_file": None,
        "smoothed_n_vertices": None,
        "smoothed_n_faces": None,
        "smooth_error": payload.get("smooth_error"),
        "log": payload.get("log", ""),
    }

    if payload.get("smoothed"):
        smoothed_name = "5_gnn_smoothed.glb"
        (out_dir / smoothed_name).write_bytes(base64.b64decode(payload["smoothed"]))
        smoothed_mesh = trimesh.load(out_dir / smoothed_name, force="mesh", process=False)
        result["smoothed_file"] = smoothed_name
        result["smoothed_n_vertices"] = len(smoothed_mesh.vertices)
        result["smoothed_n_faces"] = len(smoothed_mesh.faces)

    _write_progress(progress_path, "done", "완료")
    return result
