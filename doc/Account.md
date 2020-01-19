你需要注意的是, self.acc 在不同的模式下是不一样的

在回测模式: self.acc是一个实例化的 QUANTAXIS.QAAccountPro 类

在模拟模式: self.acc是一个实例化的 qifiaccount 账户


实时的账户的历史成交 self.acc.trade
回测的账户的历史成交 self.acc.history_table