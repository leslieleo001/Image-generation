import sys
import os

# 添加项目根目录到Python路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件
    project_root = os.path.dirname(sys.executable)
else:
    # 如果是开发环境
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from PyQt6.QtWidgets import QApplication
from src.main.app import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 