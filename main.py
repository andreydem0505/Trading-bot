import smtplib
import ssl
from time import sleep
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from kucoin.client import Market
from kucoin.client import Trade
from kucoin.client import User
import math
import os


MAIN_CURRENCY = 'USDT'


class KuCoin:
    def __init__(self):
        key = os.getenv("API_KEY")
        secret = os.getenv("API_SECRET")
        passphrase = os.getenv("API_PASSPHRASE")
        self.client = Trade(key=key, secret=secret, passphrase=passphrase)
        self.user = User(key=key, secret=secret, passphrase=passphrase)
        self.market = Market()


class Sender:
    def send(self, subject, text):
        pass


class EmailSender(Sender):
    def __init__(self):
        self.port = 587
        self.smtp_server = "smtp.gmail.com"
        self.sender_email = os.getenv("EMAIL_FROM")
        self.receiver_email = os.getenv("EMAIL_TO")
        self.password = os.getenv("EMAIL_PASSWORD")

    def send(self, subject, text):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = "Trading bot"
        text = text
        message.attach(MIMEText(text, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.starttls(context=context)
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_email, message.as_string())


class Notificator:
    def __init__(self, sender):
        self.sender = sender

    def start(self):
        self.sender.send("Start working", "I have started working for you.")

    def not_enough_balance(self, ticker):
        self.sender.send("Couldn't buy", f"I wanted to buy {ticker} but there are not enough {MAIN_CURRENCY} on your "
                                         f"balance.")

    def bought(self, ticker):
        self.sender.send(f'{ticker} was bought', f"I've bought {ticker}.")

    def exception(self, exception):
        self.sender.send("Error", str(exception))


def is_trading_symbol(data):
    return data['quoteCurrency'] == MAIN_CURRENCY and data['enableTrading']


def get_symbols(market):
    return set(map(lambda data: data['baseCurrency'], filter(is_trading_symbol, market.get_symbol_list())))


def get_balance(user):
    return float(user.get_account_list(currency=MAIN_CURRENCY, account_type='trade')[0]['balance'])


def buy(client, user, ticker):
    while True:
        try:
            client.create_market_order(ticker, 'buy', funds=math.floor(get_balance(user)))
        except Exception:
            continue
    notificator.bought(symbol)


if __name__ == "__main__":
    kuCoin = KuCoin()

    email_sender = EmailSender()
    notificator = Notificator(email_sender)
    notificator.start()

    latest_symbols = get_symbols(kuCoin.market)

    while True:
        current_symbols = get_symbols(kuCoin.market)
        difference = current_symbols - latest_symbols

        try:
            if len(difference) > 0:
                symbol = difference.pop()

                if get_balance(kuCoin.user) >= 1:
                    pair = f'{symbol}-{MAIN_CURRENCY}'
                    print(pair)
                    buy(kuCoin.client, kuCoin.user, pair)
                else:
                    notificator.not_enough_balance(symbol)

        except IOError:
            sleep(10)
            continue
        except Exception as e:
            notificator.exception(e)

        latest_symbols = current_symbols
