from typing import Tuple
import cv2
import mediapipe as mp
import numpy as np


def extract_features_from_video(video_path: str) -> Tuple[np.ndarray, dict]:
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5)
    cap = cv2.VideoCapture(video_path)
    all_landmarks = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        if results.pose_landmarks:
            coords = []
            for lm in results.pose_landmarks.landmark:
                coords.extend([lm.x, lm.y, lm.z, lm.visibility])
            all_landmarks.append(coords)
    cap.release()
    pose.close()

    if not all_landmarks:
        raise RuntimeError("No pose landmarks detected in video")

    arr = np.array(all_landmarks)
    mean = arr.mean(axis=0)
    std = arr.std(axis=0)
    features = np.concatenate([mean, std])
    stats = {"frames": len(all_landmarks), "mean_std": float(std.mean())}
    return features, stats

