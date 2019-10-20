import datetime
import json
import os
import re
import sys
import threading
import time
import uuid

import pandas as pd
import pymongo
import requests
from qaenv import (eventmq_amqp, eventmq_ip, eventmq_password, eventmq_port,
                   eventmq_username, mongo_ip, mongo_uri)

import QUANTAXIS as QA
from QAPUBSUB.consumer import subscriber, subscriber_routing
from QAPUBSUB.producer import publisher_routing
from QAStrategy.util import QA_data_futuremin_resample
from QIFIAccount import ORDER_DIRECTION, QIFI_Account
from QUANTAXIS.QAARP import QA_Risk, QA_User
from QUANTAXIS.QAEngine.QAThreadEngine import QA_Thread
from QUANTAXIS.QAUtil.QAParameter import MARKET_TYPE, RUNNING_ENVIRONMENT


class QAStrategyCTABase():
    def __init__(self, code='rb1905', frequence='1min', strategy_id='QA_STRATEGY', risk_check_gap=1, portfolio='default',
                 start='2019-01-01', end='2019-10-21',
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

        self.taskid = taskid

        self.running_time = ''

        self.market_preset = QA.QAARP.MARKET_PRESET()
        self._market_data = []
        self.risk_check_gap = risk_check_gap

        self.isupdate = False
        self.new_data = {}
        self.last_order_towards = {'BUY': '', 'SELL': ''}

        self.market_type = MARKET_TYPE.FUTURE_CN if re.search(
            r'[a-zA-z]+', self.code) else MARKET_TYPE.STOCK_CN

    def run_sim(self):
        self.running_mode = 'sim'

        self._old_data = QA.QA_fetch_get_future_min('tdx', self.code.upper(), QA.QA_util_get_last_day(
            QA.QA_util_get_real_date(str(datetime.date.today()))), str(datetime.datetime.now()), self.frequence).set_index(['datetime', 'code'])
        self._old_data = self._old_data.assign(volume=self._old_data.trade).loc[:, [
            'open', 'high', 'low', 'close', 'volume']]

        self.database = pymongo.MongoClient(mongo_ip).QAREALTIME

        self.client = self.database.account
        self.subscriber_client = self.database.subscribe

        self.acc = QIFI_Account(
            username=self.strategy_id, password=self.strategy_id, trade_host=mongo_ip)
        self.acc.initial()

        self.pub = publisher_routing(exchange='QAORDER_ROUTER', host=self.trade_host,
                                     port=self.trade_port, user=self.trade_user, password=self.trade_password)

        self.subscribe_data(self.code.lower(), self.frequence, self.data_host,
                            self.data_port, self.data_user, self.data_password)

        self.add_subscriber('oL-C4w1HjuPRqTIRcZUyYR0QcLzo')
        self.database.strategy_schedule.job_control.update(
            {'strategy_id': self.strategy_id},
            {'strategy_id': self.strategy_id, 'taskid': self.taskid,
             'filepath': os.path.abspath(__file__), 'status': 200}, upsert=True)

        threading.Thread(target=self.sub.start, daemon=True).start()

    def run_backtest(self):
        self.debug()
        self.acc.save()

        risk = QA_Risk(self.acc)
        risk.save()

    def debug(self):
        self.running_mode = 'backtest'
        self.database = pymongo.MongoClient(mongo_ip).QUANTAXIS
        user = QA_User(username="admin", password='admin')
        port = user.new_portfolio(self.portfolio)
        self.acc = port.new_accountpro(
            account_cookie=self.strategy_id, init_cash=1000000, market_type= self.market_type)
        self.positions = self.acc.get_position(self.code)

        print(self.acc)

        print(self.acc.market_type)
        data = QA.QA_quotation(self.code.upper(), self.start, self.end, source=QA.DATASOURCE.MONGO,
                               frequence=self.frequence, market=self.market_type, output=QA.OUTPUT_FORMAT.DATASTRUCT)

        for _, item in data.data.reset_index().iterrows():
            self.running_time = item['datetime']    
            self._market_data.append(item)
            self.on_bar(item)

    def subscribe_data(self, code, frequence, data_host, data_port, data_user, data_password):
        """[summary]

        Arguments:
            code {[type]} -- [description]
            frequence {[type]} -- [description]
        """

        self.sub = subscriber(exchange='realtime_{}_{}'.format(
            frequence, code), host=data_host, port=data_port, user=data_user, password=data_password)
        self.sub.callback = self.callback

    @property
    def old_data(self):
        return self._old_data

    def update(self):
        self._old_data = self._market_data
        self.on_1min_bar()

    @property
    def market_datetime(self):
        return self.market_data.index.levels[0]

    @property
    def market_data(self):

        if self.running_mode == 'sim':
            return self._market_data
        elif self.running_mode == 'backtest':
            return pd.concat(self._market_data, axis=1).T.set_index(['datetime', 'code'])

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
        self.positions.on_price_change(float(new_bar['close'])) 
        self.on_bar(new_bar)

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
        self.running_time = self.new_data['datetime']
        if self.new_data['datetime'][-9:] == '00.000000':
            self.isupdate = True
        self.acc.on_price_change(self.code, self.new_data['close'])
        bar = pd.DataFrame([self.new_data]).set_index(['datetime', 'code']
                                                      ).loc[:, ['open', 'high', 'low', 'close', 'volume']]
        now = datetime.datetime.now()
        if now.hour == 20 and now.minute == 59 and now.second < 10:
            self.daily_func()
            time.sleep(10)

        # res = self.job_control.find_one(
        #     {'strategy_id': self.strategy_id, 'strategy_id': self.strategy_id})
        # self.control_status(res)

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

    def on_bar(self, bar):
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

    def risk_check(self):
        pass

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

    def send_order(self,  direction='BUY', offset='OPEN', price=3925, volume=10, order_id=''):

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

                try:
                    for user in self.subscriber_list:
                        QA.QA_util_log_info(self.subscriber_list)

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
            return self.acc.hold_available.get(self.code)

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
    QAStrategyCTABase(code='RB2001').run()
