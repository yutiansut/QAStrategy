from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA
import pprint


class CCI(QAStrategyCTABase):

    def on_bar(self, bar):

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
        return QA.QA_indicator_CCI(self.market_data, 61)

    def risk_check(self):
        pass
        # pprint.pprint(self.qifiacc.message)


if __name__ == '__main__':
    CCI(code='RB2001', frequence='1min',
        strategy_id='a3916de0-bd28-4b9c-bea1-94d91f1744ac').run()
