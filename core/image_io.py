import tifffile
import numpy as np
import logging

logger = logging.getLogger("film_splitter")

def load_tiff(filepath: str) -> np.ndarray:
    """
    使用 tifffile 读取高位深 TIFF 图像 (纯 I/O 无副作用)
    
    :param filepath: TIFF 文件路径
    :return: 图像矩阵 (可能是 16-bit 或 32-bit, 多通道或单通道)
    """
    logger.info(f"[I/O] 开始读取 TIFF: {filepath}")
    image = tifffile.imread(filepath)
    
    size_mb = image.nbytes / (1024 * 1024)
    logger.info(f"[I/O] 读取完成: shape={image.shape}, dtype={image.dtype}, "
                f"占用内存={size_mb:.1f} MB")
    logger.debug(f"[I/O] 像素值范围: [{np.min(image)}, {np.max(image)}]")
    return image

def save_tiff_slice(filepath: str, image_slice: np.ndarray, metadata: dict = None):
    """
    无损保存高位深图像切片 (纯 I/O)
    
    :param filepath: 保存路径
    :param image_slice: 原图切片矩阵
    :param metadata: 可选的元数据字典 (如 resolution, icc_profile)
    """
    # 简单判断 photometric 以兼容灰度或 RGB 图像
    if len(image_slice.shape) == 3 and image_slice.shape[2] in [3, 4]:
        photometric = 'rgb'
    else:
        photometric = 'minisblack'
    
    size_mb = image_slice.nbytes / (1024 * 1024)
    logger.info(f"[I/O] 保存切片: {filepath}")
    logger.info(f"[I/O]   shape={image_slice.shape}, dtype={image_slice.dtype}, "
                f"大小={size_mb:.1f} MB, photometric={photometric}")
        
    kwargs = {'photometric': photometric}
    if metadata:
        if metadata.get('resolution'):
            kwargs['resolution'] = metadata['resolution']
        if metadata.get('resolutionunit'):
            kwargs['resolutionunit'] = metadata['resolutionunit']
        if metadata.get('icc_profile'):
            # ICC Profile 在 TIFF 规范中 Tag ID 为 34675，类型为 Byte (B)
            kwargs['extratags'] = [(34675, 'B', len(metadata['icc_profile']), metadata['icc_profile'], True)]
            logger.info("[I/O]   已附加 ICC Profile 及分辨率元数据")
            
    tifffile.imwrite(filepath, image_slice, **kwargs)
    logger.info(f"[I/O]   写入完成 ✓")
