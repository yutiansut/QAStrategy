from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

class CCI(QAStrategyCTABase):



    def on_tick(self, tick):
        print(tick)

    def cci(self, code):


        market_data = self.get_code_marketdata(code)
        return QA.QA_indicator_CCI(market_data, 61)


if __name__ == '__main__':

    strategy = CCI(code=['au2006', 'ag2002'], frequence='tick', model='rust',
                   strategy_id='a3916de0-bx8-4b19c-bxxax1-94d91f1744ac', start='2019-10-01', end='2019-11-01')
    strategy.run_sim()