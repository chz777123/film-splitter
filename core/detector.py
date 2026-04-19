import numpy as np
import cv2
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
import logging

logger = logging.getLogger("film_splitter")

def find_film_frames(image: np.ndarray) -> list[dict]:
    """
    135底片高亮间隙特征识别算法 (Pure Function)
    
    支持多条带同时扫描：
      1. 条带分割：先在垂直于扫描方向上投影，分离出独立的胶片条带
      2. 帧间隙识别：对每个条带分别进行两轮寻峰（探测估算 + 精确提取）
    
    :param image: 8-bit proxy image matrix I(x,y) (grayscale), W x H
    :return: List of dictionaries containing coordinates of frames
    """
    logger.info("========== 开始执行帧识别算法 ==========")
    
    if image is None or image.size == 0 or len(image.shape) != 2:
        logger.warning("输入图像无效 (None / 空 / 非二维矩阵)，直接返回空列表")
        return []
        
    H, W = image.shape
    logger.info(f"输入代理图尺寸: {W}x{H} (宽x高), dtype={image.dtype}")
    
    # ── Step 1: 自动判断胶片方向与条带分割 ──
    is_horizontal = W > H
    direction = "横向 (W>H, 胶片水平放置, 间隙为垂直线)" if is_horizontal else "纵向 (H>=W, 胶片垂直放置, 间隙为水平线)"
    logger.info(f"[Step 1] 自动判断扫描方向: {direction}")
    
    def min_max_norm(arr):
        min_val = np.min(arr)
        max_val = np.max(arr)
        if max_val - min_val == 0:
            return np.zeros_like(arr)
        return (arr - min_val) / (max_val - min_val)

    # 沿短边投影，寻找背景上的亮带（胶片本身比扫描仪纯黑背景亮）
    if is_horizontal:
        strip_proj = np.mean(image, axis=1) # 长度 H
        strip_base_len = H
    else:
        strip_proj = np.mean(image, axis=0) # 长度 W
        strip_base_len = W
        
    strip_sigma = max(5, strip_base_len // 100)
    strip_proj_smooth = gaussian_filter1d(strip_proj, sigma=strip_sigma)
    strip_proj_norm = min_max_norm(strip_proj_smooth)
    
    # 假设一个有效的胶片条带至少占据扫描仪宽度的 10%
    min_strip_width = max(10, strip_base_len // 10)
    
    strip_peaks, strip_props = find_peaks(
        strip_proj_norm, 
        prominence=0.1, 
        width=min_strip_width, 
        rel_height=0.8 # 在波峰 80% 深度处测量宽度，以获取条带边界
    )
    
    strips = []
    if len(strip_peaks) > 0:
        starts = strip_props['left_ips'].astype(int)
        ends = strip_props['right_ips'].astype(int)
        for s, e in zip(starts, ends):
            # 向外扩展一点安全余量 2%
            margin = int(strip_base_len * 0.02)
            s = max(0, s - margin)
            e = min(strip_base_len, e + margin)
            # 过滤掉过窄的伪条带
            if e - s > min_strip_width:
                strips.append((s, e))
    
    # 如果没检测到明显的条带（例如纯白背景单条底片），则退化为将整张图视为一个条带
    if not strips:
        logger.info("[Step 1] 未检测到多条带特征，将整张图作为单一胶片处理")
        strips.append((0, strip_base_len))
        
    logger.info(f"[Step 1] 条带分割完成: 共分离出 {len(strips)} 个胶片条带")
    for idx, (s, e) in enumerate(strips):
        logger.info(f"  条带 #{idx+1}: 宽度坐标 [{s}, {e}], 实际宽度 {e-s}px")
        
    all_frames = []
    
    # ── Step 2: 对每个条带分别进行帧识别 ──
    for strip_idx, (s, e) in enumerate(strips):
        logger.info(f"--- 开始处理条带 #{strip_idx+1} ---")
        
        if is_horizontal:
            strip_img = image[s:e, :]
            base_len = e - s # 当前条带的高度
            signal_len = W   # 当前条带的长度
        else:
            strip_img = image[:, s:e]
            base_len = e - s # 当前条带的宽度
            signal_len = H   # 当前条带的长度
            
        # 1. 信号提取
        if is_horizontal:
            Sb = np.mean(strip_img, axis=0)
            sobel = cv2.Sobel(strip_img, cv2.CV_64F, 1, 0, ksize=3)
            Sg = np.mean(np.abs(sobel), axis=0)
        else:
            Sb = np.mean(strip_img, axis=1)
            sobel = cv2.Sobel(strip_img, cv2.CV_64F, 0, 1, ksize=3)
            Sg = np.mean(np.abs(sobel), axis=1)
            
        # 2. 平滑与归一化
        sigma = max(3, base_len // 150)
        Sb_smooth = gaussian_filter1d(Sb, sigma=sigma)
        Sg_smooth = gaussian_filter1d(Sg, sigma=sigma)
        
        Sb_norm = min_max_norm(Sb_smooth)
        Sg_norm = min_max_norm(Sg_smooth)
        
        # 3. 信号融合（Gap Score）
        S_score = Sb_norm * (1.0 - Sg_norm)
        score_range = np.max(S_score) - np.min(S_score)
        
        # 4. 寻峰 (依据 135 胶片物理几何比例)
        # 135 胶片半格(Half-frame)的长边与胶片宽度的比例约为 18/35 ≈ 0.51
        # 全格(Full-frame)约为 36/35 ≈ 1.03
        # 所以物理上任意两个相邻间隙的最小距离必定 > 0.45 * base_len
        distance = max(1, int(0.45 * base_len))
        prominence = max(0.05, 0.15 * score_range)
        
        logger.info(f"[条带 #{strip_idx+1}] 寻峰参数: distance={distance}, prominence={prominence:.4f}")
        peaks, properties = find_peaks(
            S_score, distance=distance, prominence=prominence
        )
        logger.info(f"[条带 #{strip_idx+1}] 寻峰结果: 最终确认 {len(peaks)} 个间隙")
        
        if len(peaks) == 0:
            logger.warning(f"[条带 #{strip_idx+1}] 未发现有效间隙，跳过该条带")
            continue
            
        # 5. 边缘帧检测与坐标生成
        margin = int(base_len * 0.02)
        virtual_peaks = list(peaks)
        
        # 估算平均帧间距，用于判断首尾是否有遗漏的边缘帧
        if len(peaks) >= 2:
            avg_spacing = np.median(np.diff(peaks))
        else:
            # 如果只有一个间隙，默认按全格距估算
            avg_spacing = 1.08 * base_len
        
        # 补齐首尾边缘帧
        if virtual_peaks[0] > 0.4 * avg_spacing:
            logger.info(f"[条带 #{strip_idx+1}] 补充首部边缘帧 (距离 {virtual_peaks[0]}px > 阈值)")
            virtual_peaks.insert(0, 0)
        if signal_len - virtual_peaks[-1] > 0.4 * avg_spacing:
            logger.info(f"[条带 #{strip_idx+1}] 补充尾部边缘帧 (距离 {signal_len - virtual_peaks[-1]}px > 阈值)")
            virtual_peaks.append(signal_len)
            
        for i in range(len(virtual_peaks) - 1):
            gap1 = virtual_peaks[i]
            gap2 = virtual_peaks[i+1]
            
            if is_horizontal:
                x_start = int(gap1 + margin)
                x_end = int(gap2 - margin)
                y_start = int(s + margin)
                y_end = int(e - margin)
            else:
                y_start = int(gap1 + margin)
                y_end = int(gap2 - margin)
                x_start = int(s + margin)
                x_end = int(e - margin)
                
            if y_start < y_end and x_start < x_end:
                all_frames.append({
                    "y_start": y_start,
                    "y_end": y_end,
                    "x_start": x_start,
                    "x_end": x_end
                })
                
    logger.info(f"========== 帧识别算法完成: 共识别出 {len(all_frames)} 个有效帧 ==========")
    return all_frames
