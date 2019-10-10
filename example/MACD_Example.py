from QAStrategy import QAStrategyCTABase
import QUANTAXIS as QA

class MACD(QAStrategyCTABase):

    def on_bar(self, bar):
        print(bar)

    def macd(self,):
        return QA.QA_Indicator_MACD(self.market_data)

    