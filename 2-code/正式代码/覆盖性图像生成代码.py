
"""
Created on Sat Sep  7 15:03:25 2024

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

def count_velocity(angles_front,angles_behind):
    velocitys=[1]
    for i in range(constant.num_chair):
        velocity_new=velocitys[i]*cos(angles_front[i])/cos(angles_behind[i])
        velocitys.append(velocity_new)
    return velocitys


#%%求夹角求速度

def calculate_tangent_slope(theta):
    """计算阿基米德螺线在给定角度处的切线斜率"""
    r =  k*theta
    dr_dtheta = k
    numerator = sin(theta) + theta * cos(theta)
    denominator = cos(theta) - theta * sin(theta)
    return numerator / denominator

def calculate_secant_slope( theta1, theta2):
    """计算通过阿基米德螺线上的两个点的割线斜率"""
    r1 =  k * theta1
    r2 =  k * theta2
    x1, y1 = r1 * cos(theta1), r1 * sin(theta1)
    x2, y2 = r2 * cos(theta2), r2 * sin(theta2)
    
    if x2 - x1 == 0:
        return np.inf  # 防止除以零的情况
    return (y2 - y1) / (x2 - x1)

def calculate_angle_between_lines(m1, m2):
    """计算两条线段斜率 m1 和 m2 之间的夹角"""
    tan_theta = abs((m2 - m1) / (1 + m1 * m2))
    return atan(tan_theta)

def main(r1,r2):
    
    a1=[]
    # 割线的两个端点角度
    theta1 = theta(r1) 
    theta2 =  theta(r2) 
    
    # 计算每个端点处的切线斜率
    m_t1 = calculate_tangent_slope( theta1)
    m_t2 = calculate_tangent_slope( theta2)
    
    # 计算割线斜率
    m_s = calculate_secant_slope(theta1, theta2)
    
    # 计算夹角
    angle1 = calculate_angle_between_lines(m_t1, m_s)
    angle2 = calculate_angle_between_lines(m_t2, m_s)
    
    # 将弧度转换为度
    a1.append(np.degrees(angle1))
    a1.append(np.degrees(angle2))
    return a1
#%%
a01_=[]
a02_=[]
a0_=[]
a11_=[]
a12_=[]
a1_=[]
alast1_=[]
alast2_=[]
alast_=[]
a100_1=[]
a100_2=[]
a100_=[]
for i in range(0,301):
    x_head=x[i]
    y_head=y[i]
    xs,ys,rs=count_position(x_head, y_head, constant)
    a_=[]
    for i in range(len(rs)-1):
        a1=main(rs[i],rs[i+1])
        a_.append(a1)
    a01=a_[0][0]
    a02=a_[0][1]
    a0_.append(a01-a02)
    a11=a_[1][0]
    a12=a_[1][1]
    a1_.append(a11-a12)
    alast1=a_[-1][0]
    alast2=a_[-1][1]
    alast_.append(alast1-alast2)
    a1001=a_[100][0]
    a1002=a_[100][1]
    a100_.append(a1001-a1002)
    a01_.append(a01)
    a02_.append(a02)
    a11_.append(a11)
    a12_.append(a12)
    alast1_.append(alast1)
    alast2_.append(alast2)
    a100_1.append(a1001)
    a100_2.append(a1002)

    

    
import matplotlib.pyplot as plt
import numpy as np



# 创建一个 2x2 的子图
fig, axs = plt.subplots(2, 2, figsize=(10, 8))

# 绘制第一个折线图
axs[0, 0].plot(a01_, 'r-')  # 'r-' 表示红色实线
axs[0, 0].plot(a02_, 'b-',alpha=0.6)
axs[0, 0].plot(a0_, 'g-')

axs[0, 0].set_title('head of dragon')

# 绘制第二个折线图
axs[0, 1].plot( a11_,'r-')  # 'g-' 表示绿色实线
axs[0, 1].plot( a12_,'b-',alpha=0.6)  # 'g-' 表示绿色实线
axs[0, 1].plot(a1_, 'g-')

axs[0, 1].set_title('body of dragon')

# 绘制第三个折线图
axs[1, 1].plot(alast1_, 'r-')  # 'b-' 表示蓝色实线
axs[1, 1].plot(alast1_, 'b-',alpha=0.6)
axs[1, 1].plot(alast_, 'g-')
axs[1, 1].set_title('tail of dragon')


# 绘制第四个折线图
axs[1, 0].plot(a100_1, 'r-')  # 'm-' 表示品红色实线
axs[1, 0].plot(a100_2, 'b-',alpha=0.6)  # 'm-' 表示品红色实线
axs[1, 0].plot(a100_, 'g-')
axs[1, 0].set_title('Middle of dragon')

# 自动调整子图参数
plt.tight_layout()
# 自动调整子图参数
plt.subplots_adjust(wspace=0.4, hspace=0.4)  # 增加水平和垂直间距
# 显示图形
plt.show()
