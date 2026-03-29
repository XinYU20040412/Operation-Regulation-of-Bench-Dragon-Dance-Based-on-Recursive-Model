# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 11:35:04 2024

@author: ASUS
"""

import numpy as np

def compute_rectangle_vertices(x1, y1, x2, y2, width):
    # 计算方向向量
    d = np.array([x2 - x1, y2 - y1])
    
    # 计算垂直向量
    v = np.array([-d[1], d[0]])
    
    # 归一化垂直向量
    v_norm = v / np.linalg.norm(v)
    
    # 计算矩形的四个顶点
    offset = (width / 2) * v_norm
    vertices = [
        np.array([x1, y1]) + offset,
        np.array([x2, y2]) + offset,
        np.array([x2, y2]) - offset,
        np.array([x1, y1]) - offset
    ]
    return np.array(vertices)

def is_overlapping(vertices1, vertices2):
    def project(vertices, axis):
        projections = [np.dot(v, axis) for v in vertices]
        return min(projections), max(projections)
    
    def get_edges(vertices):
        edges = []
        for i in range(len(vertices)):
            edge = vertices[(i + 1) % len(vertices)] - vertices[i]
            edges.append(edge)
        return edges

    def get_normal(edge):
        return np.array([-edge[1], edge[0]])
    
    edges1 = get_edges(vertices1)
    edges2 = get_edges(vertices2)
    axes = [get_normal(edge) for edge in edges1] + [get_normal(edge) for edge in edges2]
    
    for axis in axes:
        min1, max1 = project(vertices1, axis)
        min2, max2 = project(vertices2, axis)
        if max1 < min2 or max2 < min1:
            return False
    return True

# 示例数据
x1, y1, x2, y2 = 0, 0, 1, 1
width = 0.2

# 计算矩形顶点
rect1_vertices = compute_rectangle_vertices(x1, y1, x2, y2, width)
rect2_vertices = compute_rectangle_vertices(x1 + 0.5, y1 + 0.5, x2 + 0.5, y2 + 0.5, width)

# 检查是否相交
collision = is_overlapping(rect1_vertices, rect2_vertices)
print("矩形相交:", collision)
#%%
import numpy as np

def compute_rectangle_vertices(x1, y1, x2, y2, width):
    d = np.array([x2 - x1, y2 - y1])
    v = np.array([-d[1], d[0]])
    v_norm = v / np.linalg.norm(v)
    
    offset = (width / 2) * v_norm
    vertices = [
        np.array([x1, y1]) + offset,
        np.array([x2, y2]) + offset,
        np.array([x2, y2]) - offset,
        np.array([x1, y1]) - offset
    ]
    return np.array(vertices)

def is_overlapping(vertices1, vertices2):
    def project(vertices, axis):
        projections = [np.dot(v, axis) for v in vertices]
        return min(projections), max(projections)
    
    def get_edges(vertices):
        edges = []
        for i in range(len(vertices)):
            edge = vertices[(i + 1) % len(vertices)] - vertices[i]
            edges.append(edge)
        return edges

    def get_normal(edge):
        return np.array([-edge[1], edge[0]])
    
    edges1 = get_edges(vertices1)
    edges2 = get_edges(vertices2)
    axes = [get_normal(edge) for edge in edges1] + [get_normal(edge) for edge in edges2]
    
    for axis in axes:
        min1, max1 = project(vertices1, axis)
        min2, max2 = project(vertices2, axis)
        if max1 < min2 or max2 < min1:
            return False
    return True

# 示例数据
x1, y1, x2, y2 = 0, 0, 1, 1
width = 0.2

# 计算矩形顶点
rect1_vertices = compute_rectangle_vertices(x1, y1, x2, y2, width)
rect2_vertices = compute_rectangle_vertices(x1 + 0.5, y1 + 0.5, x2 + 0.5, y2 + 0.5, width)

# 检查是否相交
collision = is_overlapping(rect1_vertices, rect2_vertices)
print("矩形相交:", collision)
