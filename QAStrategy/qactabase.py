import datetime
import json
import os
import sys
import threading
import time
import uuid

import pandas as pd
import pymongo
import requests

import QUANTAXIS as QA
from QAPUBSUB.consumer import subscriber, subscriber_routing
from QAPUBSUB.producer import publisher_routing
from QAStrategy.util import QA_data_futuremin_resample
from QUANTAXIS.QAARP import QA_User
from QUANTAXIS.QAEngine.QAThreadEngine import QA_Thread
from QUANTAXIS.QAUtil.QAParameter import MARKET_TYPE, RUNNING_ENVIRONMENT
from QIFIAccount import QIFI_Account, ORDER_DIRECTION


class QAStrategyCTABase():
    def __init__(self, code='rb1905', dtype='1min', strategy_id='QA_STRATEGY',
                 data_host='127.0.0.1', data_port=5672, data_user='admin', data_password='admin',
                 trade_host='127.0.0.1', trade_port=5672, trade_user='admin', trade_password='admin',
                 taskid=None, mongouri='mongodb://127.0.0.1:27017'):

        self.trade_host = trade_host

        self.xcode = code
        self.dtype = dtype

        self.market_preset = QA.QAARP.MARKET_PRESET()
        self._market_data = []

        self.strategy_id = strategy_id

        self.qifiacc = QIFI_Account(
            username=strategy_id, password=strategy_id, )

        self._old_data = QA.QA_fetch_get_future_min('tdx', code.upper(), QA.QA_util_get_last_day(
            QA.QA_util_get_real_date(str(datetime.date.today()))), str(datetime.datetime.now()), dtype).set_index(['datetime', 'code'])
        self._old_data = self._old_data.assign(volume=self._old_data.trade).loc[:, [
            'open', 'high', 'low', 'close', 'volume']]

        self.subscribe_data(code.lower(), dtype, data_host,
                            data_port, data_user, data_password)

        self.pub = publisher_routing(exchange='QAORDER_ROUTER', host=trade_host,
                                     port=trade_port, user=trade_user, password=trade_password)

        self.isupdate = False
        self.new_data = {}
        self.last_order_towards = {'BUY': '', 'SELL': ''}
        self.client = pymongo.MongoClient(mongouri).QAREALTIME.account
        self.subscriber_client = pymongo.MongoClient(
            mongouri).QAREALTIME.subscribe

        self.subscriber_client.insert_one(
            {'strategy_id': self.strategy_id, 'user_id': 'oL-C4w1HjuPRqTIRcZUyYR0QcLzo'})
        """需要一个单独的线程 daemon=True 更新账户
        
        """
        self.account_thread = threading.Thread(
            target=self.update_account, daemon=True)
        self.account_thread.start()

        """account 类

        account类的属性, 可以是独立账户/可以是子账户
        """

        self.job_control = pymongo.MongoClient(
            mongouri).QAREALTIME.strategy_schedule
        self.job_control.update(
            {'strategy_id': self.strategy_id},
            {'strategy_id': self.strategy_id, 'taskid': taskid,
             'filepath': os.path.abspath(__file__), 'status': 200}, upsert=True)

    def subscribe_data(self, code, dtype, data_host, data_port, data_user, data_password):
        """[summary]

        Arguments:
            code {[type]} -- [description]
            dtype {[type]} -- [description]
        """

        self.sub = subscriber(exchange='realtime_min_{}'.format(
            code), host=data_host, port=data_port, user=data_user, password=data_password)
        self.sub.callback = self.callback

    @property
    def old_data(self):
        return self._old_data

    def update(self):
        self._old_data = self._market_data
        self.on_1min_bar()

    @property
    def market_data(self):
        return self._market_data

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
        self.on_bar()

    def ind2str(self, ind, ind_type):
        z = ind.tail(1).reset_index().to_dict(orient='records')[0]
        return json.dumps({'topic': ind_type, 'code': self.xcode, 'type': self.dtype, 'data': z})

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

        if self.new_data['datetime'][-9:] == '00.000000':
            self.isupdate = True
        bar = pd.DataFrame([self.new_data]).set_index(['datetime', 'code']
                                                      ).loc[:, ['open', 'high', 'low', 'close', 'volume']]
        now = datetime.datetime.now()
        if now.hour == 20 and now.minute == 59 and now.second < 10:
            self.daily_func()
            time.sleep(10)

        res = self.job_control.find_one(
            {'strategy_id': self.strategy_id, 'strategy_id': self.strategy_id})
        self.control_status(res)

        self.upcoming_data(bar)

    def control_status(self, res):
        print(res)

    @property
    def subscriber_list(self):
        """订阅者

        Returns:
            [type] -- [description]
        """

        return list(set([item['user_id'] for item in self.subscriber_client.find({'strategy_id': self.strategy_id})]))

    def load_strategy(self):
        raise NotImplementedError

    def on_bar(self):
        raise NotImplementedError

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

    def check_order(self, direction, offset):
        """[summary]
        同方向不开仓

        buy - open
        sell - close
        """

        if self.last_order_towards[direction] == str(offset):
            return False
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

    def send_order(self,  direction='BUY', offset='OPEN', price=3925, volume=10, order_id=QA.QA_util_random_with_topic('WDRB_QA01')):
        QA.QA_util_log_info(
            '============ {} SEND ORDER =================='.format(order_id))
        QA.QA_util_log_info('direction{} offset {} price{} volume{}'.format(
            direction, offset, price, volume))

        if self.check_order(direction, offset):
            self.last_order_towards = {'BUY': '', 'SELL': ''}
            self.last_order_towards[direction] = offset
            now = str(datetime.datetime.now())

            towards = eval('ORDER_DIRECTION.{}_{}'.format(direction, offset))

            order = self.qifiacc.send_order(
                code=self.xcode, towards=towards, price=price, amount=volume, order_id=order_id)
            order['topic'] = 'send_order'
            self.pub.pub(
                json.dumps(order), routing_key=self.strategy_id)

            self.qifiacc.make_deal(order)

            try:
                for user in self.subscriber_list:
                    QA.QA_util_log_info(self.subscriber_list)

                    "oL-C4w2WlfyZ1vHSAHLXb2gvqiMI"
                    """http://www.yutiansut.com/signal?user_id=oL-C4w1HjuPRqTIRcZUyYR0QcLzo&template=xiadan_report&\
                                strategy_id=test1&realaccount=133496&code=rb1910&order_direction=BUY&\
                                order_offset=OPEN&price=3600&volume=1&order_time=20190909
                    """

                    requests.post('http://www.yutiansut.com/signal?user_id={}&template={}&\
                                strategy_id={}&realaccount={}&code={}&order_direction={}&\
                                order_offset={}&price={}&volume={}&order_time={}'.format(
                        user, "xiadan_report", self.strategy_id, self.strategy_id, self.xcode.lower(), direction, offset, price, volume, now))
            except Exception as e:
                QA.QA_util_log_info(e)

        else:
            QA.QA_util_log_info('failed in ORDER_CHECK')

    def update_account(self):
        QA.QA_util_log_info('{} UPDATE ACCOUNT'.format(
            str(datetime.datetime.now())))
        _t = self.client.find_one({'strategy_id': self.strategy_id})
        print(_t)
        self.accounts = _t['accounts']
        self.orders = _t['orders']
        self.positions = _t['positions']
        self.trades = _t['trades']
        self.updatetime = _t['updatetime']

    def get_exchange(self, code):
        return self.market_preset.get_exchange(code)

    def get_positions(self, code):
        self.update_account()
        return self.positions.get('{}.{}'.format(self.get_exchange(code), code.lower()), False)

    def get_cash(self):
        self.update_account()
        return self.accounts.get('available', '')

    def start(self):
        while True:
            self.sub.start()
