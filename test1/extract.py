#!/usr/bin/env python3
import numpy as np
 
def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))
 
def angle_between(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return np.arccos(np.clip(cosine_angle, -1.0, 1.0))  
 
def extract_features(keypoints):
 
    keypoints = np.array(keypoints)
    if keypoints.shape != (21, 3):
        raise ValueError("Expected input shape (21, 3), got {}".format(keypoints.shape))
 
    features = []
 
    pairs = [
        (0, 4), (0, 8), (0, 12), (0, 16), (0, 20),
        (4, 8), (8, 12), (12, 16), (16, 20),    
        (5, 9), (9, 13), (13, 17)
    ]
 
    for i, j in pairs:
        dist = euclidean(keypoints[i], keypoints[j])
        features.append(dist)
 
    angles = [
        (0, 1, 2), (1, 2, 3), (2, 3, 4),
        (0, 5, 6), (5, 6, 7), (6, 7, 8),
        (0, 9,10), (9,10,11), (10,11,12),
        (0,13,14), (13,14,15), (14,15,16),
        (0,17,18), (17,18,19), (18,19,20)
    ]
 
    for a, b, c in angles:
        ang = angle_between(keypoints[a], keypoints[b], keypoints[c])
        features.append(ang)
 
    return np.array(features)