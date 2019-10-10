from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA


class MACD(QAStrategyCTABase):

    def on_bar(self, bar):
        print(bar)

        res = self.macd()

        print(res)

        if res.DIF[-1] > res.DEA[-1]:
            self.send_order('BUY', 'OPEN', price=bar['close'], volume=1)

    def macd(self,):
        return QA.QA_indicator_MACD(self.market_data)

    def risk_check(self):
        print(self.qifiacc.message)


if __name__ == '__main__':
    MACD(code='RB2001', frequence='1min').run()
