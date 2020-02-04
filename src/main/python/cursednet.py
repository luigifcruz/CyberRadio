import torch.nn as nn


class conv_block(nn.Module):

    def __init__(self, in_ch, out_ch):
        super(conv_block, self).__init__()

        self.conv = nn.Sequential(
            nn.Conv1d(in_ch, out_ch, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(out_ch),
            nn.Tanh())

    def forward(self, x):
        x = self.conv(x)
        return x


class CursedNet(nn.Module):

    def __init__(self, input_ch, output_ch):
        super(CursedNet, self).__init__()
        self.input_ch = input_ch
        self.output_ch = output_ch

        self.Maxpool1 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.Maxpool2 = nn.MaxPool1d(kernel_size=2, stride=2)
        self.Maxpool3 = nn.MaxPool1d(kernel_size=2, stride=2)

        self.Conv1 = conv_block(input_ch, 16)
        self.Conv2 = conv_block(16, 32)
        self.Conv3 = conv_block(32, 32)
        self.Conv4 = conv_block(32, 16)
        self.Conv5 = conv_block(16, 8)
        self.Conv6 = conv_block(8, 4)
        self.Conv7 = conv_block(4, 2)
        self.Conv8 = nn.Conv1d(2, output_ch, kernel_size=1,
                               stride=1, padding=0)

        self.tanh = nn.Tanh()

    def forward(self, x):
        e1 = self.Conv1(x)
        e1 = self.Conv2(e1)
        e1 = self.Conv3(e1)

        e2 = self.Maxpool1(e1)
        e2 = self.Conv4(e2)
        e2 = self.Conv5(e2)

        e3 = self.Maxpool2(e2)
        e3 = self.Conv6(e3)
        e3 = self.Conv7(e3)

        out = self.Maxpool2(e3)
        out = self.Conv8(out)
        out = self.tanh(out)

        return out
