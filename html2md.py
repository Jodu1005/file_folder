#!/usr/bin/env python3
"""
HTML 转 Markdown 转换器
"""

import argparse
import sys
from pathlib import Path

try:
    import html2text
except ImportError:
    print("错误: 需要安装 html2text 库")
    print("请运行: pip install html2text")
    sys.exit(1)


def html_to_markdown(html_content: str, body_width: int = 0) -> str:
    """将 HTML 内容转换为 Markdown"""
    h = html2text.HTML2Text()
    h.body_width = body_width  # 0 表示不换行
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.ignore_tables = False
    h.unicode_snob = True
    h.skip_internal_links = True
    return h.handle(html_content)


def convert_file(input_path: str, output_path: str = None, body_width: int = 0):
    """转换单个 HTML 文件为 Markdown"""
    input_file = Path(input_path)

    if not input_file.exists():
        print(f"错误: 文件不存在: {input_path}")
        sys.exit(1)

    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    md_content = html_to_markdown(html_content, body_width)

    if output_path:
        output_file = Path(output_path)
    else:
        output_file = input_file.with_suffix('.md')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"转换成功: {input_path} -> {output_file}")


def convert_directory(input_dir: str, output_dir: str = None, body_width: int = 0):
    """转换目录下所有 HTML 文件"""
    input_path = Path(input_dir)

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path

    html_files = list(input_path.glob('*.html')) + list(input_path.glob('*.htm'))

    if not html_files:
        print(f"在 {input_dir} 中未找到 HTML 文件")
        return

    print(f"找到 {len(html_files)} 个 HTML 文件")

    for html_file in html_files:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        md_content = html_to_markdown(html_content, body_width)
        output_file = output_path / html_file.with_suffix('.md').name

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"转换成功: {html_file.name} -> {output_file.name}")


def main():
    parser = argparse.ArgumentParser(description='将 HTML 文件转换为 Markdown')
    parser.add_argument('input', help='输入 HTML 文件或目录')
    parser.add_argument('-o', '--output', help='输出文件或目录 (默认: 与输入同目录)')
    parser.add_argument('-w', '--width', type=int, default=0, help='行宽 (默认: 0 不换行)')
    parser.add_argument('-d', '--directory', action='store_true', help='批量转换目录')

    args = parser.parse_args()

    if args.directory or Path(args.input).is_dir():
        convert_directory(args.input, args.output, args.width)
    else:
        convert_file(args.input, args.output, args.width)


if __name__ == '__main__':
    main()