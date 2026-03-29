# -*- coding: utf-8 -*-
"""
Created on Thu Sep  5 20:21:14 2024

@author: ASUS
"""
import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
from math import pi,log,sqrt,cos,sin
import numpy as np
from scipy.optimize import fsolve
k=0.55/(2*pi)
C=0.5*k**2*log(k)
#%%
def theta(r):#定义两个转换工具
    return r/k
def r_(theta_):
    return k*theta_

rA=r_(32*pi)  #初始时刻r
tA=(0.5*(rA*sqrt(rA**2+k**2)+k**2*log(rA+sqrt(rA**2+k**2)))-C)/k#求解顺序时刻A点对应
t=[tA-i for i in range(0,301)]
rr=[]
x=[]
y=[]
theta_=[]

for i in t:
    #求解龙头的每一个时刻的位置
    
    def equation(r,t=i):
        return 0.5*(r*sqrt(r**2+k**2)+k**2*log(r+sqrt(r**2+k**2)))-k*t-C

    # 使用 fsolve 查找方程的根
    initial_guess = 1  # 初始猜测值
    solution = fsolve(equation, initial_guess)
    r=solution[0]#极径
    rr.append(r)
    a=theta(r)#每个时刻的对应极角
    theta_.append(a)
    x0=r*cos(a)
    y0=r*sin(a)
    x.append(x0)
    y.append(y0)

# 画散点图
plt.plot(x, y,color='blue')
# 显示图形
plt.show()


#%%
class constant(object):
    def __init__(self):
        self.num_chair=223
        self.d_head=0.01*(341-2*27.5)
        self.d_gen=0.01*(220-2*27.5)
constant=constant()   
def point_equation(delta_theta,x1,y1,r0,d):
    #选取点与上一位置点的距离差
    _,theta1=xy_to_polar(x1,y1)
    theta2=theta1+pi/4
    x2=r0*theta2*cos(theta2)/(2*pi)
    y2=r0*theta2*sin(theta2)/(2*pi)
    distance=(x1-x2)**2+(y1-y2)**2
    return distance-d**2  
def xy_to_polar(x,y):
    r0=0.55
    r=np.sqrt(x**2+y**2)
    theta=2*pi*(r/r0)
    return r,theta
def count_position(x_head,y_head,constant):
    #得出每一点的位置(x,y,r)
    xs,ys,rs,r0=[x_head],[y_head],[sqrt(x_head**2+y_head**2)],0.55
    for i in range(constant.num_chair):
        x,y=xs[i],ys[i]
        if i==0:
            delta_theta=fsolve(point_equation, pi/4,args=(x,y,r0,constant.d_head))
        else:
            delta_theta=fsolve(point_equation, pi/4,args=(x,y,r0,constant.d_gen))
        _,theta1=xy_to_polar(x,y)
        theta2=theta1+delta_theta
        x_new=r0*theta2*cos(theta2)/(2*pi)
        y_new=r0*theta2*sin(theta2)/(2*pi)
        xs.append(x_new)
        ys.append(y_new)
        rs.append(theta2*r0/2*pi)
    return xs,ys,rs
    
x_now=x[-1]
y_now=y[-1]
xs,ys,rs=count_position(x_now,y_now,constant)

# 画散点图
plt.plot(xs, ys,color='red')
# 显示图形
plt.show()


    

