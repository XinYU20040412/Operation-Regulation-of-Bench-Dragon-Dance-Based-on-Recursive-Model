# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 08:09:00 2024

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
import matplotlib.pyplot as plt
from math import pi,sqrt,cos,sin,atan,tan,asin,acos
from scipy.optimize import fsolve
import numpy as np
from decimal import Decimal
from prob1 import constant
from prob4_head_positions2 import x_head_position2,y_head_position2
#from prob4_calc_r_boundary import r_boundary

def cot(angle):
    return 1/tan(angle)

class figurable_constant(object):
    #所有初始常量以及通过手工数学计算能算出的恒量
    def __init__(self,constant,v):
        self.d_head=constant.d_head
        self.d_gen=constant.d_gen
        self.num_chair=constant.num_chair
        self.r_head_boundary=4.67131999
        self.r_gen_boundary=4.67131999
        self.R=4.5
        self.r0=1.7
        self.v=v
        self.theta0=2*pi*self.R/self.r0-4*pi
        self.alpha=atan(self.R/(2*pi*self.r0))
        self.x_in=self.R*cos(self.theta0)
        self.y_in=self.R*sin(self.theta0)
        self.d_l1=abs(self.y_in-self.x_in*cot(self.theta0-self.alpha))/sqrt(1+cot(self.alpha-self.theta0)**2)
        self.d_l2=abs(self.y_in-self.x_in*tan(self.theta0-pi-self.alpha))/sqrt(1+tan(self.alpha-self.theta0)**2)
        self.l1=2*self.d_l2
        self.l2=2*self.d_l1
        self.r1=(self.l1**2+self.l2**2)/(3*self.l2)
        self.r2=self.r1/2
        self.gamma=pi-asin(2*self.l1*self.l2/(self.l1**2+self.l2**2))
        self.gamma1_head=2*asin(self.d_head/(2*self.r1))
        self.gamma2_head=2*asin(self.d_head/(2*self.r2))
        self.gamma1_gen=2*asin(self.d_gen/(2*self.r1))
        self.gamma2_gen=2*asin(self.d_gen/(2*self.r2))
        self.t1_head=self.gamma1_head*self.r1/self.v
        self.t2_head=self.gamma2_head*self.r2/self.v
        self.t1_gen=self.gamma1_gen*self.r1/self.v
        self.t2_gen=self.gamma2_gen*self.r2/self.v
        self.t1_l=self.gamma*self.r1/self.v
        self.t2_l=self.gamma*self.r2/self.v
        self.x_Oin=self.x_in+self.r1/sqrt(1+tan(self.theta0-self.alpha)**2)
        self.y_Oin=self.y_in+self.r1*tan(self.theta0-pi-self.alpha)/sqrt(1+tan(self.theta0-pi-self.alpha)**2)
        self.x_Oout=self.x_in-self.r1/sqrt(1+tan(self.theta0-self.alpha)**2)
        self.y_Oout=self.y_in-self.r1*tan(self.theta0-pi-self.alpha)/sqrt(1+tan(self.theta0-pi-self.alpha)**2)
        self.t_sum_turn_back=self.gamma*(self.r1+self.r2)/self.v

class circle_equation(object):
    #圆的参数方程对象
    def __init__(self,phi0,radius,velocity,x_O,y_O,t_center):
        self.phi0=phi0
        self.radius=radius
        self.velocity=velocity
        self.x_O=x_O
        self.y_O=y_O
        self.t_center=t_center
    
    def count_position_by_time(self,t):
        if t<=self.t_center:
            pass
        else:
            t=t-self.t_center
        x=self.radius*cos(self.radius*t/self.velocity+self.phi0)+self.x_O
        y=self.radius*sin(self.radius*t/self.velocity+self.phi0)+self.y_O
        return x,y
    
    def count_position_by_phase(self,phase):
        x=self.radius*cos(phase)+self.x_O
        y=self.radius*sin(phase)+self.y_O
        return x,y

class helice(object):
    def __init__(self,r0,phi0):
        self.r0=r0
        self.phi0=phi0
    
    def count_position_by_phase(self,phase):
        x=self.r0*(phase+self.phi0)*cos(phase)/(2*pi)
        y=self.r0*(phase+self.phi0)*sin(phase)/(2*pi)
        return x,y

#%%judge boundary condition
def judge_boundary(xi ,yi, constant, ishead, **kwargs):
    #theta_par_in_b3=constant.theta0-constant.alpha
    theta_par_in_b2=-constant.alpha+(pi-constant.theta0)+(pi-constant.gamma)
    theta_par_out_b2=constant.theta0-pi-constant.gamma-constant.alpha
    #theta_par_out_b1=constant.theta0-constant.alpha+constant.gamma
    r=sqrt(xi**2+yi**2)
    if ishead==1:
        if kwargs['t']==0:
            return 3 ,2
        elif 0<kwargs['t'] and kwargs['t']<=constant.t1_l:
            if kwargs['t']<constant.t1_head:
                return 3 ,1
            return 2 ,2
        elif constant.t1_l<kwargs['t'] and kwargs['t']-constant.t1_l<=constant.t2_l:
            if kwargs['t']-constant.t1_l<constant.t2_head:
                return 2 ,1
            return 1,2
        elif constant.r_head_boundary>r:
            return 1 ,1
        return 0,0
    else:
        if r>constant.r_gen_boundary and kwargs['last_boundary']==0:
            return 0 ,0
        elif r<constant.r_gen_boundary and kwargs['last_boundary']==0:
            return 1 ,1
        elif kwargs['last_boundary']==3:
            return kwargs['last_boundary'], 0
        elif theta_par_out_b2>kwargs['theta'] and kwargs['last_boundary']==1:
            return 2 ,1
        elif theta_par_in_b2<kwargs['theta'] and kwargs['last_boundary']==2:
            return 3 ,1
        return kwargs['last_boundary'], 0
            
#%%iteration to get next point
def point_equation(delta_theta, x, y, now_boundary, isboundary, d, equations):
    if now_boundary==0 or now_boundary==3:
        r=sqrt(x**2+y**2)
        if now_boundary==0:
            theta1=2*pi*r/constant.r0-pi
            theta2=theta1-delta_theta
            helice_out=equations['helice_out']
            x_new,y_new=helice_out.count_position_by_phase(theta2)
        elif now_boundary==3:
            theta1=2*pi*r/constant.r0
            theta2=theta1+delta_theta
            helice_in=equations['helice_in']
            x_new,y_new=helice_in.count_position_by_phase(theta2)
            
    elif now_boundary==1:
        if isboundary==1:
            circle_out=equations['circle_out']
            x_new,y_new=circle_out.count_position_by_phase(delta_theta)
    
    elif now_boundary==2:
        if isboundary==1:
            circle_in=equations['circle_in']
            x_new,y_new=circle_in.count_position_by_phase(delta_theta)

    distance=(x-x_new)**2+(y-y_new)**2
    return distance-d**2

def count_next_point_position( x, y, now_boundary, isboundary, equations, ishead, constant):

    if now_boundary==0 or now_boundary==3:#迭代新点在螺旋线上
        if now_boundary==0:
            theta1=2*pi*constant.R/constant.r0
            helice_out=equations['helice_out']
            if ishead==1:
                delta_theta=fsolve(point_equation, 0,args=(x,y,now_boundary,isboundary,constant.d_head,equations))
            else:
                delta_theta=fsolve(point_equation, 0,args=(x,y,now_boundary,isboundary,constant.d_gen,equations))
            x_next,y_next=helice_out.count_position_by_phase(theta1-delta_theta)
        
        elif now_boundary==3:
            theta1=2*pi*constant.R/constant.r0
            if isboundary==1:#边界三边界处理
                if ishead==1:
                    delta_theta=fsolve(point_equation, pi/12,args=(x,y,now_boundary,isboundary,constant.d_head,equations))
                else:
                    delta_theta=fsolve(point_equation, pi/12,args=(x,y,now_boundary,isboundary,constant.d_gen,equations))
            else:
                if ishead==1:
                    delta_theta=fsolve(point_equation, pi/12,args=(x,y,now_boundary,isboundary,constant.d_head,equations))
                else:
                    delta_theta=fsolve(point_equation, pi/12,args=(x,y,now_boundary,isboundary,constant.d_gen,equations))
            x_next,y_next=helice_in.count_position_by_phase(theta1+delta_theta)
        return x_next ,y_next
        
    elif now_boundary==1:
        circle_out=equations['circle_out']
        if isboundary==1:#边界一边界处理
            if ishead==1:
                delta_theta=fsolve(point_equation, 0,args=(x,y,now_boundary,isboundary,constant.d_head,equations))
            else:
                delta_theta=fsolve(point_equation, 0,args=(x,y,now_boundary,isboundary,constant.d_gen,equations))
            x_new,y_new=circle_out.count_position_by_phase(delta_theta)
    
    elif now_boundary==2:
        circle_in=equations['circle_in']
        if isboundary==1:#边界二边界处理
            if ishead==1:
                delta_theta=fsolve(point_equation, pi/2,args=(x,y,now_boundary,isboundary,constant.d_head,equations))
            else:
                delta_theta=fsolve(point_equation, pi/2,args=(x,y,now_boundary,isboundary,constant.d_gen,equations))
            x_new,y_new=circle_in.count_position_by_phase(delta_theta)
    return x_new,y_new,delta_theta
        
            
def count_position_all(x_head , y_head, t, constant, equations):#(t>0)
    #得出每一点的位置(x,y,r)
    circle_out=equations['circle_out']
    circle_in=equations['circle_in']
    xs,ys=[x_head],[y_head]
    thetas_cir_in,thetas_cir_out=[],[]
    boundarys=[]
    positions_moment=[x_head,y_head]
    for i in range(constant.num_chair):
        x,y=xs[i],ys[i]
        if i==0:
            now_boundary,isboundary_head=judge_boundary(x, y, constant, 1, t=t)
            if isboundary_head==1:
                boundarys.append(now_boundary-1)
            else:
                boundarys.append(now_boundary)
            if now_boundary==0 or now_boundary==3:
                x_new,y_new=count_next_point_position(x, y, now_boundary, isboundary_head, equations, 1, constant)
            else:#龙头在圆弧上
                if isboundary_head==1:
                    x_new,y_new,delta_theta=count_next_point_position(x, y, now_boundary, isboundary_head, equations, 1, constant)
                    if now_boundary==1:
                        thetas_cir_out.append(delta_theta)
                    elif now_boundary==2:
                        thetas_cir_in.append(delta_theta)
                else:
                    if now_boundary==1:
                        theta0=constant.v*(t-constant.t1_l)/constant.r0+circle_in.phi0
                        theta_new=theta0-constant.gamma2_head
                        x_new,y_new=circle_out.count_position_by_phase(theta_new)
                        thetas_cir_out.append(theta_new)
                    elif now_boundary==2:
                        theta0=-constant.v*t/constant.r0+circle_out.phi0
                        theta_new=theta0+constant.gamma1_head
                        x_new,y_new=circle_in.count_position_by_phase(theta_new)
                        thetas_cir_in.append(theta_new)
                    
        else:
            last_boundary=boundarys[-1]
            if last_boundary==0:
                now_boundary,isboundary=judge_boundary(x, y, constant, 0, last_boundary=last_boundary)
            else:
                if last_boundary==1:
                    theta=thetas_cir_out[-1]
                    now_boundary,isboundary=judge_boundary(x, y, constant, 0, last_boundary=last_boundary ,theta=theta)
                elif last_boundary==2:
                    theta=thetas_cir_in[-1]
                    now_boundary,isboundary=judge_boundary(x, y, constant, 0, last_boundary=last_boundary ,theta=theta)
                elif last_boundary==3:
                    now_boundary,isboundary=judge_boundary(x, y, constant, 0, last_boundary=last_boundary)
                    
            if now_boundary==0 or now_boundary==3:
                x_new,y_new=count_next_point_position(x, y, now_boundary, isboundary, equations, 0, constant)
            else:
                if isboundary==1:
                    x_new,y_new,delta_theta=count_next_point_position(x, y, now_boundary, isboundary, equations, 0, constant)
                    if now_boundary==1:
                        thetas_cir_out.append(delta_theta)
                    elif now_boundary==2:
                        thetas_cir_in.append(delta_theta)
                else:
                    if now_boundary==1:
                        theta_new=thetas_cir_out[-1]-constant.gamma2_gen
                        x_new,y_new=circle_out.count_position_by_phase(theta_new)
                        thetas_cir_out.append(theta_new)
                    elif now_boundary==2:
                        theta_new=thetas_cir_in[-1]+constant.gamma1_gen
                        x_new,y_new=circle_in.count_position_by_phase(theta_new)
                        thetas_cir_in.append(theta_new)
        boundarys.append(now_boundary)
        xs.append(x_new)
        ys.append(y_new)
        positions_moment.append(x_new)
        positions_moment.append(y_new)
    def ensure_numeric(lst):
        lst_rebuild=[]
        for i in lst:
            if type(i)==float:
                lst_rebuild.append(float(i))
            elif type(i)=='numpy.float64':
                lst_rebuild.append(Decimal('numpy_float'))     
        return lst_rebuild
    xs,ys,positions_moment = ensure_numeric(xs),ensure_numeric(ys),ensure_numeric(positions_moment)
    return xs,ys,boundarys,positions_moment

#%%计算速度


def count_angle(xs,ys,boundarys,constant):
    #计算每条凳子前端与后端与相应切线或者竖直直线的夹角
    def linear_para(x1,y1,x2,y2):#得出一般直线方程系数
        return y1-y2,x2-x1,x1*y2-x2*y1
    angles_front,angles_behind,r0=[],[],constant.r0
    for i in range(constant.num_chair):
        x1,x2,y1,y2=xs[i],xs[i+1],ys[i],ys[i+1]
        A,B,C=linear_para(xs[i],ys[i],xs[i+1],ys[i+1])
        if boundarys[i]==0:
            r1=sqrt(x1**2+y1**2)
            r2=sqrt(x2**2+y2**2)
            if boundarys[i+1]==1:
                alpha1=atan(1/(((2*pi*r1)/r0)+pi))
                beta=atan((A*tan(2*pi*r1/r0)-B)/(A+B*tan(2*pi*r1/r0)))
                angles_front.append(alpha1-beta)
                alpha2=acos(abs(A*constant.x_Oout+B*constant.y_Oout+C)/(sqrt(A**2+B**2)*constant.r2))
                angles_behind.append(alpha2)
            else:
                alpha1=atan(1/(((2*pi*r1)/r0)+pi))
                alpha2=atan(1/(((2*pi*r1)/r0)+pi))
                beta=atan((A*tan(2*pi*r1/r0)-B)/(A+B*tan(2*pi*r1/r0)))
                angles_front.append(abs(alpha1-beta))
                angles_behind.append(abs(alpha2-beta))
        elif boundarys[i]==1:
            if boundarys[i+1]==1:
                angles_front.append(0)
                angles_behind.append(0)
            else:
                alpha1=acos(abs(A*constant.x_Oout+B*constant.y_Oout+C)/(sqrt(A**2+B**2)*constant.r2))
                alpha2=acos(abs(A*constant.x_Oin+B*constant.y_Oin+C)/(sqrt(A**2+B**2)*constant.r1))
                angles_front.append(alpha1)
                angles_behind.append(alpha2)
        elif boundarys[i]==2:
            if boundarys[i+1]==2:
                angles_front.append(0)
                angles_behind.append(0)
            else:
                alpha1=acos(abs(A*constant.x_Oin+B*constant.y_Oin+C)/(sqrt(A**2+B**2)*constant.r1))
                alpha2=atan(r0/(2*pi*r2))
                beta2=atan((A*tan(2*pi*r2/r0)-B)/(A+B*tan(2*pi*r2/r0)))
                angles_front.append(alpha1)
                angles_behind.append(alpha2-beta2)
        elif boundarys[i]==3:
            alpha1=atan(r0/(2*pi*r1))
            alpha2=atan(r0/(2*pi*r2))
            beta1=atan((A*tan(2*pi*r1/r0)-B)/(A+B*tan(2*pi*r1/r0)))
            beta2=atan((A*tan(2*pi*r2/r0)-B)/(A+B*tan(2*pi*r2/r0)))
            angles_front.append(abs(alpha1-beta1))
            angles_behind.append(abs(alpha2-beta2))
    return angles_front,angles_behind

def count_velocity_all(angles_front,angles_behind):
    velocitys=[1]
    for i in range(constant.num_chair):
        velocity_new=velocitys[i]*cos(angles_front[i])/cos(angles_behind[i])
        velocitys.append(velocity_new)
    return velocitys

#%%main_code
v=1
constant=figurable_constant(constant,v)#传递变量参数
t_pan=constant.t_sum_turn_back
t_frist=int(t_pan)+1#判断时间的标准，进行判别什么时候输入什么参数
def dh(tt,v):#定义并且寻找进入盘出螺线的各个时刻龙头位置
    k = 1.7/ (2 * pi)
    C = 0.5 * k**2 * log(k)

    def theta(r):
        return (r / k)-pi

    def r_(theta_):
        return k * (theta_+pi)
    rB = 4.5
    tB = (0.5 * (rB * sqrt(rB**2 + k**2) + k**2 * log(rB + sqrt(rB**2 + k**2))) - C) /k *v
    t_out= t_pan#!!!
    t = tB+tt-t_out 
    def equation(r, t=t):
        return 0.5 * (r * sqrt(r**2 + k**2) + k**2 * log(r + sqrt(r**2 + k**2))) - k *v* t - C
    initial_guess = 1
    solution = fsolve(equation, initial_guess)
    r = solution[0]       
    a = theta(r)     
    x0 = r * cos(a)
    y0 = r * sin(a)
    return x0,y0
def head(t,v):#求解出任意时刻，任意速度的头位置
    if t>=t_pan:
        x_head,y_head=dh(t,v)
        return x_head,y_head
    else:
        #
        circle_in=circle_equation(constant.theta0-constant.alpha, constant.r1, -constant.v, constant.x_Oin, constant.y_Oin, constant.t1_l)
        circle_out=circle_equation(constant.theta0-pi-constant.gamma-constant.alpha, constant.r2, constant.v, constant.x_Oout, constant.y_Oout ,constant.t1_l)
        helice_in=helice(constant.r0,0)
        helice_out=helice(constant.r0,pi)
        equations={'circle_in':circle_in,'circle_out':circle_out,'helice_in':helice_in,'helice_out':helice_out}
        x_head,y_head=circle_in.count_position_by_time(t)
        #
        return x_head,y_head
def max_v_idex(t,v):
    #
    x_head,y_head=head(t,v)
    circle_in=circle_equation(constant.theta0-constant.alpha, constant.r1, -constant.v, constant.x_Oin, constant.y_Oin, constant.t1_l)
    circle_out=circle_equation(constant.theta0-pi-constant.gamma-constant.alpha, constant.r2, constant.v, constant.x_Oout, constant.y_Oout ,constant.t1_l)
    helice_in=helice(constant.r0,0)
    helice_out=helice(constant.r0,pi)
    equations={'circle_in':circle_in,'circle_out':circle_out,'helice_in':helice_in,'helice_out':helice_out}
    x_head,y_head=circle_in.count_position_by_time(t)
    #
    xs,ys,boundarys,positions=count_position_all(x_head , y_head, 0, constant, equations)
    b=boundarys
    idex=[]
    if b[0]==0:
        for i in range(len(b)):
            if b[i]==0 and b[i+1]==1:
                idex.append(i)
                idex.append(i+1)
            elif b[i]==1 and b[i+1]==2:
                idex.append(i+1)
            elif b[i]==2 and b[i+1]==3:
                idex.append(i+1)
                break
    elif b[0]==1:
        for i in range(len(b)):
            if b[i]==1 and b[i+1]==2:
                idex.append(i)
                idex.append(i+1)
            elif b[i]==2 and b[i+1]==3:
                idex.append(i+1)
    elif b[0]==2:
        for i in range(len(b)):
            if b[i]==2 and b[i+1]==3:
                idex.append(i)
                idex.append(i+1)
    return idex
def max_v(t,v):
    maxv=[]
    vv=count_velocity_all(angles_front,angles_behind)
    for i in max_v_idex(t,v):
        maxv.append(vv[i])
    return max(maxv)







for i in range(10):
    vv=[]
    dv=0.1
    dt=10#!!!
    for i in np.arange(0,101,dt):
        vv.append(max_v(i,v))
    max__v=max(vv)
    if max__v>2:
        print('速度为',v-dv,'时没超',v,'时超速了')
        break
    else:
        v+=dv
print('最大龙头速度为',v)
        
        
    
    
    
'''
circle_in=circle_equation(constant.theta0-constant.alpha, constant.r1, -constant.v, constant.x_Oin, constant.y_Oin, constant.t1_l)
circle_out=circle_equation(constant.theta0-pi-constant.gamma-constant.alpha, constant.r2, constant.v, constant.x_Oout, constant.y_Oout ,constant.t1_l)
helice_in=helice(constant.r0,0)
helice_out=helice(constant.r0,pi)
equations={'circle_in':circle_in,'circle_out':circle_out,'helice_in':helice_in,'helice_out':helice_out}
x_head,y_head=circle_in.count_position_by_time(1)
xs,ys,boundarys,positions=count_position_all(x_head , y_head, 0, constant, equations)
vs=count_velocity_all(count_angle(xs,ys,boundarys,constant))
'''
