# -*- coding: utf-8 -*-
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base='Console'
setup(  name = "鬼武者节点测试工具",
        version = "1.2.0",
        description = "GWZ CDN TEST",
        options = {"build_exe": build_exe_options},
        executables = [Executable("GWZ_CDN_TEST.py", base=base)])