from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QFileDialog, QLabel, QMessageBox)
from core.image_io import load_tiff, save_tiff_slice
from core.preprocessor import create_proxy_image
from core.detector import find_film_frames
from utils.logger import logger
from .canvas import InteractiveCanvas
import os

class MainWindow(QMainWindow):
    """
    主窗口 (View Layer)
    包含控制面板和画布，通过业务逻辑层处理数据。
    """
    def __init__(self, state_manager, task_scheduler):
        super().__init__()
        self.state_manager = state_manager
        self.task_scheduler = task_scheduler
        
        self.setWindowTitle("135 Film Splitter")
        self.resize(1200, 800)
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧：参数控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_panel.setFixedWidth(200)
        
        self.btn_load = QPushButton("Load TIFF")
        self.btn_load.clicked.connect(self.on_load_clicked)
        
        self.btn_detect = QPushButton("Auto Detect Frames")
        self.btn_detect.clicked.connect(self.on_detect_clicked)
        self.btn_detect.setEnabled(False)
        
        self.btn_export = QPushButton("Export Slices")
        self.btn_export.clicked.connect(self.on_export_clicked)
        self.btn_export.setEnabled(False)
        
        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        
        control_layout.addWidget(self.btn_load)
        control_layout.addWidget(self.btn_detect)
        control_layout.addWidget(self.btn_export)
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        
        # 右侧：交互画布
        self.canvas = InteractiveCanvas()
        
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.canvas)
        
    def set_status(self, text):
        self.status_label.setText(text)
        logger.info(f"UI Status: {text}")
        
    def on_load_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open TIFF", "", "TIFF Images (*.tif *.tiff)")
        if not filepath:
            return
            
        self.set_status("Loading and generating proxy...")
        self.btn_load.setEnabled(False)
        
        # 后台执行耗时 I/O 和预处理 (防止 UI 假死)
        def load_task():
            img = load_tiff(filepath)
            proxy = create_proxy_image(img)
            return filepath, img.shape, proxy
            
        self.task_scheduler.run_task(
            load_task,
            on_result=self.on_load_success,
            on_error=lambda err: self.set_status(f"Load failed: {err[1]}"),
            on_finished=lambda: self.btn_load.setEnabled(True)
        )
        
    def on_load_success(self, result):
        filepath, shape, proxy = result
        self.state_manager.set_image_info(filepath, proxy, shape)
        self.canvas.set_image(proxy)
        self.btn_detect.setEnabled(True)
        self.btn_export.setEnabled(False)
        self.set_status(f"Loaded: {os.path.basename(filepath)}")
        
    def on_detect_clicked(self):
        if self.state_manager.proxy_image is None:
            return
            
        self.set_status("Detecting frames...")
        self.btn_detect.setEnabled(False)
        self.btn_export.setEnabled(False)
        
        proxy_img = self.state_manager.proxy_image
        
        # 后台执行核心算法层的纯计算函数
        self.task_scheduler.run_task(
            lambda: find_film_frames(proxy_img),
            on_result=self.on_detect_success,
            on_error=lambda err: self.set_status(f"Detect failed: {err[1]}"),
            on_finished=lambda: self.btn_detect.setEnabled(True)
        )
        
    def on_detect_success(self, frames):
        self.state_manager.set_frames(frames)
        self.canvas.render_frames(frames)
        self.btn_export.setEnabled(True)
        self.set_status(f"Detected {len(frames)} frames. You can drag to adjust.")
        
    def on_export_clicked(self):
        if not self.state_manager.original_filepath:
            return
            
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Directory")
        if not export_dir:
            return
            
        # 1. 从前端画布获取用户可能微调过的最新代理图坐标
        final_proxy_frames = self.canvas.get_current_frames()
        self.state_manager.set_frames(final_proxy_frames)
        
        # 2. 调用业务逻辑层的映射引擎：代理坐标 -> 高位深原图坐标
        mapper = self.state_manager.mapper
        orig_frames = [mapper.map_frame_to_original(f) for f in final_proxy_frames]
        orig_path = self.state_manager.original_filepath
        
        self.set_status("Exporting slices...")
        self.btn_export.setEnabled(False)
        
        # 3. 后台执行高位深切片裁切与保存
        def export_task():
            logger.info("Reading original high-bit TIFF for lossless export...")
            img = load_tiff(orig_path)
            
            # 读取原图关键元数据
            import tifffile
            metadata = {}
            try:
                with tifffile.TiffFile(orig_path) as tif:
                    page = tif.pages[0]
                    res_x = page.tags.get('XResolution')
                    res_y = page.tags.get('YResolution')
                    res_unit = page.tags.get('ResolutionUnit')
                    icc = page.tags.get('ICCProfile')
                    
                    if res_x and res_y:
                        metadata['resolution'] = (res_x.value, res_y.value)
                    if res_unit:
                        metadata['resolutionunit'] = res_unit.value
                    if icc:
                        metadata['icc_profile'] = icc.value
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {e}")
                
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            
            for idx, frame in enumerate(orig_frames):
                y1, y2 = frame["y_start"], frame["y_end"]
                x1, x2 = frame["x_start"], frame["x_end"]
                
                # 安全边界检查，防止越界
                h, w = img.shape[:2]
                y1, y2 = max(0, y1), min(h, y2)
                x1, x2 = max(0, x1), min(w, x2)
                
                if y1 >= y2 or x1 >= x2:
                    logger.warning(f"Invalid frame skipped: {frame}")
                    continue
                    
                slice_img = img[y1:y2, x1:x2]
                out_path = os.path.join(export_dir, f"{base_name}_frame_{idx+1}.tif")
                save_tiff_slice(out_path, slice_img, metadata=metadata)
                logger.info(f"Saved {out_path}")
                
            return len(orig_frames)
            
        self.task_scheduler.run_task(
            export_task,
            on_result=self.on_export_success,
            on_error=lambda err: self.set_status(f"Export failed: {err[1]}"),
            on_finished=lambda: self.btn_export.setEnabled(True)
        )
        
    def on_export_success(self, count):
        msg = f"Successfully exported {count} frames."
        self.set_status(msg)
        QMessageBox.information(self, "Export Complete", msg)
