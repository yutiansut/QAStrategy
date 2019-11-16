# QAStrategy
策略基类/ 基于QAAccount/QACEPEnging/QASPMS/QAREALTIMECollector/QATRADER

_QAStrategy支持[```QIFI```](http://github.com/quantaxis/qifi)协议_



QAStrategy 是QUANTAXIS 第一个面向交易员/策略开发者的 用户友好型项目, 致力于降低使用门槛和成本,
```快速编写/测试/模拟你的策略```


QAStrategy 面向场景, 主要有3个策略基类


- QAStrategyCTABase  cta模板/ 单标的模板   支持股票/期货

- QAStrategyStockBase  股票池模板/ 多标的模板  支持股票/期货

- QAStrategyHedgeBase  对冲模板/ 双标的模板  (目前没写完)


策略开发者/交易员 只需要面向你自己的主要方向, 选择一个你想要的模板, 继承并开发即可快速在2分钟内完成一个简单策略



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
                self.send_order('SELL', 'CLOSE', price=bar['close'], volume=1)

        elif res.CCI[-1] > 100:
            print('SHORT')
            if self.positions.volume_short == 0:
                self.send_order('SELL', 'OPEN', price=bar['close'], volume=1)
            if self.positions.volume_long > 0:
                self.send_order('BUY', 'CLOSE', price=bar['close'], volume=1)

    def cci(self,):
        """你可以自定义你想要的函数
        """
        return QA.QA_indicator_CCI(self.market_data, 61)


strategy = CCI(code='RB2001', frequence='1min',
                strategy_id='a3916de0-bd28-4b9c-bea1-94d91f1744ac')
strategy.run_backtest()

```

更多详细信息参考教程