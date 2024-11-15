import os
import copy
import numpy as np
import pandas as pd 
import torch
from torch import nn, optim 
from torch.nn import functional as F 
import torchsummary


class Net(nn.Module):
    def __init__(self): 
        super().__init__()

        self.conv1 = nn.Sequential(
            nn.Conv2d(1, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128), 
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128), 
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128), 
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128), 
            nn.ReLU(),
        )      
        self.outlayer = nn.Conv2d(128, 1, kernel_size=5, stride=1, padding=0)

    def forward(self, x): # 反向传播
        x = self.conv1(x)
        x = torch.sigmoid(self.outlayer(x))
        x = x.view(-1, 1)

        return x

device = torch.device('cuda:0')
model = Net().to(device)
model.load_state_dict(torch.load(r'D:\M_L_Projrct\pythonProject\aiensitan\Grandmaster\Model\Model2.pkl',weights_only=True))
# print('-----------load model----------')
def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

# torchsummary.summary(model, (1, 5, 5))
# print('parameters_count:',count_parameters(model))
model.eval()
model.half()


def Mark(Board):
    """
    对棋盘状态进行评估，给出评估分数。

    该函数首先对棋盘状态进行预处理，然后使用一个预训练的模型进行评估。
    评估过程中，会将棋盘状态进行翻转并再次评估，以确保评估的对称性。

    参数:
    Board: 二维数组，表示棋盘状态。其中，-1代表对方棋子，0代表空位，1代表己方棋子。

    返回:
    评估分数，表示当前棋盘状态的优劣。
    """
    # 对棋盘状态进行预处理，将-0替换为0，并调整形状为(-1, 5, 5)
    Board = np.where(Board == -0, 0, Board).reshape(-1, 5, 5)

    # 禁用梯度计算，因为评估过程中不需要反向传播
    with torch.no_grad():
        # 将棋盘状态归一化，并转换为PyTorch张量
        x = Board / 6.
        x = torch.from_numpy(x)
        x = x.view(-1, 1, 5, 5).half()
        x = x.to(device)

        # 使用模型进行评估
        pred = model(x)
        pred = pred.cpu().numpy()

        # 对棋盘状态进行翻转并重新评估，以确保评估的对称性
        x = -np.flip(Board, [1, 2]) / 6.
        x = np.where(x == -0, 0, x)
        x = torch.from_numpy(x)
        x = x.view(-1, 1, 5, 5).half()
        x = x.to(device)
        pred_ = model(x)
        pred_ = pred_.cpu().numpy()

    # 将评估结果转换为单个分数
    try:
        pred = float(pred.reshape(-1))
        pred_ = 1 - float(pred_.reshape(-1))
    except:
        pred = pred.reshape(-1)
        pred_ = 1 - pred_.reshape(-1)

    # 返回平均评估分数
    return (pred + pred_) / 2


def RedMove(board, position, direction):
    x, y = position
    if direction == 0:
        board[x][y + 1] = board[x][y]
        board[x][y] = 0.
    elif direction == 1:
        board[x + 1][y] = board[x][y]
        board[x][y] = 0.
    elif direction == 2:
        board[x + 1][y + 1] = board[x][y]
        board[x][y] = 0.
    
    return board

def BlueMove(board, position, direction):
    x, y = position
    if direction == 0:
        board[x][y - 1] = board[x][y]
        board[x][y] = 0.
    elif direction == 1:
        board[x - 1][y] = board[x][y]
        board[x][y] = 0.
    elif direction == 2:
        board[x - 1][y - 1] = board[x][y]
        board[x][y] = 0.
    
    return board

def softmax(x):
    return np.exp(x)/sum(np.exp(x))

def Get_P(Board, MoveList): # 获取棋子走每个方向的获胜概率
    '''

    :param Board: 棋盘
    :param MoveList: 可移动列表
    :return: 获取棋子走每个方向的获胜概率
    '''
    x, y = MoveList[0][0]
    #print(Board)
    if Board[x][y] > 0:
        BoardList = []
        for position, direction in MoveList:
            BoardList.append(RedMove(copy.copy(Board), position, direction))
        Board_ = np.vstack(BoardList)
        Value = Mark(Board_)
        return softmax(Value)

    elif Board[x][y] < 0:
        BoardList = []
        for position, direction in MoveList:
            BoardList.append(BlueMove(copy.copy(Board), position, direction))
        Board_ = np.vstack(BoardList)
        Value = Mark(Board_)

        return softmax(1 - np.array(Value))

if __name__ == '__main__':
    pass

