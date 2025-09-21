#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import exifread
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

def get_exif_date(image_path):
    """从图片中提取EXIF拍摄日期信息"""
    try:
        with open(image_path, 'rb') as f:
            tags = exifread.process_file(f)
            
        # 尝试获取不同格式的日期标签
        date_tags = [
            'EXIF DateTimeOriginal',
            'EXIF DateTimeDigitized',
            'Image DateTime'
        ]
        
        for tag in date_tags:
            if tag in tags:
                date_str = str(tags[tag])
                # 通常EXIF日期格式为: YYYY:MM:DD HH:MM:SS
                try:
                    date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    return date_obj.strftime('%Y-%m-%d')  # 返回年月日格式
                except ValueError:
                    continue
                    
        return None
    except Exception as e:
        print(f"读取EXIF信息时出错: {e}")
        return None

def add_watermark(image_path, output_path, date_text, position='right-bottom', 
                 font_size=36, font_color=(255, 255, 255, 128)):
    """向图片添加水印"""
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            # 尝试使用系统字体
            font_path = None
            
            # 在Windows系统上尝试找到一个中文字体
            if os.name == 'nt':
                font_path = "C:\\Windows\\Fonts\\simhei.ttf"  # 黑体
                if not os.path.exists(font_path):
                    font_path = "C:\\Windows\\Fonts\\simsun.ttc"  # 宋体
                    
            # 在macOS上尝试找到一个中文字体
            elif sys.platform == 'darwin':
                font_path = "/System/Library/Fonts/PingFang.ttc"
                
            # 在Linux上尝试找到一个中文字体
            else:
                possible_fonts = [
                    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
                ]
                for path in possible_fonts:
                    if os.path.exists(path):
                        font_path = path
                        break
                        
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 如果找不到合适的字体，使用默认字体
                font = ImageFont.load_default()
                print("警告: 未找到合适的字体，使用默认字体")
        except Exception as e:
            print(f"加载字体时出错: {e}，使用默认字体")
            font = ImageFont.load_default()
        
        # 获取图片尺寸
        width, height = img.size
        
        # 获取文本尺寸
        if hasattr(draw, 'textsize'):
            text_width, text_height = draw.textsize(date_text, font=font)
        elif hasattr(font, 'getbbox'):
            # 新版Pillow使用getbbox
            bbox = font.getbbox(date_text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        elif hasattr(font, 'getlength'):
            # 如果有getlength但没有getbbox
            text_width = font.getlength(date_text)
            # 估算高度，可能不够精确
            text_height = font_size
        else:
            # 最后的备选方案
            text_width = len(date_text) * (font_size // 2)
            text_height = font_size
        
        # 根据位置参数确定水印位置
        padding = 10  # 边距
        
        if position == 'left-top':
            position = (padding, padding)
        elif position == 'center-top':
            position = ((width - text_width) // 2, padding)
        elif position == 'right-top':
            position = (width - text_width - padding, padding)
        elif position == 'left-center':
            position = (padding, (height - text_height) // 2)
        elif position == 'center':
            position = ((width - text_width) // 2, (height - text_height) // 2)
        elif position == 'right-center':
            position = (width - text_width - padding, (height - text_height) // 2)
        elif position == 'left-bottom':
            position = (padding, height - text_height - padding)
        elif position == 'center-bottom':
            position = ((width - text_width) // 2, height - text_height - padding)
        elif position == 'right-bottom':
            position = (width - text_width - padding, height - text_height - padding)
        else:
            # 默认右下角
            position = (width - text_width - padding, height - text_height - padding)
        
        # 绘制水印文本
        try:
            draw.text(position, date_text, font=font, fill=font_color)
        except TypeError:
            # 对于某些PIL版本，可能需要不同的参数格式
            draw.text(position, date_text, font=font, fill=font_color[:3])
        
        # 保存图片
        img.save(output_path)
        return True
    except Exception as e:
        print(f"添加水印时出错: {e}")
        return False

def process_images(input_path, position, font_size, font_color):
    """处理指定路径下的所有图片"""
    if os.path.isfile(input_path):
        # 处理单个文件
        files = [input_path]
        base_dir = os.path.dirname(input_path)
    elif os.path.isdir(input_path):
        # 处理目录下的所有文件
        base_dir = input_path
        files = [os.path.join(input_path, f) for f in os.listdir(input_path) 
                if os.path.isfile(os.path.join(input_path, f))]
    else:
        print(f"错误: 路径 '{input_path}' 不存在")
        return
    
    # 创建输出目录
    output_dir = os.path.join(base_dir, os.path.basename(base_dir) + "_watermark")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']
    
    processed_count = 0
    for file_path in files:
        # 检查是否为图片文件
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in image_extensions:
            continue
            
        # 获取EXIF日期
        date_text = get_exif_date(file_path)
        if not date_text:
            print(f"警告: 无法从 '{file_path}' 获取EXIF日期信息，跳过此文件")
            continue
            
        # 创建输出文件路径
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, filename)
        
        # 添加水印
        if add_watermark(file_path, output_path, date_text, position, font_size, font_color):
            processed_count += 1
            print(f"已处理: {file_path} -> {output_path}")
    
    print(f"\n处理完成! 共处理 {processed_count} 个文件，输出目录: {output_dir}")

def parse_color(color_str):
    """解析颜色字符串为RGBA元组"""
    try:
        # 处理十六进制颜色代码
        if color_str.startswith('#'):
            color_str = color_str.lstrip('#')
            if len(color_str) == 6:
                r, g, b = tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4))
                return (r, g, b, 255)  # 不透明
            elif len(color_str) == 8:
                r, g, b, a = tuple(int(color_str[i:i+2], 16) for i in (0, 2, 4, 6))
                return (r, g, b, a)
        
        # 处理RGB或RGBA格式
        if color_str.startswith('rgb(') or color_str.startswith('rgba('):
            color_str = color_str.replace('rgba(', '').replace('rgb(', '').replace(')', '')
            parts = [int(x.strip()) for x in color_str.split(',')]
            if len(parts) == 3:
                return tuple(parts) + (255,)  # 添加不透明度
            elif len(parts) == 4:
                return tuple(parts)
        
        # 处理命名颜色
        color_map = {
            'white': (255, 255, 255, 255),
            'black': (0, 0, 0, 255),
            'red': (255, 0, 0, 255),
            'green': (0, 255, 0, 255),
            'blue': (0, 0, 255, 255),
            'yellow': (255, 255, 0, 255),
            'cyan': (0, 255, 255, 255),
            'magenta': (255, 0, 255, 255),
            'gray': (128, 128, 128, 255),
            'transparent': (255, 255, 255, 128),  # 半透明白色
        }
        
        if color_str.lower() in color_map:
            return color_map[color_str.lower()]
            
    except Exception as e:
        print(f"解析颜色时出错: {e}，使用默认颜色")
    
    # 默认返回半透明白色
    return (255, 255, 255, 128)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='给图片添加EXIF日期水印')
    parser.add_argument('path', help='图片文件或包含图片的目录路径')
    parser.add_argument('-p', '--position', default='right-bottom',
                        choices=['left-top', 'center-top', 'right-top',
                                'left-center', 'center', 'right-center',
                                'left-bottom', 'center-bottom', 'right-bottom'],
                        help='水印位置 (默认: right-bottom)')
    parser.add_argument('-s', '--size', type=int, default=36,
                        help='字体大小 (默认: 36)')
    parser.add_argument('-c', '--color', default='transparent',
                        help='字体颜色，支持命名颜色(white, black, red等)、'
                             '十六进制(#RRGGBB或#RRGGBBAA)或RGB/RGBA格式 (默认: transparent)')
    
    args = parser.parse_args()
    
    # 解析颜色
    font_color = parse_color(args.color)
    
    # 处理图片
    process_images(args.path, args.position, args.size, font_color)

if __name__ == '__main__':
    main()