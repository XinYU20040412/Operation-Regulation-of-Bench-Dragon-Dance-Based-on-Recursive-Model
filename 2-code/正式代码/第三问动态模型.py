# -*- coding: utf-8 -*-
"""
Created on Sat Sep  7 10:23:31 2024

@author: ASUS
"""


import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
from math import pi, log, sqrt, cos, sin
import numpy as np
from scipy.optimize import fsolve
from shapely.geometry import Polygon
import geopandas as gpd

class Constant:
    def __init__(self):
        self.num_chair = 223
        self.d_head = 0.01 * (341 - 2 * 27.5)
        self.d_gen = 0.01 * (220 - 2 * 27.5)

constant = Constant()

def theta(r, p):
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    return r / k

def r_(theta_, p):
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    return k * theta_

def point_equation(delta_theta, x1, y1, p, d):
    r0 = p
    _, theta1 = xy_to_polar(x1, y1, p)
    theta2 = theta1 + delta_theta
    x2 = r0 * theta2 * cos(theta2) / (2 * pi)
    y2 = r0 * theta2 * sin(theta2) / (2 * pi)
    distance = (x1 - x2)**2 + (y1 - y2)**2
    return distance - d**2

def xy_to_polar(x, y, p):
    r0 = p
    r = np.sqrt(x**2 + y**2)
    theta = 2 * pi * (r / r0)
    return r, theta

def count_position(x_head, y_head, constant, p):
    xs, ys, rs, r0 = [x_head], [y_head], [sqrt(x_head**2 + y_head**2)], p
    for i in range(constant.num_chair):
        x, y = xs[i], ys[i]
        if i == 0:
            delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, constant.d_head), xtol=1e-10)[0]
        else:
            delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, constant.d_gen), xtol=1e-10)[0]
        _, theta1 = xy_to_polar(x, y, p)
        theta2 = theta1 + delta_theta
        x_new = r0 * theta2 * cos(theta2) / (2 * pi)
        y_new = r0 * theta2 * sin(theta2) / (2 * pi)
        xs.append(x_new)
        ys.append(y_new)
        rs.append(theta2 * r0 / (2 * pi))
    return xs, ys, rs

def compute_rectangle_vertices(x1_, y1_, x2_, y2_, i, width=0.3):
    if i == 0:
        k = (341 - 27.5) / (341 - 55)
    else:
        k = (220 - 27.5) / (220 - 55)
    x1 = x2_ - k * (x2_ - x1_)
    y1 = y2_ - k * (y2_ - y1_)
    x2 = x1_ + k * (x2_ - x1_)
    y2 = y1_ + k * (y2_ - y1_)
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

def juxin(p, i):
    p0, pf = p
    x1, y1 = p0
    x2, y2 = pf
    vertices = compute_rectangle_vertices(x1, y1, x2, y2, i)
    polygon = Polygon(vertices)
    return polygon

def p_(t, i, p):
    rA = r_(32 * pi, p)
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
    T = tA - t
    
    def equation(r, t=T):
        return 0.5 * (r * sqrt(r**2 + k**2) + k**2 * log(r + sqrt(r**2 + k**2))) - k * t - C
    
    solution = fsolve(equation, 1, xtol=1e-10)
    r = solution[0]
    a = theta(r, p)
    x0 = r * cos(a)
    y0 = r * sin(a)
    xs, ys, rs = count_position(x0, y0, constant, p)
    
    return [xs[i], ys[i]], [xs[i + 1], ys[i + 1]]

def decide(t, p):
    for i in range(0, 10):
        for j in range(2, 28):
            i_ = i + j
            ju1 = juxin(p_(t, i, p), i)
            ju2 = juxin(p_(t, i_, p), i_)
            if ju1.intersects(ju2):
                return 'T', i, i_
    return 'F'
#%%动态模型如下
p = 0.448699#!!!
for _ in range(55):
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    rB = 4.5
    tB = (0.5 * (rB * sqrt(rB**2 + k**2) + k**2 * log(rB + sqrt(rB**2 + k**2))) - C) /k 
    
    rA = r_(32 * pi, p)
    tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
    tf=tA-tB
    print('运动到指定地点要花费时间（s）：',tf)
    dt=10#!!!
    t_=[i for i in np.arange(190,tf,dt)]
    
    tt=[]
    for t in t_:
        if decide(t,p)!='F':
            print('在',t,'秒撞上')
            a,b,c=decide(t,p)
            tt.append(t)
            print('螺距为：',p,'时','第{',b,'}节与第{',c,'}节撞上了','碰撞时的龙头坐标(x,y)：',p_(tt[0],0,p)[0])
            continue
        #print(t,p)
    
    p -= 0.000001#!!!
    print('p现在迭代减小')


















