#!/usr/bin/env python
"""
文件上传与分析功能快速测试脚本
"""

import asyncio
from app.utils.file_analyzer import FileAnalyzer
from pathlib import Path

async def test_file_analyzer():
    """测试文件分析器"""
    print("=" * 60)
    print("🧪 文件分析器功能测试")
    print("=" * 60)
    
    # 测试 1: 文件格式检测
    print("\n✅ 测试 1: 文件格式检测")
    test_files = [
        "test.jpg",
        "document.pdf",
        "readme.txt",
        "report.docx",
        "unknown.xyz"
    ]
    
    for filename in test_files:
        is_supported, file_type = FileAnalyzer.is_supported_file(filename)
        status = "✓" if is_supported else "✗"
        print(f"  {status} {filename:<20} -> {file_type or '不支持'}")
    
    # 测试 2: 文件大小限制
    print("\n✅ 测试 2: 文件大小验证")
    test_sizes = [
        (1024, "1KB"),
        (1024 * 100, "100KB"),
        (1024 * 1024 * 5, "5MB"),
        (1024 * 1024 * 15, "15MB (超限制)")
    ]
    
    for size, label in test_sizes:
        is_valid, error = FileAnalyzer.validate_file("test.jpg", size)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {label:<20} -> {'有效' if is_valid else f'错误: {error}'}")
    
    # 测试 3: 模块功能检查
    print("\n✅ 测试 3: 依赖库检查")
    dependencies = {
        'PIL': False,
        'PyPDF2': False,
        'python-docx': False,
    }
    
    try:
        from PIL import Image
        dependencies['PIL'] = True
    except ImportError:
        pass
    
    try:
        import PyPDF2
        dependencies['PyPDF2'] = True
    except ImportError:
        pass
    
    try:
        from docx import Document
        dependencies['python-docx'] = True
    except ImportError:
        pass
    
    for lib, available in dependencies.items():
        status = "✓" if available else "✗"
        print(f"  {status} {lib:<20} -> {'已安装' if available else '未安装'}")
    
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    all_deps_available = all(dependencies.values())
    if all_deps_available:
        print("✅ 所有依赖库已安装，文件分析功能完全可用")
    else:
        print("⚠️  某些依赖库未安装，部分功能不可用")
        print("\n请运行以下命令安装缺失的库:")
        if not dependencies['PIL']:
            print("  pip install Pillow")
        if not dependencies['PyPDF2']:
            print("  pip install PyPDF2")
        if not dependencies['python-docx']:
            print("  pip install python-docx")
    
    print("\n" + "=" * 60)
    print("🚀 新增功能说明")
    print("=" * 60)
    print("""
所有新增功能:

1. 📁 文件上传 API (/api/upload-file)
   - 支持多文件批量上传
   - 自动格式检测和优化
   - 返回详细分析结果

2. 🔍 深度分析 API (/api/analyze-files)
   - 使用 AI 进行专业分析
   - 提供综合见解和建议
   - 支持多文件对比

3. 🖼️ 图片处理
   - 主要颜色提取
   - 尺寸信息识别
   - Base64 编码预览

4. 📄 文档处理
   - PDF: 智能文本提取 (前5页)
   - Word: 段落和表格识别
   - 文本: 自动编码检测

5. 💬 聊天集成
   - 在 AI 对话中上传文件
   - 自动文件分析和讨论
   - 携带文件内容的消息

更多信息请查看: FILE_UPLOAD_GUIDE.md
    """)

if __name__ == "__main__":
    asyncio.run(test_file_analyzer())
