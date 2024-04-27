import os
import pandas as pd
import numpy as np
from sklearn import preprocessing
import seaborn as sns
sns.set(color_codes=True)
import matplotlib.pyplot as plt
import os
import pandas as pd
import numpy as np
from sklearn import preprocessing
import seaborn as sns
sns.set(color_codes=True)
import matplotlib.pyplot as plt
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense
import tensorflow.keras as keras
#from keras.regularizers import regularizers

def denoise(t, x):
    # 1、数据预处理
    res = int(np.sqrt(len(x)))
    xr = x[:res * res]
    delay = t[:res * res]

    # 2、一维数组转换为二维矩阵
    x2list = []
    for i in range(res):
        x2list.append(xr[i * res:i * res + res])
    x2array = np.array(x2list)

    # 3、奇异值分解
    U, S, V = np.linalg.svd(x2array)
    S_list = list(S)
    ## 奇异值求和
    S_sum = sum(S)
    ##奇异值序列归一化
    S_normalization_list = [x / S_sum for x in S_list]

    # nengliang
    E = 0
    for i in range(len(S_list)):
        E = S_list[i] * S_list[i] + E

    p = []
    for i in range(0, len(S_list)):
        if i == len(S_list) - 1:
            p.append((S_list[i] * S_list[i]) / E)
        else:
            p.append(((S_list[i] * S_list[i]) - (S_list[i + 1] * S_list[i + 1])) / E)

    X = []
    for i in range(len(S_normalization_list)):
        X.append(i + 1)
    # fig3 = plt.figure(figsize=(15, 8)).add_subplot(111)
    # fig3.plot(X, p)
    # fig3.set_xticks(X)
    # fig3.set_xlabel('jieci', size=15)
    # fig3.set_ylabel('nengliangchafennpu', size=15)
    # plt.xticks(rotation=90, fontsize=10)
    # plt.show()

    # 4、画图
    X = []
    for i in range(len(S_normalization_list)):
        X.append(i + 1)

    # fig1 = plt.figure(figsize=(15, 8)).add_subplot(111)
    # fig1.plot(X, S_normalization_list)
    # fig1.set_xticks(X)
    # fig1.set_xlabel('Rank', size=10)
    # fig1.set_ylabel('Normalize singular values', size=15)
    # plt.xticks(rotation=90, fontsize=10)
    # plt.show()

    # 5、数据重构
    K = 5  ## 保留的奇异值阶数
    for i in range(len(S_list) - K):
        S_list[i + K] = 0.0

    S_new = np.mat(np.diag(S_list))
    reduceNoiseMat = np.array(U * S_new * V)
    reduceNoiseList = []
    for i in range(len(x2array)):
        for j in range(len(x2array)):
            reduceNoiseList.append(reduceNoiseMat[i][j])

    # 6、返回结果
    for i in range(len(reduceNoiseList)):
        if reduceNoiseList[i] < 0.0:
            reduceNoiseList[i] = 0

    return (delay, reduceNoiseList)