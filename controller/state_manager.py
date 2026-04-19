from utils.logger import logger
from .coord_mapper import CoordinateMapper

class StateManager:
    """
    状态管理器
    记录当前加载的图像信息、代理图、坐标映射器、UI框选状态等
    """
    def __init__(self):
        self.original_filepath = None
        self.proxy_image = None
        self.original_shape = None  # (H, W) 
        self.mapper = CoordinateMapper()
        self.frames = []  # list of dictionaries (在 proxy 坐标系下)
        
    def set_image_info(self, filepath: str, proxy_img, orig_shape):
        """
        加载图像后，更新全局状态
        """
        self.original_filepath = filepath
        self.proxy_image = proxy_img
        self.original_shape = orig_shape
        
        orig_h, orig_w = orig_shape[:2]
        proxy_h, proxy_w = proxy_img.shape[:2]
        
        # 更新坐标映射引擎的比例
        self.mapper.update_scale(orig_w, proxy_w)
        
        logger.info(f"Image state updated: {filepath}")
        logger.info(f"Original size: {orig_w}x{orig_h}, Proxy size: {proxy_w}x{proxy_h}")
        logger.info(f"Scale factor: {self.mapper.scale:.4f}")
        
    def set_frames(self, frames: list):
        """
        算法识别完毕或用户手动调整后，更新帧坐标信息
        """
        self.frames = frames
        logger.info(f"Updated {len(frames)} frames in StateManager.")
        
    def clear(self):
        self.original_filepath = None
        self.proxy_image = None
        self.original_shape = None
        self.frames = []
        self.mapper.update_scale(1, 1)
        logger.info("StateManager cleared.")
