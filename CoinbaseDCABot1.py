#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    *******************************************************************************************
    CoinbaseDCABot: Coinbase DCA Trading Bot
    Developer: Developer: Ali Toori, Full-Stack Python Developer\
    Founder: https://boteaz.com
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
        self.LOGGER.info(f'Cancelling order: {order_id}')
        self.auth_client.cancel_order(order_id=order_id)

    # Cancel all orders of an asset
    def cancel_all_orders(self, product_id):
        self.LOGGER.info(f'Cancelling all orders of: {product_id}')
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
        self.LOGGER.info(f"DCA Trading Bot Started with pair: {self.product_id}")
        # Place base order and monitor safety orders

    # Stops DCA Trading
    def stop_trading(self):
        self.cancel_all_orders()

    # Checks if DCASTrategy is running
    def is_running(self):
        return self.trading_active

    def get_status(self):
        return status

    # Cancel all orders
    def cancel_all_orders(self):
        if self.base_order_placed:
            self.LOGGER.info(f'Cancelled all orders: {self.trading_pair}')
        else:
            self.LOGGER.info('No orders found')

    # Place the base order
    def place_base_order(self):
        if not self.base_order_placed:

            self.base_order_placed = True

        else:
            self.LOGGER.info('Base order already placed.')


    # Places safety order
    def place_safety_order(self, safety_order_price, safety_order_size):
        self.LOGGER.info(f'Placing Safety at {current_price} with size {size}')
        current_price = self.coinbase_bot.get_current_price(product_id=self.product_id)
        # Place safety order
        safety_order = self.coinbase_bot.buy(product_id=self.product_id, size=size, price=current_price)
        self.safety_orders_placed.append(safety_order)
        self.LOGGER.info(f'Safety order placed at {current_price} with size {size}')

    # Places TakeProfit Order
    def place_take_profit_order(self):

        self.LOGGER.info(f'Take Profit order placed at {current_price} with size {self.base_order_size}')

    # Places StopLoss Order
    def place_stop_loss_order(self):
        self.LOGGER.info(f'Placing Stop Loss order')

        self.LOGGER.info(f'Stop Loss order placed at {current_price} with size {self.size}')

    # Get order status by ID
    def get_order_status(self, order_id):
        order = self.coinbase_bot.auth_client.get_order(order_id)
        return order['status']

    # Update traling take profit price
    def update_trailing_take_profit(self):
        if self.take_profit_order is None:
            return
        if self.base_order_placed:

            self.LOGGER.info(f'Trailing Take profit updated: {self.take_profit_price}')
        else:
            self.LOGGER.info('Base order not placed yet.')

    # Update trailing stop loss price
    def update_trailing_stop_loss(self):
        if self.stop_loss_order is None:
            return

            self.LOGGER.info(f'Traling Stop loss updated: {self.stop_loss_price}')
        else:
            self.LOGGER.info('Base order not placed yet.')

    # Check if safety order needs to be placed
    def check_safety_orders(self):
        if self.base_order_placed:
            for safety_order in self.safety_orders:

                # Check if safety order needs to be placed
                if current_price <= safety_order_price:

                    break
        else:
            self.LOGGER.info('Base order not yet placed.')


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
        print('CoinbaseDCABot: Coinbase DCA Trading Bot\n'
              'Developer: Developer: Ali Toori, Full-Stack Python Developer\n'
              'Founder: https://boteaz.com'
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

        self.LOGGER.info('Dollar Cost Averaging (DCA) Trading Bot')
        self.LOGGER.info('This app implements a DCA trading strategy on Coinbase Pro.')

        # Initialize API credentials and inputs for CoinbaseBot
        key = self.api_key
        secret = self.api_secret
        passphrase = self.passphrase
        trading_pair = self.trading_pair

        # Initialize inputs for DCAStrategy
        base_order_size = self.base_order_size
        safety_order_size = self.safety_order_size
        take_profit_percentage = self.take_profit_percentage
        initial_stop_loss_percentage = self.initial_stop_loss_percentage
        trailing_deviation = self.trailing_deviation
        take_profit_increment_factor = self.take_profit_increment_factor
        max_safety_orders = self.max_safety_orders
        safety_order_size_scale = self.safety_order_size_scale
        safety_order_step_scale = self.safety_order_step_scale
        activation_percentage = self.activation_percentage

        # chec if if API credentials have been entered
        if not key or not secret or not passphrase:
            self.LOGGER.info('Please enter your Coinbase Pro API credentials')
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
            self.LOGGER.info('DCA Bot is already running')
        # Start DCA trading
        else:
            strategy.start_trading()

        self.LOGGER.info('DCA Bot has stopped')

if __name__ == '__main__':
    CoinbaseDCABot().main()
