from QUANTAXIS.QAARP import QA_User
from QUANTAXIS.QAUtil.QAParameter import RUNNING_ENVIRONMENT
from QUANTAXIS.QAEngine.QAThreadEngine import QA_Thread


class QAStrategy(QA_Thread):
    def __init__(self, user, password, portfolio,
                 account_cookie, market_type, init_cash,
                 running_environment=RUNNING_ENVIRONMENT.BACKETEST,
                 *arg, **kwargs):
        """
        """

        self.user = QA_User(username=user, password=password)
        self.portfolio = self.user.new_portfolio(portfolio)

        if running_environment == RUNNING_ENVIRONMENT.BACKETEST:
            self.account = self.portfolio.new_account(
                account_cookie=account_cookie, init_cash=init_cash, market_type=market_type)
        else:
            self.account = self.portfolio.new_account(
                account_cookie=account_cookie, init_cash=init_cash, market_type=market_type, auto_reload=True)

    def on_bar(self, data):
        pass

    def on_tick(self, data):
        pass
