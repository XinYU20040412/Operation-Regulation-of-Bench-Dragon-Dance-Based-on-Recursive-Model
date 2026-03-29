# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 14:55:30 2024

@author: ASUS
"""

import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
from math import pi, log, sqrt, cos, sin
import numpy as np
from scipy.optimize import fsolve

def theta(r,p):#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    return r / k

def r_(theta_,p):
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    return k * theta_

#%%求龙身上点位置
class constant(object):
    def __init__(self):
        self.num_chair = 223
        self.d_head = 0.01 * (341 - 2 * 27.5)
        self.d_gen = 0.01 * (220 - 2 * 27.5)

constant = constant()

def point_equation(delta_theta,x1,y1,p,d):
    #选取点与上一位置点的距离差    pip install --upgrade numpy
    r0=p
    _,theta1=xy_to_polar(x1,y1,p)
    theta2=theta1+delta_theta
    x2=r0*theta2*cos(theta2)/(2*pi)
    y2=r0*theta2*sin(theta2)/(2*pi)
    distance=(x1-x2)**2+(y1-y2)**2
    return distance-d**2
def xy_to_polar(x, y,p):#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    r0 = p
    r = np.sqrt(x**2 + y**2)
    theta = 2 * pi * (r / r0)
    return r, theta

def count_position(x_head, y_head, constant,p):#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    xs, ys, rs, r0 = [x_head], [y_head], [sqrt(x_head**2 + y_head**2)], p
    for i in range(constant.num_chair):
        x, y = xs[i], ys[i]
        if i == 0:
            delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, constant.d_head),xtol=1e-10)
        else:
            delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, constant.d_gen),xtol=1e-10)
        delta_theta = delta_theta[0]  # 确保是标量
        _, theta1 = xy_to_polar(x, y,p)
        theta2 = theta1 + delta_theta
        x_new = r0 * theta2 * cos(theta2) / (2 * pi)
        y_new = r0 * theta2 * sin(theta2) / (2 * pi)
        xs.append(x_new)
        ys.append(y_new)
        rs.append(theta2 * r0 / (2 * pi))
    return xs, ys, rs


#%%碰撞模型

import geopandas as gpd
from shapely.geometry import Point, Polygon

def compute_rectangle_vertices(x1_, y1_, x2_, y2_,i ,width=0.3):#计算四个角点考虑了延伸和宽度
    if i ==0:
        k=(341-27.5)/(341-55)
    else:
        k=(220-27.5)/(220-55)
    x1=x2_-k*(x2_-x1_)
    y1=y2_-k*(y2_-y1_)
    x2=x1_+k*(x2_-x1_)
    y2=y1_+k*(y2_-y1_)
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

# 构建矩形对象
def juxin(p,i):
    p0,pf=p
    x1,y1=p0
    x2,y2=pf
    p1=compute_rectangle_vertices(x1, y1, x2, y2,i)[0]
    p2=compute_rectangle_vertices(x1, y1, x2, y2,i)[1]
    p3=compute_rectangle_vertices(x1, y1, x2, y2,i)[2]
    p4=compute_rectangle_vertices(x1, y1, x2, y2,i)[3]
    polygon = Polygon([p1,p2,p3,p4])
    return polygon
def p_(t,i,p):#i是第i节龙身的前把手,找把手坐标
    rA = r_(32 * pi,p)
    k = p / (2 * pi)
    C = 0.5 * k**2 * log(k)
    tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
    T=tA-t
    def equation(r, t=T):
        return 0.5 * (r * sqrt(r**2 + k**2) + k**2 * log(r + sqrt(r**2 + k**2))) - k * t - C

    initial_guess = 1
    solution = fsolve(equation, initial_guess,xtol=1e-10)
    r = solution[0]  
    a = theta(r,p)
    x0 = r * cos(a)
    y0 = r * sin(a)
    xs, ys, rs = count_position(x0, y0, constant,p)#生成龙身上的节点位置
    
    return [xs[i],ys[i]],[xs[i+1],ys[i+1]]

def decide(t,p):
    for i in range(0,10):
        for j in range(2,21): # 一定要跳过i+1，相邻的一定是重叠的
            i_=i+j
            ju1=juxin(p_(t,i,p),i)
            ju2=juxin(p_(t,i_,p),i_)
            if ju1.intersects(ju2):
                return 'T',i,i_
        return 'F'
p=0.4175
for i in range(0,55):
    a_=theta(4.5,p)
    xx=4.5*cos(a_)
    yy=4.5*sin(a_)
    xs,ys,rs=count_position(xx, yy, constant,p)
    
    rB=4.5
    rA=r_(32*pi,p)
    k=p/(2*pi)
    C = 0.5 * k**2 * log(k)
    tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
    tB= (0.5 * (rB * sqrt(rB**2 + k**2) + k**2 * log(rB + sqrt(rB**2 + k**2))) - C) / k
    for i in range(0,55):
        if decide(tA-tB,p)!='F':
            T,i,i_=decide(tA-tB,p)
            print('在p等于',p,'时','第',i,'节与','第',i_,'节碰撞')           
        p-=0.00001
        print(p)







