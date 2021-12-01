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
        self.client = Trade(key=key, secret=secret)
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


def get_symbols(market):
    return set(map(lambda data: data['currency'], market.get_currencies()))


def get_balance(user):
    return float(user.get_account_list(currency='USDT', account_type='trade')[0]['balance'])


def get_symbol_price(market, symbol):
    return market.get_ticker(f'{symbol}-USDT')['price']


if __name__ == "__main__":
    kuCoin = KuCoin()

    email_sender = EmailSender()
    email_sender.send('Start', "I've started working")

    latest_symbols = get_symbols(kuCoin.market)

    while True:
        current_symbols = get_symbols(kuCoin.market)
        difference = current_symbols - latest_symbols

        if len(difference) > 0:
            coin = difference.pop()

            if get_balance(kuCoin.user) > 1:
                header = f'{coin} was bought'
                message = f"I've bought {coin} with price ${get_symbol_price(kuCoin.market, coin)} for ${math.floor(get_balance(kuCoin.user))}."
            else:
                header = "Couldn't buy"
                message = f"I wanted to buy {coin} but there are not enough USDT on your balance."
            email_sender.send(header, message)

        latest_symbols = current_symbols
