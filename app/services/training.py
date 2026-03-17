from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from app.services.dataset import DatasetLoader, LabelHelper

class Trainer:
    def __init__(self, data_dir: Path, model_dir: Path, label_helper: LabelHelper):
        self.data_dir = Path(data_dir)
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.label_helper = label_helper
        self.dataset = DatasetLoader(self.data_dir, self.label_helper)
        self.model_path = self.model_dir / "pingpong_model.joblib"

    def train(self):
        X, y = self.dataset.load_training_data()
        pipeline = Pipeline([
            ("scaler", StandardScaler(with_mean=False)),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1)),
        ])
        pipeline.fit(X, y)
        joblib.dump(pipeline, self.model_path)
        return {"samples": len(y), "classes": len(set(y)), "path": str(self.model_path)}

    def save_user_annotation(self, features: np.ndarray, label_id: int, filename: str):
        record = {
            "filename": filename,
            "label_id": int(label_id),
            "feature": features.astype(float).tolist(),
        }
        self.dataset.append_annotation(record)
        return record

