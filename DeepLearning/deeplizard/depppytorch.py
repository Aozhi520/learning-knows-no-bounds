import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
import torchvision.transforms as transforms
import torch.optim as optim

torch.set_printoptions(linewidth=120) #Display option for output
torch.set_grad_enabled(True)  #Already on by default

from torch.utils.tensorboard import SummaryWriter

from itertools import product

class Network(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=6, kernel_size=5)
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=12, kernel_size=5)

        self.fc1 = nn.Linear(in_features=12*4*4, out_features=120)
        self.fc2 = nn.Linear(in_features=120, out_features=60)
        self.out = nn.Linear(in_features=60, out_features=10)

    def forward(self, t):
        # (1) input layer
        t = t

        # (2) hidden conv layer
        t = self.conv1(t)
        t = F.relu(t)
        t = F.max_pool2d(t, kernel_size=2, stride=2)

        # (3) hidden conv layer
        t = self.conv2(t)
        t = F.relu(t)
        t = F.max_pool2d(t, kernel_size=2, stride=2)

        # (4) hidden linear layer
        t = t.reshape(-1, 12 * 4 * 4)
        t = self.fc1(t)
        t = F.relu(t)

        # (5) hidden linear layer
        t = self.fc2(t)
        t = F.relu(t)

        # (6) output layer
        t = self.out(t)
        #t = F.softmax(t, dim=1)

        return t


def get_num_correct(pred,labels):
    return pred.argmax(dim=1).eq(labels).sum().item()


train_set = torchvision.datasets.FashionMNIST(
    root='./data',
    train=True, 
    download=True,
    transform=transforms.Compose([
        transforms.ToTensor()
    ])
)

#快速试验不同超参数并在tensorboard可视化
#创建超参数字典
parameters = dict(
    lr = [.01, .001]
    ,batch_size = [100, 1000]
    ,shuffle = [True, False]
)
#另一种表示字典的方式
# parameters = {
#     'lr': [0.01, 0.001]
#     ,'batch_size' : [100, 1000]
#     ,'shuffle': [True, False]
# }

#构建列表的列表
param_values = [v for v in parameters.values()]

#解包
for lr, batch_size, shuffle in product(*param_values):
    comment = f' batch_size={batch_size} lr={lr} shuffle={shuffle}'

    train_loader = torch.utils.data.DataLoader(train_set,
                                               batch_size,
                                               shuffle=shuffle)

    network = Network()

    optimizer = optim.Adam(network.parameters(), lr) 


    images,labels = next(iter(train_loader))
    grid = torchvision.utils.make_grid(images)

    #tensorboard
    tb = SummaryWriter(comment=comment)
    tb.add_image('image',grid)
    tb.add_graph(network,images)

    for epoch in range(7):
        print("epoch: ",epoch)
        train_epoch = 0
        train_corrcet = 0 #计算每个批次总共预测正确的数量
        total_loss = 0

        for batch in train_loader: #get batch
            images, labels = batch

            pred = network(images)
            loss = F.cross_entropy(pred, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
            train_epoch +=1

            total_loss += loss.item() * images.shape[0]  #获得更准确的total_loss值
            # total_loss += loss.item() * batch_size  #按预定义的batch_size值进行缩放是不准确的
            train_corrcet += get_num_correct(pred,labels)


        tb.add_scalar("Loss",total_loss,epoch)
        tb.add_scalar("Number Correct",train_corrcet,epoch)
        tb.add_scalar("Accuracy",train_corrcet/len(train_set),epoch)
    

        # tb.add_histogram("conv1.bias",network.conv1.bias,epoch)
        # tb.add_histogram("conv1.weight",network.conv1.weight,epoch)
        # tb.add_histogram(
        #         'conv1.weight.grad'
        #         ,network.conv1.weight.grad
        #         ,epoch
        # )

        print("train_epoch: ", train_epoch, " train_loss: ", loss.item() , " correct_accuracy: ", train_corrcet/len(train_set)) 


    tb.close()