import json
from pathlib import Path
import pickle
from typing import Tuple
import numpy as np

DEFAULT_LABELS = [
    "摆短","拉","控制","侧身拉","劈长","拧","挑","侧旋","转不转","中性","普通"
]

class LabelHelper:
    def __init__(self, data_dir: Path, model_dir: Path):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.label_map_path = self.model_dir / "label_map.json"
        self.label_map = self._load_label_map()

    def _load_label_map(self):
        if self.label_map_path.exists():
            return json.loads(self.label_map_path.read_text(encoding="utf-8"))
        label_map = {str(i): name for i, name in enumerate(DEFAULT_LABELS)}
        self.label_map_path.write_text(json.dumps(label_map, ensure_ascii=False, indent=2), encoding="utf-8")
        return label_map

    def id_to_name(self, idx: int) -> str:
        return self.label_map.get(str(idx), f"label_{idx}")

    def name_to_id(self, name: str) -> int:
        for k, v in self.label_map.items():
            if v == name:
                return int(k)
        new_id = max([int(k) for k in self.label_map.keys()] + [-1]) + 1
        self.label_map[str(new_id)] = name
        self.label_map_path.write_text(json.dumps(self.label_map, ensure_ascii=False, indent=2), encoding="utf-8")
        return new_id

    def id_to_name_list(self):
        return [{"id": int(k), "name": v} for k, v in sorted(self.label_map.items(), key=lambda kv: int(kv[0]))]


class DatasetLoader:
    def __init__(self, data_dir: Path, label_helper: LabelHelper):
        self.data_dir = Path(data_dir)
        self.label_helper = label_helper
        self.user_ann_path = Path("app/data/user_annotations.json")

    def _extract_feature(self, obj) -> np.ndarray:
        arr = np.asarray(obj, dtype=np.float32)
        if arr.ndim > 1:
            arr = arr.mean(axis=0)
        return arr.flatten()

    def load_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for rec in self.load_user_annotations():
            X.append(self._extract_feature(rec["feature"]))
            y.append(int(rec["label_id"]))
        if not X:
            raise RuntimeError("没有可用的标注数据，请先通过页面上传并标注视频后再训练。")
        max_len = max(len(v) for v in X)
        X_padded = []
        for v in X:
            if len(v) < max_len:
                v = np.concatenate([v, np.zeros(max_len - len(v), dtype=np.float32)])
            X_padded.append(v)
        return np.vstack(X_padded), np.array(y)

    def load_user_annotations(self):
        if not self.user_ann_path.exists():
            return []
        return json.loads(self.user_ann_path.read_text(encoding="utf-8"))

    def append_annotation(self, record):
        existing = []
        if self.user_ann_path.exists():
            existing = json.loads(self.user_ann_path.read_text(encoding="utf-8"))
        existing.append(record)
        self.user_ann_path.parent.mkdir(parents=True, exist_ok=True)
        self.user_ann_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

