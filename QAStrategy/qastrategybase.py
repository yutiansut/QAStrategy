import datetime
import json
import os
import re
import sys
import threading
import time
import copy
import uuid

import pandas as pd
import pymongo
import requests
from qaenv import (eventmq_amqp, eventmq_ip, eventmq_password, eventmq_port,
                   eventmq_username, mongo_ip, mongo_uri)

import QUANTAXIS as QA
from QAPUBSUB.consumer import subscriber, subscriber_routing, subscriber_topic
from QAPUBSUB.producer import publisher_routing
from QAStrategy.util import QA_data_futuremin_resample
from QIFIAccount import ORDER_DIRECTION, QIFI_Account
from QUANTAXIS.QAARP import QA_Risk, QA_User
from QUANTAXIS.QAEngine.QAThreadEngine import QA_Thread
from QUANTAXIS.QAUtil.QAParameter import MARKET_TYPE, RUNNING_ENVIRONMENT


class QAStrategyCTABase():
    def __init__(self, code='rb1905', frequence='1min', strategy_id='QA_STRATEGY', risk_check_gap=1, portfolio='default',
                 start='2019-01-01', end='2019-10-21', init_cash=1000000, send_wx = False,
                 data_host=eventmq_ip, data_port=eventmq_port, data_user=eventmq_username, data_password=eventmq_password,
                 trade_host=eventmq_ip, trade_port=eventmq_port, trade_user=eventmq_username, trade_password=eventmq_password,
                 taskid=None, mongo_ip=mongo_ip):

        self.trade_host = trade_host

        self.code = code
        self.frequence = frequence
        self.strategy_id = strategy_id

        self.portfolio = portfolio

        self.data_host = data_host
        self.data_port = data_port
        self.data_user = data_user
        self.data_password = data_password
        self.trade_host = trade_host
        self.trade_port = trade_port
        self.trade_user = trade_user
        self.trade_password = trade_password

        self.start = start
        self.end = end
        self.init_cash = init_cash
        self.taskid = taskid

        self.running_time = ''

        self.market_preset = QA.QAARP.MARKET_PRESET()
        self._market_data = []
        self.risk_check_gap = risk_check_gap

        self.isupdate = False
        self.new_data = {}
        self._systemvar = {}
        self._signal = []
        self.send_wx = send_wx
        self.last_order_towards = {'BUY': '', 'SELL': ''}
        self.dt = ''
        if isinstance(self.code, str):
            self.market_type = MARKET_TYPE.FUTURE_CN if re.search(
                r'[a-zA-z]+', self.code) else MARKET_TYPE.STOCK_CN
        else:
            self.market_type = MARKET_TYPE.FUTURE_CN if re.search(
                r'[a-zA-z]+', self.code[0]) else MARKET_TYPE.STOCK_CN

        self.bar_order = {'BUY_OPEN': 0, 'SELL_OPEN': 0,
                          'BUY_CLOSE': 0, 'SELL_CLOSE': 0}

    @property
    def bar_id(self):
        return len(self._market_data)

    def _debug_sim(self):

        self.running_mode = 'sim'
        if self.frequence.endswith('min'):
            self._old_data = QA.QA_fetch_get_future_min('tdx', self.code.upper(), QA.QA_util_get_last_day(
                QA.QA_util_get_real_date(str(datetime.date.today()))), str(datetime.datetime.now()), self.frequence)[:-1].set_index(['datetime', 'code'])
            self._old_data = self._old_data.assign(volume=self._old_data.trade).loc[:, [
                'open', 'high', 'low', 'close', 'volume']]
        else:
            pass

        self.database = pymongo.MongoClient(mongo_ip).QAREALTIME

        self.client = self.database.account
        self.subscriber_client = self.database.subscribe

        self.acc = QIFI_Account(
            username=self.strategy_id, password=self.strategy_id, trade_host=mongo_ip, init_cash=self.init_cash)
        self.acc.initial()

        self.pub = publisher_routing(exchange='QAORDER_ROUTER', host=self.trade_host,
                                     port=self.trade_port, user=self.trade_user, password=self.trade_password)

        self.subscribe_data(self.code.lower(), self.frequence, self.data_host,
                            self.data_port, self.data_user, self.data_password)

        self.database.strategy_schedule.job_control.update(
            {'strategy_id': self.strategy_id},
            {'strategy_id': self.strategy_id, 'taskid': self.taskid,
             'filepath': os.path.abspath(__file__), 'status': 200}, upsert=True)

    def debug_sim(self):
        self._debug_sim()
        threading.Thread(target=self.sub.start, daemon=True).start()

    def run_sim(self):
        self._debug_sim()

        self.sub.start()

    def run_backtest(self):
        self.debug()
        self.acc.save()

        risk = QA_Risk(self.acc)
        risk.save()

        try:
            """add rank flow if exist

            QARank是我们内部用于评价策略ELO的库 此处并不影响正常使用
            """
            from QARank import QA_Rank
            QA_Rank(self.acc).send()
        except:
            pass

    def debug(self):
        self.running_mode = 'backtest'
        self.database = pymongo.MongoClient(mongo_ip).QUANTAXIS
        user = QA_User(username="admin", password='admin')
        port = user.new_portfolio(self.portfolio)
        self.acc = port.new_accountpro(
            account_cookie=self.strategy_id, init_cash=self.init_cash, market_type=self.market_type)
        self.positions = self.acc.get_position(self.code)

        print(self.acc)

        print(self.acc.market_type)
        data = QA.QA_quotation(self.code.upper(), self.start, self.end, source=QA.DATASOURCE.MONGO,
                               frequence=self.frequence, market=self.market_type, output=QA.OUTPUT_FORMAT.DATASTRUCT)

        def x1(item):
            # print(data)

            if str(item.name[0])[0:10] != str(self.running_time)[0:10]:
                self.on_dailyclose()
                self.on_dailyopen()
                if self.market_type == QA.MARKET_TYPE.STOCK_CN:
                    print('backtest: Settle!')
                    self.acc.settle()
            self._on_1min_bar()
            self._market_data.append(item)
            self.running_time = str(item.name[0])
            self.on_bar(item)

        data.data.apply(x1, axis=1)

    def subscribe_data(self, code, frequence, data_host, data_port, data_user, data_password):
        """[summary]

        Arguments:
            code {[type]} -- [description]
            frequence {[type]} -- [description]
        """

        self.sub = subscriber(exchange='realtime_{}_{}'.format(
            frequence, code), host=data_host, port=data_port, user=data_user, password=data_password)
        self.sub.callback = self.callback

    def subscribe_multi(self, codelist, frequence, data_host, data_port, data_user, data_password):

        self.sub = subscriber_topic(exchange='realtime_{}'.format(
            frequence), host=data_host, port=data_port, user=data_user, password=data_password)
        for item in codelist:
            self.sub.add_sub(exchange='realtime_{}'.format(
                frequence), routing_key=item)
        self.sub.callback = self.callback

    @property
    def old_data(self):
        return self._old_data

    def update(self):
        """
        此处是切换bar的时候的节点
        """
        self._old_data = self._market_data
        self._on_1min_bar()

    @property
    def market_datetime(self):
        return self.market_data.index.levels[0]

    @property
    def market_data(self):

        if self.running_mode == 'sim':
            return self._market_data
        elif self.running_mode == 'backtest':
            return pd.concat(self._market_data[-100:], axis=1, sort=False).T

    def force_close(self):
        # 强平
        if self.positions.volume_long > 0:
            self.send_order('SELL', 'CLOSE', price=self.positions.last_price,
                            volume=self.positions.volume_long)
        if self.positions.volume_short > 0:
            self.send_order('BUY', 'CLOSE', price=self.positions.last_price,
                            volume=self.positions.volume_short)

    def upcoming_data(self, new_bar):
        """upcoming_bar :

        Arguments:
            new_bar {json} -- [description]
        """
        self._market_data = pd.concat([self._old_data, new_bar])
        # QA.QA_util_log_info(self._market_data)

        if self.isupdate:
            self.update()
            self.isupdate = False

        self.update_account()
        self.positions.on_price_change(float(self.new_data['close']))
        self.on_bar(self.new_data)

    def ind2str(self, ind, ind_type):
        z = ind.tail(1).reset_index().to_dict(orient='records')[0]
        return json.dumps({'topic': ind_type, 'code': self.code, 'type': self.frequence, 'data': z})

    def callback(self, a, b, c, body):
        """在strategy的callback中,我们需要的是

        1. 更新数据
        2. 更新bar
        3. 更新策略状态
        4. 推送事件

        Arguments:
            a {[type]} -- [description]
            b {[type]} -- [description]
            c {[type]} -- [description]
            body {[type]} -- [description]
        """

        self.new_data = json.loads(str(body, encoding='utf-8'))

        if self.dt != str(self.new_data['datetime'])[0:16]:
            print('update!!!!!!!!!!!!')
            self.dt = str(self.new_data['datetime'])[0:16]
            self.isupdate = True

        self.acc.on_price_change(self.code, self.new_data['close'])
        # .loc[:, ['open', 'high', 'low', 'close', 'volume', 'tradetime']]
        bar = pd.DataFrame([self.new_data]).set_index(['datetime', 'code'])
        now = datetime.datetime.now()
        if now.hour == 20 and now.minute == 59 and now.second < 10:
            self.daily_func()
            time.sleep(10)

        # res = self.job_control.find_one(
        #     {'strategy_id': self.strategy_id, 'strategy_id': self.strategy_id})
        # self.control_status(res)
        self.running_time = self.new_data['datetime']
        self.upcoming_data(bar)

    def control_status(self, res):
        print(res)

    def add_subscriber(self, qaproid):
        """Add a subscriber
        增加订阅者的QAPRO_ID

        """
        self.subscriber_client.insert_one(
            {'strategy_id': self.strategy_id, 'user_id': qaproid})

    @property
    def subscriber_list(self):
        """订阅者

        Returns:
            [type] -- [description]
        """

        return list(set([item['user_id'] for item in self.subscriber_client.find({'strategy_id': self.strategy_id})]))

    def load_strategy(self):
        raise NotImplementedError

    def on_dailyopen(self):
        pass

    def on_dailyclose(self):
        pass

    def on_bar(self, bar):
        raise NotImplementedError

    def _on_1min_bar(self):
        #raise NotImplementedError
        if len(self._systemvar.keys()) > 0:
            self._signal.append(copy.deepcopy(self._systemvar))

    def on_1min_bar(self):
        raise NotImplementedError

    def on_5min_bar(self):
        raise NotImplementedError

    def on_15min_bar(self):
        raise NotImplementedError

    def on_30min_bar(self):
        raise NotImplementedError

    def order_handler(self):
        self._orders = {}

    def daily_func(self):
        QA.QA_util_log_info('DAILY FUNC')

    def risk_check(self):
        pass

    def plot(self, name, data, format):
        """ plot是可以存储你的临时信息的接口, 后期会接入可视化



        Arguments:
            name {[type]} -- [description]
            data {[type]} -- [description]
            format {[type]} -- [description]
        """
        self._systemvar[name] = {'datetime': copy.deepcopy(str(
            self.running_time)), 'value': data, 'format': format}

    def check_order(self, direction, offset):
        """[summary]
        同方向不开仓  只对期货市场做限制

        buy - open
        sell - close
        """
        if self.market_type == QA.MARKET_TYPE.FUTURE_CN:
            if self.last_order_towards[direction] == str(offset):
                return False
            else:
                return True
        else:
            return True

    def receive_simpledeal(self,
                           code: str,
                           trade_time,
                           trade_amount,
                           direction,
                           offset,
                           trade_price,
                           message='sell_open'):
        self.send_order(direction=direction, offset=offset,
                        volume=trade_amount, price=trade_price, order_id=QA.QA_util_random_with_topic(self.strategy_id))

    def send_order(self,  direction='BUY', offset='OPEN', price=3925, volume=10, order_id='',):

        towards = eval('ORDER_DIRECTION.{}_{}'.format(direction, offset))
        order_id = str(uuid.uuid4()) if order_id == '' else order_id

        if isinstance(price, float):
            pass
        elif isinstance(price, pd.Series):
            price = price.values[0]

        if self.running_mode == 'sim':

            QA.QA_util_log_info(
                '============ {} SEND ORDER =================='.format(order_id))
            QA.QA_util_log_info('direction{} offset {} price{} volume{}'.format(
                direction, offset, price, volume))

            if self.check_order(direction, offset):
                self.last_order_towards = {'BUY': '', 'SELL': ''}
                self.last_order_towards[direction] = offset
                now = str(datetime.datetime.now())

                order = self.acc.send_order(
                    code=self.code, towards=towards, price=price, amount=volume, order_id=order_id)
                order['topic'] = 'send_order'
                self.pub.pub(
                    json.dumps(order), routing_key=self.strategy_id)

                self.acc.make_deal(order)
                self.bar_order['{}_{}'.format(direction, offset)] = self.bar_id
                if self.send_wx:
                    for user in self.subscriber_list:
                        QA.QA_util_log_info(self.subscriber_list)
                        try:
                            "oL-C4w2WlfyZ1vHSAHLXb2gvqiMI"
                            """http://www.yutiansut.com/signal?user_id=oL-C4w1HjuPRqTIRcZUyYR0QcLzo&template=xiadan_report&\
                                        strategy_id=test1&realaccount=133496&code=rb1910&order_direction=BUY&\
                                        order_offset=OPEN&price=3600&volume=1&order_time=20190909
                            """

                            requests.post('http://www.yutiansut.com/signal?user_id={}&template={}&strategy_id={}&realaccount={}&code={}&order_direction={}&order_offset={}&price={}&volume={}&order_time={}'.format(
                                user, "xiadan_report", self.strategy_id, self.acc.user_id, self.code.lower(), direction, offset, price, volume, now))
                        except Exception as e:
                            QA.QA_util_log_info(e)

            else:
                QA.QA_util_log_info('failed in ORDER_CHECK')

        elif self.running_mode == 'backtest':

            self.bar_order['{}_{}'.format(direction, offset)] = self.bar_id

            self.acc.receive_simpledeal(
                code=self.code, trade_time=self.running_time, trade_towards=towards, trade_amount=volume, trade_price=price, order_id=order_id)
            self.positions = self.acc.get_position(self.code)

    def update_account(self):
        if self.running_mode == 'sim':
            QA.QA_util_log_info('{} UPDATE ACCOUNT'.format(
                str(datetime.datetime.now())))

            self.accounts = self.acc.account_msg
            self.orders = self.acc.orders
            self.positions = self.acc.get_position(self.code)
            self.trades = self.acc.trades
            self.updatetime = self.acc.dtstr
        elif self.running_mode == 'backtest':
            self.positions = self.acc.get_position(self.code)

    def get_exchange(self, code):
        return self.market_preset.get_exchange(code)

    def get_positions(self, code):
        if self.running_mode == 'sim':
            self.update_account()
            return self.positions
        elif self.running_mode == 'backtest':
            return self.acc.get_position(code)

    def get_cash(self):
        if self.running_mode == 'sim':
            self.update_account()
            return self.accounts.get('available', '')
        elif self.running_mode == 'backtest':
            return self.acc.cash_available

    def run(self):

        while True:
            time.sleep(self.risk_check_gap)
            self.risk_check()


if __name__ == '__main__':
    QAStrategyCTABase(code='rb2005').run()
