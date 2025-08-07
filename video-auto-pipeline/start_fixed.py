#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的启动脚本
"""

import os
import sys
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# 导入必要的模块
try:
    from web_app import app
    
    if __name__ == "__main__":
        print("启动修复后的Web应用...")
        app.run(debug=True, host='0.0.0.0', port=5001)
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)
