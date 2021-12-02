import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from kucoin.client import Market
from kucoin.client import Trade
from kucoin.client import User
import math
import os


class KuCoin:
    def __init__(self):
        key = os.getenv("API_KEY")
        secret = os.getenv("API_SECRET")
        passphrase = os.getenv("API_PASSPHRASE")
        self.client = Trade(key=key, secret=secret, passphrase=passphrase)
        self.user = User(key=key, secret=secret, passphrase=passphrase)
        self.market = Market()


class EmailSender:
    def __init__(self):
        self.port = 587
        self.smtp_server = "smtp.gmail.com"
        self.sender_email = os.getenv("EMAIL_FROM")
        self.receiver_email = os.getenv("EMAIL_TO")
        self.password = os.getenv("EMAIL_PASSWORD")

    def send(self, subject, text):
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = "Trade bot"
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

    def not_enough_balance(self, ticker):
        self.sender.send("Couldn't buy", f"I wanted to buy {ticker} but there are not enough USDT on your balance.")

    def bought(self, ticker):
        self.sender.send(f'{ticker} was bought', f"I've bought {ticker}.")


def get_tickers(market):
    return set(map(lambda data: data['symbol'], filter(lambda data: data['symbol'].endswith('-USDT'), market.get_all_tickers()['ticker'])))


def get_balance(user):
    return float(user.get_account_list(currency='USDT', account_type='trade')[0]['balance'])


def get_price(market, ticker):
    return float(market.get_ticker(ticker)['price'])


def get_amount_to_buy(user, market, ticker):
    return math.floor(get_balance(user) / get_price(market, ticker))


if __name__ == "__main__":
    kuCoin = KuCoin()

    email_sender = EmailSender()
    notificator = Notificator(email_sender)

    latest_tickers = get_tickers(kuCoin.market)

    while True:
        current_tickers = get_tickers(kuCoin.market)
        difference = current_tickers - latest_tickers

        if len(difference) > 0:
            pair = difference.pop()

            if get_balance(kuCoin.user) > 1:
                kuCoin.client.create_market_order(pair, 'buy', size=get_amount_to_buy(kuCoin.user, kuCoin.market, pair))
                notificator.bought(pair)
            else:
                notificator.not_enough_balance(pair)

        latest_tickers = current_tickers
