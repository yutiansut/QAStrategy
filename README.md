# QAStrategy
策略基类/ 基于QAAccount/QACEPEnging/QASPMS/QAREALTIMECollector/QATRADER

_QAStrategy支持[```QIFI```](http://github.com/quantaxis/qifi)协议_



QAStrategy 是QUANTAXIS 第一个面向交易员/策略开发者的 用户友好型项目, 致力于降低使用门槛和成本,
```快速编写/测试/模拟你的策略```


当你用QAStrategy写完一个回测 你可以无缝的把他直接改成一个实时模拟策略



QAStrategy 面向场景, 主要有3个策略基类


(PS: 股票日内回转(有底仓的情况) QAStrategy也一并支持, 默认给予10万股, 使用debug_t0()/run_backtestt0())

- QAStrategyCTABase  cta模板/ 单标的模板   支持股票/期货

- QAStrategyStockBase  股票池模板/ 多标的模板  支持股票/期货

- QAStrategyHedgeBase  对冲模板/ 双标的模板  (目前没写完)


策略开发者/交易员 只需要面向你自己的主要方向, 选择一个你想要的模板, 继承并开发即可快速在2分钟内完成一个简单策略



在每个策略基类中 有一些是 大家共享的公共变量  还有一些是基类自己的变量

=====================================================================================

## varibles 

- self.market_data 此变量为公共变量 记录策略的历史数据 [回测/实时均可用]
- self.send_order 此函数为公共函数 但是在不同的基类中, 参数不同
- self.running_time
- self.acc 此变量为公共变量 代表了账户
- self.market_datetime
- self.bar_id
- self.latest_price
- self.isupdate

## functions
- def plot(self, name, data, format)
- def get_code(self):
- def ind2str(self, ind, ind_type)
- def get_exchange(self, code):
- def get_positions(self, code):
- def get_cash(self):
- def get_code_marketdata(self, code)
- def get_current_marketdata(self)
- def subscribe_data(self, code, frequence, data_host, data_port, data_user, data_password, model='py'):
- def debug_currenttick(self, freq):
- def debug_histick(self, freq):  
- def debug_t0(self)
- def debug(self):
- def run_backtest(self)
- def run_sim(self)
- def debug_sim(self)

## inhert functions

```python
def on_bar(self, bar):
    print(bar)
```
```python
def on_tick(self, tick):
    pass
```


```python
def force_close(self):
    pass
```


```python
def on_dailyopen(self):
    pass
```


```python
def on_dailyclose(self):
    pass
```

```python
def check_order(self, direction, offset, code= None):
    pass
```

```python
def on_ordererror(self, direction, offset, price, volume):
```

```python
def user_init(self):
```


=====================================================================================





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
