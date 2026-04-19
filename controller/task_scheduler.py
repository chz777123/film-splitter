import sys
import traceback
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from utils.logger import logger

class TaskSignals(QObject):
    """
    定义后台任务可发射的信号
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)

class Worker(QRunnable):
    """
    可运行的 Worker，用于在 QThreadPool 中后台执行任务
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()

    @Slot()
    def run(self):
        try:
            # 执行耗时操作 (例如图像加载、预处理、核心识别算法)
            result = self.fn(*self.args, **self.kwargs)
        except Exception:
            exctype, value = sys.exc_info()[:2]
            logger.error(f"Worker Error: {value}\n{traceback.format_exc()}")
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class TaskScheduler:
    """
    异步任务调度器 (防止 UI 假死)
    """
    def __init__(self):
        self.threadpool = QThreadPool()
        logger.info(f"TaskScheduler initialized. Max threads: {self.threadpool.maxThreadCount()}")
        
    def run_task(self, func, on_result=None, on_error=None, on_finished=None, *args, **kwargs):
        """
        提交一个函数到后台线程执行
        
        :param func: 要执行的纯函数或耗时 I/O 函数
        :param on_result: 成功返回结果时的 UI 回调
        :param on_error: 出错时的 UI 回调
        :param on_finished: 结束时的 UI 回调 (无论成功或失败)
        """
        worker = Worker(func, *args, **kwargs)
        
        if on_result:
            worker.signals.result.connect(on_result)
            
        if on_error:
            worker.signals.error.connect(on_error)
            
        if on_finished:
            worker.signals.finished.connect(on_finished)
            
        self.threadpool.start(worker)
