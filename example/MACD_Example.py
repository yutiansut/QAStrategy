import pprint

import QUANTAXIS as QA
from QAStrategy import QAStrategyCTABase


class MACD(QAStrategyCTABase):

    def on_bar(self, bar):

        res = self.macd()

        print(res.iloc[-1])

        if res.DIF[-1] > res.DEA[-1]:

            print('LONG')

            if self.positions.volume_long == 0:
                self.send_order('BUY', 'OPEN', price=bar['close'], volume=1)
            if self.positions.volume_short > 0:
                self.send_order('BUY', 'CLOSE', price=bar['close'], volume=1)

        else:
            print('SHORT')
            if self.positions.volume_short == 0:
                self.send_order('SELL', 'OPEN', price=bar['close'], volume=1)
            if self.positions.volume_long > 0:
                self.send_order('SELL', 'CLOSE', price=bar['close'], volume=1)

    def macd(self,):
        return QA.QA_indicator_MACD(self.market_data)

    def risk_check(self):
        pass
        # pprint.pprint(self.qifiacc.message)


if __name__ == '__main__':
    MACD = MACD(code='rb2005', frequence='1min', data_host='192.168.2.118', mongo_ip='192.168.2.118', trade_host='192.168.2.118', send_wx=True,
                strategy_id='1dds1s2d-7902-4a85-adb2-fbac4bb977fe', start='2019-10-01', end='2019-11-01', model= 'rust')
    MACD.run_sim()
