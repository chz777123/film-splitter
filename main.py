import sys
from PySide6.QtWidgets import QApplication
from controller.state_manager import StateManager
from controller.task_scheduler import TaskScheduler
from ui.main_window import MainWindow
from utils.logger import logger

def main():
    logger.info("Starting 135 Film Splitter Application...")
    app = QApplication(sys.argv)
    
    # 依赖注入 (DI): 实例化业务逻辑层对象
    state_manager = StateManager()
    task_scheduler = TaskScheduler()
    
    # 实例化 UI 展现层，将业务逻辑控制器注入
    window = MainWindow(state_manager, task_scheduler)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
