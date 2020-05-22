from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA
import pprint

class CCI(QAStrategyCTABase):



    def on_bar(self, bar):

        res = self.cci()

        #print(res.iloc[-1])

        if res.CCI[-1] < -100:

            #print('LONG')

            if self.positions.volume_long == 0:
                self.send_order('BUY', 'OPEN', price=bar['close'], volume=1)

            if self.positions.volume_short > 0:
                self.send_order('BUY', 'CLOSE', price=bar['close'], volume=1)

        else:
            #print('SHORT')
            if self.positions.volume_short == 0:
                self.send_order('SELL', 'OPEN', price=bar['close'], volume=1)
            if self.positions.volume_long > 0:
                self.send_order('SELL', 'CLOSE', price=bar['close'], volume=1)

    def cci(self,):
        return QA.QA_indicator_CCI(self.market_data, 61)

    def risk_check(self):
        pass
        # pprint.pprint(self.qifiacc.message)


if __name__ == '__main__':

    strategy = CCI(code='RBL8', frequence='1min',
                   strategy_id='a3916de0-bx8-4b19c-bxxax1-94d91f1744ac', start='2020-01-01', end='2020-02-05') 

    """测试  一般在jupyter中用

    
    """
    import datetime
    t1 = datetime.datetime.now()
    strategy.debug()
    print(datetime.datetime.now() - t1)
    """
    
    之后你可以用strategy.acc.history_table 这些以前qa回测的东西来查看
    """

    """ 回测
    """
    # strategy.run_backtest()

    # """ 模拟
    # """
    # strategy = CCI(code='rb2005', frequence='1min',
    #                strategy_id='a3916de0-bd28-4b9c-bea1-94d91f1744ac', send_wx=True,)
    # strategy.debug_sim()
    # strategy.add_subscriber("你的wechatid 在QARPO中获取")

    """debugsim是非阻塞的
    
    在进程中 用run_sim
    """

