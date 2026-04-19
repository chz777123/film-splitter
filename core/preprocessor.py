import numpy as np
import cv2
import logging

logger = logging.getLogger("film_splitter")

def create_proxy_image(image: np.ndarray, target_width: int = 1000) -> np.ndarray:
    """
    生成 8-bit 灰度代理图，用于 UI 渲染和核心识别算法
    
    :param image: 高位深或大尺寸原图 (可能是 RGB 或灰度)
    :param target_width: 代理图的期望宽度，用于降采样
    :return: 8-bit 灰度代理图矩阵
    """
    logger.info("---------- 开始生成 8-bit 代理图 ----------")
    
    if image is None or image.size == 0:
        logger.warning("输入图像为空，返回空数组")
        return np.array([])
        
    H, W = image.shape[:2]
    channels = image.shape[2] if len(image.shape) == 3 else 1
    logger.info(f"原图信息: 尺寸={W}x{H}, 通道数={channels}, "
                f"dtype={image.dtype}, 位深={image.dtype.itemsize * 8}-bit")
    logger.debug(f"原图像素值范围: [{np.min(image)}, {np.max(image)}]")
    
    # 1. 降采样 (保持长宽比)
    scale = target_width / W if W > target_width else 1.0
    new_W = int(W * scale)
    new_H = int(H * scale)
    logger.info(f"[降采样] 缩放比例: {scale:.6f}, 目标尺寸: {new_W}x{new_H}")
    
    resized = cv2.resize(image, (new_W, new_H), interpolation=cv2.INTER_AREA)
    logger.info(f"[降采样] cv2.resize 完成 (INTER_AREA)")
    
    # 2. 转换为灰度图
    if len(resized.shape) == 3:
        if resized.shape[2] == 3:
            gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
            logger.info("[灰度化] RGB -> Grayscale")
        elif resized.shape[2] == 4:
            gray = cv2.cvtColor(resized, cv2.COLOR_RGBA2GRAY)
            logger.info("[灰度化] RGBA -> Grayscale")
        else:
            gray = resized[:, :, 0]
            logger.info(f"[灰度化] 取第 0 通道作为灰度 (通道数={resized.shape[2]})")
    else:
        gray = resized
        logger.info("[灰度化] 输入已为单通道灰度图，无需转换")
        
    # 3. 映射到 8-bit (0-255)
    min_val = np.min(gray)
    max_val = np.max(gray)
    logger.info(f"[8-bit映射] 灰度值范围: [{min_val}, {max_val}]")
    
    if max_val > min_val:
        normalized = (gray.astype(np.float32) - min_val) / (max_val - min_val)
        proxy_8bit = (normalized * 255).astype(np.uint8)
        logger.info(f"[8-bit映射] 归一化完成 -> uint8, "
                    f"输出范围: [{np.min(proxy_8bit)}, {np.max(proxy_8bit)}]")
    else:
        proxy_8bit = np.zeros_like(gray, dtype=np.uint8)
        logger.warning("[8-bit映射] 灰度值恒定 (min==max)，输出全零矩阵")
        
    logger.info(f"---------- 代理图生成完成: {proxy_8bit.shape[1]}x{proxy_8bit.shape[0]}, "
                f"dtype={proxy_8bit.dtype} ----------")
    return proxy_8bit
