# QAStrategy
策略基类/ 基于QAAccount/QACEPEnging/QASPMS/QAREALTIMECollector/QATRADER

_QAStrategy支持[```QIFI```](http://github.com/quantaxis/qifi)协议_

> QAStrategy 的实盘使用天勤的下单网关(Open-Trade-Gateway) 如果是天勤的用户 你可以理解为这是另一个版本的tqsdk

> QAStrategy 的回测也兼容QUANTAXIS的QAAccount 以及QACommunity的可视化内容


QAStrategy 是QUANTAXIS 第一个面向交易员/策略开发者的 用户友好型项目, 致力于降低使用门槛和成本,
```快速编写/测试/模拟你的策略```

当你用QAStrategy写完一个回测 你可以无缝的把他直接改成一个实时模拟策略



QAStrategy 面向场景, 主要有3个策略基类


(PS: 股票日内回转(有底仓的情况) QAStrategy也一并支持, 默认给予10万股, 使用debug_t0()/run_backtestt0())

- QAStrategyCTABase  cta模板/ 单标的模板   支持股票/期货

- QAStrategyStockBase  股票池模板/ 多标的模板  支持股票/期货

- QAStrategyHedgeBase  对冲模板/ 双标的模板  (目前没写完)


策略开发者/交易员 只需要面向你自己的主要方向, 选择一个你想要的模板, 继承并开发即可快速在2分钟内完成一个简单策略


## 为什么使用QAStrategy

1. 你们根本不会用quantaxis 大部分人还停留在pandas都不会用的阶段 

2. quantaxis 项目过于灵活, 并且文档缺失较多 除非二次开发人员和我自己 都不推荐直接使用quantaxis

3. 你应该专注在策略开发上 而不是先学个python

4. QAStrategy是 无缝兼容回测/模拟/实盘的 你可以较为快速的直接上手

5. 支持QAStrategy的周边手机APP即将上线, QACommunity桌面端也是无缝兼容的


> 书生造反 十年不成  不要总是在想这个难那个不好用了 just do it  现在开始比什么都重要 !#

> 如果你在QAStrategy的过程中遇到了任何问题 都可以直接发issue要求群主给你解决!


## 如何使用QAStrategy

我们推荐你使用QUANTAXIS的docker环境来直接上手

如果你希望手动部署 可以参考QUANTAXIS项目中的issue  部署好行情网关 数据更新以及相应其他的设置(mq/db)


当你通过QUANTAXIS DOCKER打开了 81界面, 即可进入研究选项

QAStrategy是内置在本docker环境中的, 直接调用即可




在每个策略基类中 有一些是 大家共享的公共变量  还有一些是基类自己的变量

=====================================================================================

## varibles  一些变量

- self.market_data 此变量为公共变量 记录策略的历史数据 [回测/实时均可用]
- self.send_order 此函数为公共函数 但是在不同的基类中, 参数不同
- self.running_time  当前运行时间
- self.acc 此变量为公共变量 代表了账户
- self.market_datetime 
- self.bar_id  在回测中使用, 及bar的id数
- self.latest_price  一个json格式的最新价格变量  一般在实时模拟中使用
- self.isupdate
- self.dt  当前时间(datetime的缩写)


## 一些比较重要的变量[篇幅较长 在首页我就不展开讲 可以移步链接中的教程]

### [持仓Position](doc/Position.md)

### [账户 Account](doc/Account.md)

### [数据 MarketData](doc/MarketData.md)

### [订单 Order](doc/Order.md)










## functions  常用函数

- 画图函数 self.plot(name, data, format)
- 获取当前code self.get_code()
- self.ind2str(ind, ind_type)
- 获取品种所在的交易所  self.get_exchange(code)
- 获取品种持仓  self.get_positions(code)
- 获取当前现金 self.get_cash()
- 获取某个品种的marketdata  self.get_code_marketdata(code)
- 获取当前的maretdata切片 self.get_current_marketdata()


- 订阅数据 (实时模拟用/ 回测不需要) self.subscribe_data(code, frequence, data_host, data_port, data_user, data_password, model='py')
- 用当日tick数据进行回测(期货)  self.debug_currenttick(freq)
- 用历史tick数据进行回测(期货) self.debug_histick(freq)
- 使用t0模式进行回测  self.debug_t0()
- 回测(不存储账户数据的模式)  self.debug()
- 回测(存储账户数据的模式) self.run_backtest()
- 实时模拟(阻塞形式 不能同时多开很多个) self.run_sim()
- 实时模拟(非阻塞模式  可以同时开很多个)  self.debug_sim()

## inherit functions  常用继承函数 (一般来说 就是你需要自定义的函数)

用户初始化函数

```python
def user_init(self):
```

每日开盘前运行的函数 默认是自带的  你可以改写
```python
def on_dailyopen(self):
    pass
```

每日收盘后运行的函数 默认是自带的  你可以改写
```python
def on_dailyclose(self):
    pass
```

在你订阅分钟级别的数据的时候,  你需要继承并改写on_bar函数

```python
def on_bar(self, bar):

    print(bar)
```


在你订阅tick级别的数据的时候,  你需要继承并改写on_tick函数

```python
def on_tick(self, tick):
    pass
```


强制平仓函数 默认是自带的  你可以改写

```python
def force_close(self):
    pass
```


在发单后会运行的函数 默认是自带的  你可以改写
```python
def check_order(self, direction, offset, code= None):
    pass
```

当发单失败的时候运行的函数 默认是自带的  你可以改写

```python
def on_ordererror(self, direction, offset, price, volume):
    pass
```
=====================================================================================


一个常见的示例如下  更多的示例可以参考  /example 中的例子


```python

from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

class CCI(QAStrategyCTABase):
    def on_bar(self, bar):
        """你的大部分策略逻辑都是在此写的
        """
        res = self.cci()  
        print(res.iloc[-1])
        if res.CCI[-1] < -100:
            print('LONG')
            if self.positions.volume_long == 0:
                self.send_order('BUY', 'OPEN', price=bar['close'], volume=1)
            if self.positions.volume_short > 0:
                self.send_order('BUY', 'CLOSE', price=bar['close'], volume=1)

        elif res.CCI[-1] > 100:
            print('SHORT')
            if self.positions.volume_short == 0:
                self.send_order('SELL', 'OPEN', price=bar['close'], volume=1)
            if self.positions.volume_long > 0:
                self.send_order('SELL', 'CLOSE', price=bar['close'], volume=1)

    def cci(self,):
        """你可以自定义你想要的函数
        """
        return QA.QA_indicator_CCI(self.market_data, 61)


strategy = CCI(code='rb2005', frequence='1min',
                strategy_id='a3916de0-bd28-4b9c-bea1-94d91f1744ac')
strategy.run_backtest()

```

更多详细信息参考教程
