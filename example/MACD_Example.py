from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA
import pprint


class MACD(QAStrategyCTABase):

    def on_bar(self, bar):

        res = self.macd()

        print(res)

        if res.DIF[-1] > res.DEA[-1]:
            if self.get_positions(self.code).volume_long == 0:
                self.send_order('BUY', 'OPEN', price=bar['close'], volume=1)

            if self.get_positions(self.code).volume_short > 0:
                self.send_order('SELL', 'CLOSE', price=bar['close'], volume=1)

        else:
            if self.get_positions(self.code).volume_short == 0:
                self.send_order('SELL', 'OPEN', price=bar['close'], volume=1)
            if self.get_positions(self.code).volume_long > 0:
                self.send_order('BUY', 'CLOSE', price=bar['close'], volume=1)

    def macd(self,):
        return QA.QA_indicator_MACD(self.market_data)

    def risk_check(self):

        pprint.pprint(self.qifiacc.message)


if __name__ == '__main__':
    MACD(code='RB2001', frequence='1min', strategy_id='1dd8b22d-7902-4a85-adb2-fbac4bb977fe').run()
