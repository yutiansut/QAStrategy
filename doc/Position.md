    你可以用self.get_position()
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