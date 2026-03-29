# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 09:04:13 2024

@author: ASUS
"""

import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
from math import pi, log, sqrt, cos, sin
import numpy as np
from scipy.optimize import fsolve

k = 0.55 / (2 * pi)
C = 0.5 * k**2 * log(k)

def theta(r):
    return r / k

def r_(theta_):
    return k * theta_

#%%求各个时刻龙头位置
rA = r_(32 * pi)
tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
t = [tA - i for i in range(0, 301)]
rr = []
x = []
y = []
theta_ = []

for i in t:
    def equation(r, t=i):
        return 0.5 * (r * sqrt(r**2 + k**2) + k**2 * log(r + sqrt(r**2 + k**2))) - k * t - C

    initial_guess = 1
    solution = fsolve(equation, initial_guess)
    r = solution[0]
    rr.append(r)
    a = theta(r)
    theta_.append(a)
    x0 = r * cos(a)
    y0 = r * sin(a)
    x.append(x0)
    y.append(y0)

# 画散点图
plt.plot(x, y, color='blue')
# 显示图形
plt.show()
#%%求龙身上点位置
class constant(object):
    def __init__(self):
        self.num_chair = 223
        self.d_head = 0.01 * (341 - 2 * 27.5)
        self.d_gen = 0.01 * (220 - 2 * 27.5)

constant = constant()

def point_equation(delta_theta,x1,y1,r0,d):
    #选取点与上一位置点的距离差
    _,theta1=xy_to_polar(x1,y1)
    theta2=theta1+delta_theta
    x2=r0*theta2*cos(theta2)/(2*pi)
    y2=r0*theta2*sin(theta2)/(2*pi)
    distance=(x1-x2)**2+(y1-y2)**2
    return distance-d**2
def xy_to_polar(x, y):
    r0 = 0.55
    r = np.sqrt(x**2 + y**2)
    theta = 2 * pi * (r / r0)
    return r, theta

def count_position(x_head, y_head, constant):
    xs, ys, rs, r0 = [x_head], [y_head], [sqrt(x_head**2 + y_head**2)], 0.55
    for i in range(constant.num_chair):
        x, y = xs[i], ys[i]
        if i == 0:
            delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, constant.d_head))
        else:
            delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, constant.d_gen))
        delta_theta = delta_theta[0]  # 确保是标量
        _, theta1 = xy_to_polar(x, y)
        theta2 = theta1 + delta_theta
        x_new = r0 * theta2 * cos(theta2) / (2 * pi)
        y_new = r0 * theta2 * sin(theta2) / (2 * pi)
        xs.append(x_new)
        ys.append(y_new)
        rs.append(theta2 * r0 / (2 * pi))
    return xs, ys, rs

x_now = x[-1]#300s时龙图
y_now = y[-1]
xs, ys, rs = count_position(x_now, y_now, constant)

plt.plot(xs,ys,color='red')
plt.show()
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
def p_(t,i):#i是第i节龙身的前把手,找把手坐标
    rA = r_(32 * pi)
    tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
    T=tA-t
    def equation(r, t=T):
        return 0.5 * (r * sqrt(r**2 + k**2) + k**2 * log(r + sqrt(r**2 + k**2))) - k * t - C

    initial_guess = 1
    solution = fsolve(equation, initial_guess)
    r = solution[0]  
    a = theta(r)
    x0 = r * cos(a)
    y0 = r * sin(a)
    xs, ys, rs = count_position(x0, y0, constant)#生成龙身上的节点位置
    
    return [xs[i],ys[i]],[xs[i+1],ys[i+1]]

def decide(t):
    for i in range(0,51):
        for j in range(2,51):#一定要跳过i+1，相邻的一定是重叠的
            i_=i+j
            ju1=juxin(p_(t,i),i)
            ju2=juxin(p_(t,i_),i_)
            if ju1.intersects(ju2):#intersects函数内置边界框测试与分离轴定理判断矩形是否相交
                return 'T',i,i_
        return 'F'

dt=0.01
tt=[]
for t in np.arange(412,414,dt):
    if decide(t)!='F':
        print('在',t,'秒撞上')
        a,b,c=decide(t)
        print('第{',b,'}节与第{',c,'}节撞上了')
        tt.append(t)
        break
print('碰撞时的龙头坐标(x,y)：',p_(tt[0],0)[0])

    




