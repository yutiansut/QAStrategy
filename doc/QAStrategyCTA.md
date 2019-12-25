## 1. QAStrategyCTABase

QAStrategy是被设计成(起码我是这么想的)成 """支持股票期货/ 支持一个函数切换回测/模拟/SIM/实盘"""的基类

QAStrategyCTABase 是面向常见cta场景

    一般是期货场景/ 兼容股票

    -  单标的
    -  事件驱动
    -  不进行选股/ 大量的择时操作


### 1.1 如何使用QAStrategyCTABase:


1.  docker用户需要先拉起期货/股票的docker, 具体的区别见之前的教程:
	http://www.yutiansut.com:3000/topic/5dc5da7dc466af76e9e3bc5d
	
2. 非docker用户需要自行部署, 具体部署流程参见之前的教程
	https://github.com/QUANTAXIS/QUANTAXIS/issues/1349

简单来说, 使用QAStrategy 你需要两步

 -  搭建本地的行情推送服务器
 	  	回测环境  由QUANTAXIS 自身项目提供, 需要先手动save数据
 		模拟环境/实盘环境  由QAREALTIME_COllECTOR项目提供, 内置在docker
		SIM环境(随机tick/ 真实tick)  由QAREALTIME_COLLECTOR/ QARANDOM_PRICE 提供, 内置在docker

-  使用QAStrategy 提供行情流推送来的数据处理节点(策略)

### 1.2 一个简单的示例

```python
from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

class Strategy(QAStrategyCTABase):

    def on_bar(self, bar):
		print(bar)

s = Strategy(code='rb2005', frequence='1min', strategy_id= 'xxx1' ) 
s.debug_sim()

```
你可以看到 由这几行代码 你就可以实现一个realtime的实时模拟策略  当然 这个策略只干了一个事情, 就是当行情来的时候, 打印行情价格

当然, 如果这是个回测代码, 你需要继续指定下开始和结束时间


```python
from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

class Strategy(QAStrategyCTABase):

    def on_bar(self, bar):
		print(bar)

s = Strategy(code='rb2005', frequence='1min', strategy_id= 'xxx1', start='2019-10-01', end='2019-11-01') 
s.run_backtest()
```

你可以看到  当我们切换模式的时候, 策略主体并没有发生任何改变   如果当你已经理解了这个代码 我们可以逐步的往下介绍新的API给你



### 1.3 下单/行情/账户/指标 的常见API

为了降低理解难度, 方便你一步一步的理解这个QAStrategy, 我在最开始的时候, 并不会考虑介绍太多的api给你, 也不会讲述底层实现过程, 我希望你可以只知道5个函数你也能一样的写策略


- 当前策略时间点:  ```self.running_time```

- 下单:   ```self.send_order```

- 接受到的数据: ```self.market_data```

- 账户: ```self.acc``

    在这里, 账户的内容是非常多的, 此处并不细讲, 在后面逐步展开

    - 实时的账户的历史成交 ```self.acc.trade```
    - 回测的账户的历史成交 ```self.acc.history_table```

- 持仓:  ```self.poistions```

- 指标:  你可以直接使用QA_Indicator系列, 加载到self.market_data上



#### 1.3.1  下单函数 send_order

下单函数被设计的非常简单:

```self.send_order('BUY', 'OPEN', price=bar['close'], volume=1)```

只需要4个函数你就可以下单了, 当然 这个场景是CTABase的, 在多标的的stockbase中, 你还需要带上你的code 这个在当前不讨论



#### 1.3.2  接受到的行情数据  self.market_data

self.market_data 是一个惰性计算的函数(@property), 因此当你收到这个数据, 你需要先复制一份来使用

这是一个multiindex的 dataframe,  如果你熟悉QUANTAXIS的 QADataStruct, 你会非常熟悉, 因为multiindex可以方便的承载多个时间/多个标的的数据

```python

def on_bar(self, bar):
    market_data = self.market_data

    print(market_data)
```

#### 1.3.3 账户 self.acc

你需要注意的是, self.acc 在不同的模式下是不一样的

在回测模式:  self.acc是一个实例化的  QUANTAXIS.QAAccountPro 类

在模拟模式:  self.acc是一个实例化的  qifiaccount 账户



#### 1.3.4 持仓  self.positions

在单标的基类中, 你可以直接调用 self.positions,  如果是多标的基类  会需要使用 self.acc.get_position(code)

position 在回测/模拟中都是一样的  属于 QAPostion类


如果你需要查询当前的仓位:  self.positions.cur_vol  / self.positions.hold_detail

如果你需要查询仓位的全部信息:  self.positons.static_message

如果你需要知道详细的基于当前价格的动态信息:  self.position.realtime_message

以下列出了一些你可以直接调用的信息, 这些信息在行情更新/下单成交的时候都已经自动计算好了

```python
self.positions.volume_long  #当前持的多单

self.positions.volume_short #当前持仓的空单数量

self.positions.volume_long_today #今日多单数量

self.positions.volume_long_his #今日多单数量

self.positions.volume_short_today #今日空单数量

self.positions.volume_short_his #今日空单数量

self.positions.position_price_long  # 基于结算价计算的多头成本价

self.positions.position_cost_long   # 基于结算价计算的多头总成本(总市值)

self.positions.position_price_short  # 基于结算价计算的空头开仓均价

self.positions.position_cost_short # 基于结算价计算的空头成本

self.positions.open_price_long  # 基于开仓价计算的多头开仓价

self.positions.open_cost_long  # 基于开仓价计算的多头开仓价

self.positions.self.open_price_short  # 基于开仓价计算的多头开仓价空头开仓价

self.positions.open_cost_short  # 基于开仓价计算的多头开仓价空头成本

```


### 1.3.5 指标

让我们回归到上面的market_data, 我们来计算一个指标

```python

import QUANTAXIS as QA

def on_bar(self, bar):
    market_data = self.market_data

    print(market_data)

    print(QA.QA_Indicator_MACD(market_data, 12, 26, 9))
```