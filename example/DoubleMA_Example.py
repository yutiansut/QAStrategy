from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA
import pprint


class DMA(QAStrategyCTABase):

    def on_bar(self, bar):

        res = self.ma()

        print(res.iloc[-1])

        if res.MA2[-1] > res.MA5[-1]:

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

    def ma(self,):
        return QA.QA_indicator_MA(self.market_data, 2, 5)

    def risk_check(self):
        pass
        # pprint.pprint(self.qifiacc.message)


if __name__ == '__main__':
    DMA = DMA(code='rb2005', frequence='1min',
         strategy_id='1dd8b22d-7902-4a85-adb2-fbac4bb977fe', start='2019-10-01', end='2019-11-01') 
    DMA.run_backtest()
