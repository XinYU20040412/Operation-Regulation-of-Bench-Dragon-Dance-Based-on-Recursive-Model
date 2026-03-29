# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 18:28:17 2024

@author: ASUS
"""
from scipy.optimize import fsolve

from math import sin,cos,pi,sqrt
k=1.7/(2*pi)
def theta(r):
    return r/k
def r_(theta):
    return theta*k
r0=4.5
theta_0=theta(r0)
ct=theta_0
x0,y0=r0*cos(theta_0),r0*sin(theta_0)
kk=-1*(cos(theta_0)-ct*sin(ct))/(sin(ct)+ct*cos(ct))
bb=r0*sin(ct)+r0*cos(ct)*(cos(theta_0)-ct*sin(ct))/(sin(ct)+ct*cos(ct))
d=abs(bb)/sqrt(1+k**2)
l2=2*sqrt(4.5**2-d**2)
r1=27/l2
r2=0.5*r1

def T(x):
    y=kk*x+bb
    return (y-y0)**2+(x-x0)**2-r1**2
initial_guess = 3
solution = fsolve(T, initial_guess)
x1 = solution[0]
y1=kk*x1+bb

def T2(x):
    y=kk*x+bb
    return (y-y0)**2+(x-x0)**2-r2**2
initial_guess = 3
solution = fsolve(T2, initial_guess)
x2 = solution[0]
y2=kk*x1+bb
x2=-x2
y2=-y2
print('圆心一为',(x1,y1))
print('圆心二为',(x2,y2))
def T3(x):
    y=(y0/x0)*x
    (y-y1)**2+(x-x1)**2-r1**2
initial_guess = 3
solution = fsolve(T3, initial_guess)
x3 = solution[0]
y3=(y0/x0)*x3
print('两圆切点为',(x3,y3))
dd1=sqrt((x3-x1)**2+(y3-y1)**2)
dd2=sqrt((x3-x2)**2+(y3-y2)**2)
print(dd1/dd2)
print(l2)