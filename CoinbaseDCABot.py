#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    *******************************************************************************************
    CoinbaseDCABot: Coinbase DCA Trading Bot
    Author: Ali Toori
    Website: https://boteaz.com/
    *******************************************************************************************
"""
import json
import logging.config
import os
from pathlib import Path
import math

import pandas as pd
import pyfiglet
import cbpro
import streamlit as st
from time import sleep
from datetime import datetime


# Coinbase Bot class to handle orders on coinbase exchange
class CoinbaseBot:
    def __init__(self, api_key, secret_key, passphrase, trading_pair="BTC-USD"):
        self.auth_client = cbpro.AuthenticatedClient(api_key, secret_key, passphrase)
        self.public_client = cbpro.PublicClient()
        self.product_id = trading_pair

    def get_order_book(self, product_id, level=1):
        return self.public_client.get_product_order_book(product_id, level=level)

    # Get current market price of an asset
    def get_current_price(self, product_id):
        ticker = self.public_client.get_product_ticker(product_id)
        return float(ticker['price'])

    # Get account balance for an asset
    def get_account(self, currency):
        accounts = self.auth_client.get_accounts()
        for account in accounts:
            if account['currency'] == currency:
                return account
        return None

    # Get balance of an asset
    def get_balance(self, currency):
        account = self.get_account(currency)
        return float(account['balance'])

    # Places Buy Limit Order
    def buy(self, product_id, size, price):
        buy_order = {
            'side': 'buy',
            'product_id': product_id,
            'size': size,
            'price': price,
        }
        order = self.auth_client.place_limit_order(**buy_order)
        return order

    # Places Sell Limit Order
    def sell(self, product_id, size, price):
        sell_order = {
            'side': 'sell',
            'product_id': product_id,
            'size': size,
            'price': price,
        }
        order = self.auth_client.place_limit_order(**sell_order)
        return order

    # Cancel order by order ID
    def cancel_order(self, order_id):
        st.write(f'Cancelling order: {order_id}')
        self.auth_client.cancel_order(order_id=order_id)

    # Cancel all orders of an asset
    def cancel_all_orders(self, product_id):
        st.write(f'Cancelling all orders of: {product_id}')
        self.auth_client.cancel_all(product_id=product_id)


# Main DCA Strategy class
class DCAStrategy:
    def __init__(self, bot=None, base_order_size=10, safety_order_size=10, take_profit_percentage=0.03,
                 trailing_deviation=0.01, initial_stop_loss_percentage=0.01,
                 take_profit_increment_factor=2, max_safety_orders=3,
                 safety_order_size_scale=1.5, safety_order_step_scale=1.5,
                 activation_percentage=0.05):
        self.coinbase_bot = bot
        self.product_id = self.coinbase_bot.product_id
        self.base_order_size = base_order_size
        self.safety_order_size = safety_order_size
        self.take_profit_percentage = take_profit_percentage
        self.trailing_deviation = trailing_deviation
        self.initial_stop_loss_percentage = initial_stop_loss_percentage
        self.take_profit_increment_factor = take_profit_increment_factor
        self.max_safety_orders = max_safety_orders
        self.safety_order_size_scale = safety_order_size_scale
        self.safety_order_step_scale = safety_order_step_scale
        self.activation_percentage = activation_percentage

        self.trading_pair = self.product_id
        self.trading_active = False
        self.base_order = None
        self.base_order_placed = False
        self.base_order_id = None
        self.safety_orders = []
        self.safety_orders_placed = []

        self.take_profit_order = None
        self.stop_loss_order = None

        self.take_profit_price = None
        self.stop_loss_price = None
        self.running = False  # initialize the running attribute to False

    # Starts DCA Trading
    def start_trading(self):
        self.trading_active = True
        st.success(f"DCA Trading Bot Started with pair: {self.product_id}")
        # Place base order and monitor safety orders
        self.place_base_order()
        while True:
            self.check_safety_orders()
            self.update_trailing_take_profit()
            self.update_trailing_stop_loss()
            sleep(60)

    # Stops DCA Trading
    def stop_trading(self):
        self.cancel_all_orders()
        self.trading_active = False
        st.warning('DCA trading strategy has stopped')

    # Checks if DCASTrategy is running
    def is_running(self):
        return self.trading_active

    def get_status(self):
        status = {
            'DateTime': datetime.now().strftime("%d-%b-%Y-%H:%M:%S"),
            'TradingPair': self.trading_pair,
            'BaseOrder': self.base_order,
            'SafetyOrders': self.safety_orders,
            'TrailingTakeProfit': self.take_profit_price,
            'TrailingStopLoss': self.stop_loss_price,
            'Running': self.running
        }
        return status

    # Cancel all orders
    def cancel_all_orders(self):
        if self.base_order_placed:
            current_price = self.coinbase_bot.cancel_all_orders(product_id=self.product_id)
            self.base_order_placed = False
            st.write(f'Cancelled all orders: {self.trading_pair}')
        else:
            st.write('No orders found')

    # Place the base order
    def place_base_order(self):
        if not self.base_order_placed:
            current_price = self.coinbase_bot.get_current_price(product_id=self.product_id)
            size = self.base_order_size / float(current_price)
            self.base_order = self.coinbase_bot.buy(product_id=self.product_id, size=size, price=current_price)
            st.write(f'Base order placed: {self.base_order}')
            self.base_order_placed = True
            # Update initial TP and SL
            self.take_profit_price = current_price + (current_price * self.take_profit_percentage)
            self.stop_loss_price = current_price - (current_price * self.initial_stop_loss_percentage)
        else:
            st.write('Base order already placed.')

    # Calculates safety orders and appends to safety_orders list
    def get_safety_orders(self, safety_order_size):
        current_price = self.coinbase_bot.get_current_price(product_id=self.product_id)
        # Check if safety order are less than the max safety orders
        if len(self.safety_orders) < self.max_safety_orders:
            # Calculate safety order price and size
            self.safety_order_size *= self.safety_order_size_scale
            self.safety_order_step_scale += self.safety_order_step_scale * self.safety_order_price_deviation
            safety_order_price = current_price - (current_price * self.safety_order_step_scale / 100)
            self.safety_orders.append({'price': safety_order_price, 'size': self.safety_order_size})

    # Places safety order
    def place_safety_order(self, safety_order_price, safety_order_size):
        st.write(f'Placing Safety at {current_price} with size {size}')
        current_price = self.coinbase_bot.get_current_price(product_id=self.product_id)
        # Place safety order
        safety_order = self.coinbase_bot.buy(product_id=self.product_id, size=size, price=current_price)
        self.safety_orders_placed.append(safety_order)
        st.write(f'Safety order placed at {current_price} with size {size}')

    # Places TakeProfit Order
    def place_take_profit_order(self):
        st.write(f'Placing Take Profit order')
        price = self.take_profit_price
        size = self.base_order['size']
        self.take_profit_order = self.coinbase_bot.sell(product_id=self.product_id, size=size, price=price)
        st.write(f'Take Profit order placed at {current_price} with size {self.base_order_size}')

    # Places StopLoss Order
    def place_stop_loss_order(self):
        st.write(f'Placing Stop Loss order')
        price = self.stop_loss_price
        size = self.base_order['size']
        self.stop_loss_order = self.coinbase_bot.sell(product_id=self.product_id, size=size, price=price)
        st.write(f'Stop Loss order placed at {current_price} with size {self.size}')

    # Get order status by ID
    def get_order_status(self, order_id):
        order = self.coinbase_bot.auth_client.get_order(order_id)
        return order['status']

    # Update traling take profit price
    def update_trailing_take_profit(self):
        if self.take_profit_order is None:
            return
        if self.base_order_placed:
            current_price = self.coinbase_bot.get_current_price(product_id=self.product_id)
            # Update trailing take profit by increamenting the previous take_profit with take_profit_increament_factor
            self.take_profit_price += (self.take_profit_price * self.take_profit_increment_factor)
            size = self.take_profit_order['size']
            self.coinbase_bot.cancel_order(self.take_profit_order['id'])
            self.take_profit_order = self.coinbase_bot.sell(size=size, price=self.take_profit_price)
            st.write(f'Trailing Take profit updated: {self.take_profit_price}')
        else:
            st.write('Base order not placed yet.')

    # Update trailing stop loss price
    def update_trailing_stop_loss(self):
        if self.stop_loss_order is None:
            return
        if self.base_order_placed:
            current_price = self.coinbase_bot.get_current_price()
            self.stop_loss_price += (self.stop_loss_price * trailing_deviation)
            size = self.stop_loss_order['size']
            self.coinbase_bot.cancel_order(self.stop_loss_order['id'])
            self.stop_loss_order = self.coinbase_bot.sell(size=size, price=self.stop_loss_price)
            st.write(f'Traling Stop loss updated: {self.stop_loss_price}')
        else:
            st.write('Base order not placed yet.')

    # Check if safety order needs to be placed
    def check_safety_orders(self):
        if self.base_order_placed:
            for safety_order in self.safety_orders:
                current_price = self.coinbase_bot.get_current_price(product_id=self.product_id)
                safety_order_price = float(safety_order['price'])
                safety_order_size = safety_order['size']
                # Check if safety order needs to be placed
                if current_price <= safety_order_price:
                    # activation_price = current_price * (1 + self.activation_percentage)
                    self.safety_orders.remove(safety_order)
                    self.place_safety_order(safety_order_price=safety_order_price, safety_order_size=safety_order_size)
                    self.place_take_profit_order()
                    self.place_stop_loss_order()
                    break
        else:
            st.write('Base order not yet placed.')


class DCATradingBot:
    def __init__(self):
        self.PROJECT_ROOT = Path(os.path.abspath(os.path.dirname(__file__)))
        self.file_settings = str(self.PROJECT_ROOT / 'BotRes/Settings.json')
        self.file_orders = str(self.PROJECT_ROOT / 'BotRes/Orders.csv')
        self.settings = self.get_settings()
        self.passphrase = self.settings['Settings']['PassPhrase']
        self.api_key = self.settings['Settings']['APIKey']
        self.api_secret = self.settings['Settings']['APISecret']
        self.trading_pair = self.settings['Settings']['TradingPair']
        self.base_order_size = self.settings['Settings']['BaseOrderSize']
        self.safety_order_size = self.settings['Settings']['SafetyOrderSize']
        self.take_profit_percentage = self.settings['Settings']['TakeProfitPercentage']
        self.initial_stop_loss_percentage = self.settings['Settings']['InitialStopLossPercentage']
        self.trailing_deviation = self.settings['Settings']['TrailingDeviation']
        self.take_profit_increment_factor = self.settings['Settings']['TPIncrementFactor']
        self.max_safety_orders = self.settings['Settings']['MaxSafetyOrders']
        self.safety_order_size_scale = self.settings['Settings']['SafetyOrderSizeScale']
        self.safety_order_step_scale = self.settings['Settings']['SafetyOrderStepScale']
        self.activation_percentage = self.settings['Settings']['ActivationPercentage']
        self.LOGGER = self.get_logger()

    # Get self.LOGGER
    @staticmethod
    def get_logger():
        """
        Get logger file handler
        :return: LOGGER
        """
        logging.config.dictConfig({
            "version": 1,
            "disable_existing_loggers": False,
            'formatters': {
                'colored': {
                    '()': 'colorlog.ColoredFormatter',  # colored output
                    # --> %(log_color)s is very important, that's what colors the line
                    'format': '[%(asctime)s,%(lineno)s] %(log_color)s[%(message)s]',
                    'log_colors': {
                        'DEBUG': 'green',
                        'INFO': 'cyan',
                        'WARNING': 'yellow',
                        'ERROR': 'red',
                        'CRITICAL': 'bold_red',
                    },
                },
                'simple': {
                    'format': '[%(asctime)s,%(lineno)s] [%(message)s]',
                },
            },
            "handlers": {
                "console": {
                    "class": "colorlog.StreamHandler",
                    "level": "INFO",
                    "formatter": "colored",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "simple",
                    "filename": "CoinbaseDCABot.log"
                },
            },
            "root": {"level": "INFO",
                     "handlers": ["console", "file"]
                     }
        })
        return logging.getLogger()

    @staticmethod
    def enable_cmd_colors():
        from sys import platform
        if platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(11), 7)

    @staticmethod
    def banner():
        pyfiglet.print_figlet(text='____________ CoinbaseDCABot\n', colors='RED')
        print('Author: Ali Toori\n'
              'Website: https://boteaz.com/\n'
              '************************************************************************')

    # Get settings from Setting.json file
    def get_settings(self):
        """
        Creates default or loads existing settings file.
        :return: settings
        """
        if os.path.isfile(self.file_settings):
            with open(self.file_settings, 'r') as f:
                settings = json.load(f)
            return settings
        settings = {"settings": {
            "APIKey": "Please set your API Key",
            "APISecret": "Please set your API Secret",
            "EntryPrice": 27000,
            "BaseOrderSize": 10,
            "SafetyOrderSize": 10,
            "TakeProfitPercentage": 0.03,
            "MaxSafetyOrders": 3,
            "TrailingDeviation": 1,
            "SafetyOrderSizeScale": 1.5,
            "SafetyOrderStepScale": 1.5,
            "ActivationPercentage": 3.0,
            "InitialStopLossPercentage": 1.0,
            "TPIncrementFactor": 0.5,
            "BotToken": "6531191311:45647MssHslMJNE2wxAsI3M4b6456",
            "ChatID": "3453242342"}}
        with open(self.file_settings, 'w') as f:
            json.dump(settings, f, indent=4)
        with open(self.file_settings, 'r') as f:
            settings = json.load(f)
        return settings

    def get_futures_account_balance(self, client, currency='USDT'):
        """Get account future balance
        :param currency: Default to USDT
        :param client: Binance client
        :return: Futures account balance
        """
        for x in client.futures_account_balance():
            if x['asset'] == currency:
                return float(x['balance'])

    def check_order(self, order_id):
        """
        Check if deal was already saved
        :param order_id: Order ID
        :return: Order if the order's id exists in orders
        """
        order_df = pd.read_csv(self.file_orders, index_col=None)
        return order_df.loc[order_df['OrderID'] == order_id]

    def get_data_frame(self, symbol):
        """ Get DataFrame from DataManager
        :param symbol: Pair symbol used as a file name
        :return: DataFrame
        """
        file_path = str(self.PROJECT_ROOT / f'DataManager/{symbol}.csv')
        return pd.read_csv(file_path, index_col=None)

    def main(self):
        self.enable_cmd_colors()
        self.banner()
        self.LOGGER.info(f'Coinbase DCABot launched')
        # Set up API credentials
        api_key = self.api_key
        secret_key = self.api_secret
        passphrase = self.passphrase

        # Create the streamlit app
        st.title('Dollar Cost Averaging (DCA) Trading Bot')
        st.write('This app implements a DCA trading strategy on Coinbase Pro.')

        # Initialize API credentials and inputs for CoinbaseBot
        key = st.text_input('Enter your Coinbase Pro API key', value=api_key)
        secret = st.text_input('Enter your Coinbase Pro API secret', type='password', value=secret_key)
        passphrase = st.text_input('Enter your Coinbase Pro API passphrase', type='password', value=passphrase)
        trading_pair = st.text_input('Trading Pair (e.g. BTC-USD)', value="BTC-USD")

        # create Streamlit inputs for DCAStrategy
        base_order_size = st.number_input('Base Order Size', value=10, step=1)
        safety_order_size = st.number_input('Safety Order Size', value=10, step=1)
        take_profit_percentage = st.number_input('Take Profit Percentage', value=0.03, step=0.01)
        initial_stop_loss_percentage = st.number_input('Initial Stop Loss Percentage', value=0.01, step=0.01)
        trailing_deviation = st.number_input('Trailing Deviation %', value=0.01, step=0.01)
        take_profit_increment_factor = st.number_input('Take Profit Increment Factor', value=2, step=1)
        max_safety_orders = st.number_input('Maximum Number of Safety Orders', value=5, step=1)
        safety_order_size_scale = st.number_input('Safety Order Size Scale', value=1.5, step=0.1)
        safety_order_step_scale = st.number_input('Safety Order Step Scale', value=1.5, step=0.1)
        activation_percentage = st.number_input('Activation Percentage', value=0.05, step=0.01)

        # chec if if API credentials have been entered
        if not key or not secret or not passphrase:
            st.warning('Please enter your Coinbase Pro API credentials')
            return

        # Create CoinbaseBot and DCAStrategy objects
        coinbase_bot = CoinbaseBot(key, secret, passphrase, trading_pair=trading_pair)
        strategy = DCAStrategy(
            bot=coinbase_bot,
            base_order_size=base_order_size,
            safety_order_size=safety_order_size,
            take_profit_percentage=take_profit_percentage,
            trailing_deviation=trailing_deviation,
            initial_stop_loss_percentage=initial_stop_loss_percentage,
            take_profit_increment_factor=take_profit_increment_factor,
            max_safety_orders=max_safety_orders,
            safety_order_size_scale=safety_order_size_scale,
            safety_order_step_scale=safety_order_step_scale,
            activation_percentage=activation_percentage
        )

        # check if strategy is already running
        if strategy.is_running():
            st.warning('DCA Bot is already running')
        # Start DCA trading
        else:
            run_bot = st.button('Run Bot')
            if run_bot:
                strategy.start_trading()

        # Create a container for the log messages
        log_container = st.container()
        log_table = log_container.empty()

        while strategy.is_running():
            status = strategy.get_status()
            # st.write(status)
            log_table.write(status)
            sleep(1)
            # sleep(10)
        st.warning('DCA Bot has stopped')

if __name__ == '__main__':
    CoinbaseDCABot().main()
