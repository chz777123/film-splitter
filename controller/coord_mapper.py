class CoordinateMapper:
    """
    坐标映射引擎 (代理图坐标 <-> 原图坐标)
    负责处理缩放带来的坐标偏移
    """
    def __init__(self):
        self.scale = 1.0  # ratio of proxy_width / original_width
        
    def update_scale(self, original_width: int, proxy_width: int):
        if original_width > 0:
            self.scale = proxy_width / original_width
        else:
            self.scale = 1.0
            
    def proxy_to_original(self, proxy_coord: int) -> int:
        """
        将 UI 上 8-bit 代理图的坐标还原为真实 16/32-bit 原图的坐标
        :param proxy_coord: 代理图上的坐标值 (x 或 y)
        :return: 对应原图上的坐标值
        """
        if self.scale <= 0:
            return 0
        return int(proxy_coord / self.scale)
        
    def original_to_proxy(self, orig_coord: int) -> int:
        """
        将真实原图上的坐标映射为 UI 代理图上的坐标 (供 UI 显示)
        :param orig_coord: 原图上的坐标值
        :return: 代理图上的坐标值
        """
        return int(orig_coord * self.scale)

    def map_frame_to_original(self, proxy_frame: dict) -> dict:
        """
        将包含四个坐标的字典从代理图坐标空间映射到原图坐标空间
        """
        return {
            "y_start": self.proxy_to_original(proxy_frame["y_start"]),
            "y_end": self.proxy_to_original(proxy_frame["y_end"]),
            "x_start": self.proxy_to_original(proxy_frame["x_start"]),
            "x_end": self.proxy_to_original(proxy_frame["x_end"])
        }
