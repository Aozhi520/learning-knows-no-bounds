import torch
from IPython import display
from d2l import torch as d2l
# import matplotlib.pyplot as plt
# plt.ion()


batch_size = 256
train_iter, test_iter = d2l.load_data_fashion_mnist(batch_size)

# 模型参数初始化
num_input = 784
num_output = 10

W = torch.normal(0, 0.01, size=(num_input, num_output), requires_grad=True)
b = torch.zeros(num_output, requires_grad=True)

# softmax
def softmax(X):
    X_exp = torch.exp(X)
    line_exp = X_exp.sum(1, keepdims = True)
    return X_exp / line_exp #line_exp的每一行元素都广播成同一元素

# 网络模型
def net(X):
    return softmax(torch.matmul(X.reshape(-1, W.shape[0]), W) + b ) #得把数据集reshape成(batch_size, num_input)形状
    #y_hat shape:[batch_size, num_output]

# 交叉熵损失函数
def cross_entropy(y_hat, y):
    return - torch.log(y_hat[range(len(y_hat)), y]) # 不需要乘y

#分类精度 

def accuracy(y_hat, y):
    """计算单样本中预测正确的数量"""
    y_hat_argmax = y_hat.argmax(dim=1)
    cmp = y_hat_argmax.type(y.dtype) == y
    return float(cmp.sum())   #要用float把tensor形式转化为python的float形式


class Accumulator:
    def __init__(self, n):
        self.data = [0.0] * n            
    
    def add(self, *args):
        self.data = [a + float(b) for a,b in zip(self.data, args)]  #关键：zip配对
        
    def __getitem__(self, idx):
        return self.data[idx]

def evaluate_accuracy(net, test_iter):
    """计算在指定数据集上模型的精度"""
    # 将模型设置为评估模式
    if isinstance(net, torch.nn.Module):
        net.eval()
    # Accumulator类储存正确预测数、预测总数
    accum = Accumulator(2)
    # 累加所有数据集的正确预测数、预测总数
    with torch.no_grad():   #因为调用了神经网络实例net，所以禁用梯度计算
        for X, y in test_iter:
            accum.add(accuracy(net(X), y), y.numel()) #不能用len(y)
    
    return accum[0] / accum[1]


# 绘图
class Animator:  #@save
    """在动画中绘制数据"""
    def __init__(self, xlabel=None, ylabel=None, legend=None, xlim=None,
                 ylim=None, xscale='linear', yscale='linear',
                 fmts=('-', 'm--', 'g-.', 'r:'), nrows=1, ncols=1,
                 figsize=(3.5, 2.5)):
        # 增量地绘制多条线
        if legend is None:
            legend = []
        d2l.use_svg_display()
        self.fig, self.axes = d2l.plt.subplots(nrows, ncols, figsize=figsize)
        if nrows * ncols == 1:
            self.axes = [self.axes, ]
        # 使用lambda函数捕获参数
        self.config_axes = lambda: d2l.set_axes(
            self.axes[0], xlabel, ylabel, xlim, ylim, xscale, yscale, legend)
        self.X, self.Y, self.fmts = None, None, fmts

    def add(self, x, y):
        # 向图表中添加多个数据点
        if not hasattr(y, "__len__"):
            y = [y]
        n = len(y)
        if not hasattr(x, "__len__"):
            x = [x] * n
        if not self.X:
            self.X = [[] for _ in range(n)]
        if not self.Y:
            self.Y = [[] for _ in range(n)]
        for i, (a, b) in enumerate(zip(x, y)):
            if a is not None and b is not None:
                self.X[i].append(a)
                self.Y[i].append(b)
        self.axes[0].cla()
        for x, y, fmt in zip(self.X, self.Y, self.fmts):
            self.axes[0].plot(x, y, fmt)
        self.config_axes()
        display.display(self.fig)
        display.clear_output(wait=True)



# 训练
def train_epoch_ch3(net, train_iter, loss, updater):
    """训练模型一个迭代周期"""
    # 将模型设置为训练模式
    if isinstance(net, torch.nn.Module):
        net.train()
    # 增加变量用于储存训练损失总和、训练准确的样本总和、样本数
    matric = Accumulator(3)
    # 训练
    for X, y in train_iter:
        #loss
        y_hat = net(X)
        Loss = loss(y_hat, y)
        #梯度下降   
        if isinstance(updater, torch.optim.Optimizer):
            # 使用PyTorch内置的优化器和损失函数
            updater.zero_grad()
            Loss.mean().backward()   #先取均值再反向传播
            updater.step()
            
        else:
            # 使用定制的优化器和损失函数
            Loss.sum().backward()
            # Loss.sum().backward()
            updater(batch_size)

        matric.add(Loss.sum(), accuracy(y_hat, y), y.numel())        

    # 返回累加后的训练损失和训练精度
    return matric[0] / matric[2], matric[1] / matric[2]


def train_ch3(net, train_iter, test_iter, loss, num_epochs, updater):
    #抄可视化
    animator = Animator(xlabel='epoch', xlim=[1, num_epochs], ylim=[0.3, 0.9],
                        legend=['train loss', 'train acc', 'test acc'])
    
    # 训练
    for epoch in range(num_epochs):
        matric = train_epoch_ch3(net, train_iter, loss, updater)
        test_acc = evaluate_accuracy(net, test_iter)
        animator.add(epoch + 1, matric )
    loss_sum, train_acc = matric


# sgd
lr = 0.1

def updater(batch_size):
    return d2l.sgd([W, b], lr, batch_size)


# start
num_epochs = 10
train_ch3(net, train_iter, test_iter, cross_entropy, num_epochs, updater)
