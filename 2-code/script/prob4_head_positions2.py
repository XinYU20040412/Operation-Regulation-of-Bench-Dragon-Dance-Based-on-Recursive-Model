# -*- coding: utf-8 -*-
"""
Created on Sat Sep  7 17:36:25 2024

@author: ASUS
"""

import numpy as np
import math
from math import pi
import seaborn as sns
import matplotlib.pyplot as plt
sns.set()
from math import pi, log, sqrt, cos, sin,atan
import numpy as np
from scipy.optimize import fsolve

k = 1.7/ (2 * pi)
C = 0.5 * k**2 * log(k)

def theta(r):
    return (r / k)-pi

def r_(theta_):
    return k * (theta_+pi)

#%%求各个时刻龙头位置
rB = 4.5
tB = (0.5 * (rB * sqrt(rB**2 + k**2) + k**2 * log(rB + sqrt(rB**2 + k**2))) - C) /k 

t_out= 11.446540388737732

t = [tB+i-t_out for i in range(12,101)]
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

x_head_position2,y_head_position2=x,y





























