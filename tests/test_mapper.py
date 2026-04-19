import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from controller.coord_mapper import CoordinateMapper

def test_mapper_scale_calculation():
    mapper = CoordinateMapper()
    # 原图宽度 5000，代理图宽度 1000 => 缩放比例 0.2
    mapper.update_scale(5000, 1000)
    assert mapper.scale == 0.2

def test_mapper_proxy_to_original():
    mapper = CoordinateMapper()
    mapper.update_scale(5000, 1000)
    
    # 代理图上的坐标 200，映射回原图应该是 200 / 0.2 = 1000
    assert mapper.proxy_to_original(200) == 1000

def test_mapper_original_to_proxy():
    mapper = CoordinateMapper()
    mapper.update_scale(5000, 1000)
    
    # 原图上的坐标 1500，映射到代理图上应该是 1500 * 0.2 = 300
    assert mapper.original_to_proxy(1500) == 300

def test_mapper_map_frame():
    mapper = CoordinateMapper()
    mapper.update_scale(4000, 800) # scale 0.2
    
    proxy_frame = {
        "y_start": 100,
        "y_end": 300,
        "x_start": 20,
        "x_end": 780
    }
    
    orig_frame = mapper.map_frame_to_original(proxy_frame)
    
    assert orig_frame["y_start"] == 500
    assert orig_frame["y_end"] == 1500
    assert orig_frame["x_start"] == 100
    assert orig_frame["x_end"] == 3900
