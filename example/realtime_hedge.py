from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

class CCI(QAStrategyCTABase):



    def on_bar(self, bar):
        print(bar)
        current_code = bar['code']
        res = self.cci(current_code)


        if res.CCI[-1] < -100:
            if self.get_positions(current_code).volume_long == 0:
                self.send_order('BUY', 'OPEN', price=bar['close'], volume=1, code= current_code)
            if self.get_positions(current_code).volume_short > 0:
                self.send_order('BUY', 'CLOSE', price=bar['close'], volume=1, code= current_code)

        else:
            #print('SHORT')
            if self.get_positions(current_code).volume_short == 0:
                self.send_order('SELL', 'OPEN', price=bar['close'], volume=1, code= current_code)
            if self.get_positions(current_code).volume_long > 0:
                self.send_order('SELL', 'CLOSE', price=bar['close'], volume=1, code= current_code)

    def cci(self, code):


        market_data = self.get_code_marketdata(code)
        return QA.QA_indicator_CCI(market_data, 61)


if __name__ == '__main__':

    strategy = CCI(code=['rb2005', 'j2005'], frequence='1min', model='rust',
                   strategy_id='a3916de0-bx8-4b19c-bxxax1-94d91f1744ac', start='2019-10-01', end='2019-11-01')
    strategy.run_sim()