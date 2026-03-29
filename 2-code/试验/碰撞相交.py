# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 11:01:54 2024

@author: ASUS
"""

from shapely.geometry import box

def create_rectangle(x1, y1, x2, y2, width):
    # 计算线段的方向向量
    dx = x2 - x1
    dy = y2 - y1

    # 计算垂直向量的单位向量
    length = (dx**2 + dy**2)**0.5
    normal_x = -dy / length
    normal_y = dx / length

    # 计算矩形的四个角
    offset_x = width / 2 * normal_x
    offset_y = width / 2 * normal_y

    x1_left = x1 + offset_x
    y1_left = y1 + offset_y
    x1_right = x1 - offset_x
    y1_right = y1 - offset_y
    x2_left = x2 + offset_x
    y2_left = y2 + offset_y
    x2_right = x2 - offset_x
    y2_right = y2 - offset_y

    # 创建矩形
    min_x = min(x1_left, x1_right, x2_left, x2_right)
    max_x = max(x1_left, x1_right, x2_left, x2_right)
    min_y = min(y1_left, y1_right, y2_left, y2_right)
    max_y = max(y1_left, y1_right, y2_left, y2_right)
    
    return box(min_x, min_y, max_x, max_y)

# 板凳参数
x1, y1, x2, y2, width = 0, 0, 10, 0, 2
x3, y3, x4, y4, width2 = 5, -1, 15, -1, 2

# 创建矩形
rect1 = create_rectangle(x1, y1, x2, y2, width)
rect2 = create_rectangle(x3, y3, x4, y4, width2)

# 检查是否相交
if rect1.intersects(rect2):
    print("碰撞发生")
else:
    print("没有碰撞")
