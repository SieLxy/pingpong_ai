from pathlib import Path
import joblib
import numpy as np
from fastapi import HTTPException
from app.services.scoring import score_action, suggestion_for_label

class InferenceService:
    def __init__(self, model_dir: Path, label_helper):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "pingpong_model.joblib"
        self.label_helper = label_helper
        self.model = None
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def reload(self):
        if self.model_path.exists():
            self.model = joblib.load(self.model_path)

    def _align_feature_dim(self, feat: np.ndarray) -> np.ndarray:
        if self.model is None:
            return feat.reshape(1, -1)
        expected = getattr(self.model, "n_features_in_", None)
        try:
            expected = expected or self.model.named_steps["scaler"].n_features_in_
        except Exception:
            pass
        if not expected:
            return feat.reshape(1, -1)
        flat = feat.flatten()
        if len(flat) < expected:
            flat = np.concatenate([flat, np.zeros(expected - len(flat), dtype=flat.dtype)])
        elif len(flat) > expected:
            flat = flat[:expected]
        return flat.reshape(1, -1)

    def predict(self, features: np.ndarray, stats: dict):
        if self.model is None:
            raise HTTPException(status_code=400, detail="模型未训练，请先上传并标注视频后再训练")
        X = self._align_feature_dim(features)
        probs = self.model.predict_proba(X)[0]
        classes = self.model.classes_
        pred_idx = int(np.argmax(probs))
        pred_label_id = int(classes[pred_idx])
        confidence = float(probs[pred_idx])
        score = score_action(confidence, stats)
        label_name = self.label_helper.id_to_name(pred_label_id)
        return {
            "label_id": pred_label_id,
            "label_name": label_name,
            "confidence": confidence,
            "score": score,
            "suggestions": suggestion_for_label(label_name),
            "stats": stats,
        }

