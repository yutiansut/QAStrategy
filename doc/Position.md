# Postions  关于你的持仓的一切

当我们开始写策略的时候, 必不可少的, 我们会跟持仓打交道, 

- 当行情变化的时候, 持仓的盈亏的计算(成本的统计视角)
- 当我们要平仓的时候, 持仓(今仓/昨仓)的判断
- 我们预估浮盈浮亏的时候, 对于仓位开仓的信号点进行的判断
- 我们进行对冲/对锁操作时, 对于双向开仓的需求

等等, 因此, QAPositions 就是面向这个需求来解决问题的, 我们把对于一个品种的持仓成为一个positions, 在一个position中你可以有开多和开空两种独立的状态

## 如何获取到持仓?

    你可以用
    
    ```python
    positions = self.get_position(code)
    ```

    在单标的基类中, 你可以直接调用 positions,  如果是多标的基类  会需要使用 self.acc.get_position(code)

    position 在回测/模拟中都是一样的  属于 QAPostion类


## 如何使用QAPosition?

    如果你需要查询当前的仓位:  positions.cur_vol  / positions.hold_detail

    如果你需要查询仓位的全部信息:  self.positons.static_message

    如果你需要知道详细的基于当前价格的动态信息:  self.position.realtime_message

    以下列出了一些你可以直接调用的信息, 这些信息在行情更新/下单成交的时候都已经自动计算好了

    ```python
    positions.volume_long  #当前持的多单

    positions.volume_short #当前持仓的空单数量

    positions.volume_long_today #今日多单数量

    positions.volume_long_his #今日多单数量

    positions.volume_short_today #今日空单数量

    positions.volume_short_his #今日空单数量

    positions.position_price_long  # 基于结算价计算的多头成本价

    positions.position_cost_long   # 基于结算价计算的多头总成本(总市值)

    positions.position_price_short  # 基于结算价计算的空头开仓均价

    positions.position_cost_short # 基于结算价计算的空头成本

    positions.open_price_long  # 基于开仓价计算的多头开仓价

    positions.open_cost_long  # 基于开仓价计算的多头开仓价

    positions.open_price_short  # 基于开仓价计算的多头开仓价空头开仓价

    positions.open_cost_short  # 基于开仓价计算的多头开仓价空头成本

    ```


## Position 原理是什么

    本质是QAPosition 属于 ```QUANTAXIS.QAMarket.QAPosition```


