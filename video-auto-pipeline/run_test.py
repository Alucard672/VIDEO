#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立的系统测试运行脚本
自动处理虚拟环境激活和路径设置
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    
    print("==========================================")
    print("视频自动化系统测试")
    print("==========================================")
    
    # 检查是否在虚拟环境中
    if not os.environ.get('VIRTUAL_ENV'):
        print("检测到未激活虚拟环境，正在激活...")
        
        # 检查虚拟环境是否存在
        venv_path = script_dir / "venv"
        if not venv_path.exists():
            print("❌ 虚拟环境不存在，请先运行 quick_start.sh")
            return 1
        
        # 激活虚拟环境并运行测试
        activate_script = venv_path / "bin" / "activate"
        if os.name == 'nt':  # Windows
            activate_script = venv_path / "Scripts" / "activate.bat"
        
        if not activate_script.exists():
            print(f"❌ 虚拟环境激活脚本不存在: {activate_script}")
            return 1
        
        # 使用subprocess运行测试
        test_script = script_dir / "test_system.py"
        if os.name == 'nt':  # Windows
            cmd = f'"{venv_path}\\Scripts\\python.exe" "{test_script}"'
        else:  # Unix/Linux/macOS
            cmd = f'"{venv_path}/bin/python" "{test_script}"'
        
        print(f"运行命令: {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=script_dir)
        return result.returncode
    else:
        print("✅ 已在虚拟环境中")
        # 直接运行测试
        test_script = script_dir / "test_system.py"
        result = subprocess.run([sys.executable, str(test_script)], cwd=script_dir)
        return result.returncode

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 