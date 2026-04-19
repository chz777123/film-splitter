import sys
import os

# Ensure the core module is discoverable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pytest
from core.detector import find_film_frames

def test_find_film_frames_empty():
    assert find_film_frames(np.array([])) == []

def test_find_film_frames_invalid_shape():
    assert find_film_frames(np.array([1, 2, 3])) == []

def test_find_film_frames_basic_logic():
    """
    测试核心寻峰逻辑是否正确。
    模拟一个 8-bit 的胶片图像代理矩阵。
    """
    W, H = 100, 400
    # 假设背景较暗 (灰度 20)
    image = np.full((H, W), 20, dtype=np.uint8)
    
    # 添加间隙 (高亮且平坦，灰度 200)
    gaps = [50, 190, 330] # 间距 140 = 1.4 * 100 (W)
    gap_width = 10
    
    for gap in gaps:
        image[gap - gap_width//2 : gap + gap_width//2, :] = 200
        
    # 添加图像内容 (有梯度变化，亮度中等)
    # 加上随机噪声使得梯度不为 0
    np.random.seed(42) # 固定随机种子，保证测试可重复
    image[60:180, :] = np.random.randint(50, 150, size=(120, W), dtype=np.uint8)
    image[200:320, :] = np.random.randint(50, 150, size=(120, W), dtype=np.uint8)
    
    frames = find_film_frames(image)
    
    # 应该找到 2 个完整的胶片帧
    assert len(frames) == 2
    
    margin = int(W * 0.02) # 100 * 0.02 = 2
    
    # 验证第一帧
    # 由于高斯平滑的影响，峰值位置可能有一点点微小的偏移，我们用近似等于或在小范围内判断
    assert abs(frames[0]["y_start"] - (50 + margin)) <= 2
    assert abs(frames[0]["y_end"] - (190 - margin)) <= 2
    assert frames[0]["x_start"] == margin
    assert frames[0]["x_end"] == W - margin
    
    # 验证第二帧
    assert abs(frames[1]["y_start"] - (190 + margin)) <= 2
    assert abs(frames[1]["y_end"] - (330 - margin)) <= 2
    assert frames[1]["x_start"] == margin
    assert frames[1]["x_end"] == W - margin
