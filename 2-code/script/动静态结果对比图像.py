# -*- coding: utf-8 -*-
"""
Created on Sun Sep  8 03:45:14 2024

@author: ASUS
"""

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 配置字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
# 生成示例数据
x =[2,3,4,5,6]
y = [0.42,0.42,0.4202,0.42021,0.420209]
y2=[0.44,0.448,0.4486,0.44869,0.448697]

# 特定的x坐标和显示的标签
x_positions = [2, 3, 4, 5, 6]
display_labels = ['0.01', '0.001', '0.0001', '0.00001', '0.000001']

# 创建图形和坐标轴
fig, ax = plt.subplots()

# 绘制数据
ax.plot(x, y, label='静态模型')
ax.plot(x, y2, label='动态模型', linestyle='--')

# 设置x轴刻度位置和标签
ax.set_xticks(x_positions)
ax.set_xticklabels(display_labels)

# 添加标题和标签
ax.set_title('动静态模型优化结果对比')
ax.set_xlabel('精度')
ax.set_ylabel('优化后的螺距参数')

# 添加图例
ax.legend()

# 显示图形
plt.show()
