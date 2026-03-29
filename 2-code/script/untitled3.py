# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 12:50:28 2024

@author: ASUS
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from math import pi, log, sqrt, cos, sin, atan, degrees


# Constants
k = 0.55 / (2 * pi)
C = 0.5 * k**2 * log(k)

def theta(r):
    return r / k

def r_(theta_):
    return k * theta_

def equation(r, t):
    return 0.5 * (r * sqrt(r**2 + k**2) + k**2 * log(r + sqrt(r**2 + k**2))) - k * t - C

# Calculate dragon head position over time
rA = r_(32 * pi)
tA = (0.5 * (rA * sqrt(rA**2 + k**2) + k**2 * log(rA + sqrt(rA**2 + k**2))) - C) / k
t = [tA - i for i in range(301)]

x, y, theta_ = [], [], []

for i in t:
    initial_guess = 1
    r = fsolve(equation, initial_guess, args=(i))[0]
    a = theta(r)
    x.append(r * cos(a))
    y.append(r * sin(a))
    theta_.append(a)



class Constant:
    def __init__(self):
        self.num_chair = 223
        self.d_head = 0.01 * (341 - 2 * 27.5)
        self.d_gen = 0.01 * (220 - 2 * 27.5)

constant = Constant()

def point_equation(delta_theta, x1, y1, r0, d):
    _, theta1 = xy_to_polar(x1, y1)
    theta2 = theta1 + delta_theta
    x2 = r0 * theta2 * cos(theta2) / (2 * pi)
    y2 = r0 * theta2 * sin(theta2) / (2 * pi)
    return (x1 - x2)**2 + (y1 - y2)**2 - d**2

def xy_to_polar(x, y):
    r0 = 0.55
    r = sqrt(x**2 + y**2)
    theta = 2 * pi * (r / r0)
    return r, theta

def count_position(x_head, y_head, constant):
    xs, ys, rs, r0 = [x_head], [y_head], [sqrt(x_head**2 + y_head**2)], 0.55
    for i in range(constant.num_chair):
        x, y = xs[i], ys[i]
        d = constant.d_head if i == 0 else constant.d_gen
        delta_theta = fsolve(point_equation, pi / 4, args=(x, y, r0, d))[0]
        _, theta1 = xy_to_polar(x, y)
        theta2 = theta1 + delta_theta
        xs.append(r0 * theta2 * cos(theta2) / (2 * pi))
        ys.append(r0 * theta2 * sin(theta2) / (2 * pi))
        rs.append(theta2 * r0 / (2 * pi))
    return xs, ys, rs

def calculate_tangent_slope(theta, a=0, b=0.55 / (2 * pi)):
    r = a + b * theta
    dr_dtheta = b
    numerator = sin(theta) + theta * cos(theta)
    denominator =  cos(theta) - theta * sin(theta)
    return numerator / denominator

def calculate_secant_slope(theta1, theta2, a=0, b=0.55 / (2 * pi)):
    r1 = a + b * theta1
    r2 = a + b * theta2
    x1, y1 = r1 * cos(theta1), r1 * sin(theta1)
    x2, y2 = r2 * cos(theta2), r2 * sin(theta2)
    return (y2 - y1) / (x2 - x1) if x2 - x1 != 0 else np.inf

def calculate_angle_between_lines(m1, m2):
    tan_theta = abs((m2 - m1) / (1 + m1 * m2))
    return atan(tan_theta)

def main(r1, r2):
    theta1 = theta(r1)
    theta2 = theta(r2)
    m_t1 = calculate_tangent_slope(theta1)
    m_t2 = calculate_tangent_slope(theta2)
    m_s = calculate_secant_slope(theta1, theta2)
    angle1 = calculate_angle_between_lines(m_t1, m_s)
    angle2 = calculate_angle_between_lines(m_t2, m_s)
    return degrees(angle1), degrees(angle2)

x_300 = x[-1]
y_300 = y[-1]
xs, ys, rs = count_position(x_300, y_300, constant)



# Calculate angles between tangent and secant lines
a_ = [main(rs[i], rs[i + 1]) for i in range(len(rs) - 1)]
print(a_)

a_frist=[]
a_last=[]
x=[i for i in range(0,301)]
for ti in range(0,301):
    x_ti=x[ti]
    y_ti=y[ti]
    xs,ys,rs=count_position(x_ti, y_ti, constant)
    
    
    a1,a2=main(rs[0],rs[1])
    a_frist.append(a1)
    a_last.append(a2)
    
    


plt.plot(a_frist,color='blue')
plt.plot(a_last,color='red')



plt.xlabel('经历时间',prop={'family': 'SimHei'})
plt.ylabel('切线与板夹角',prop={'family': 'SimHei'})
plt.title('同板各端点处螺线切线与板所在直线的夹角,',prop={'family': 'SimHei'})
plt.show()
