import time
import requests
import datetime
from pyquery import PyQuery as jq
from stem import Signal
from stem.control import Controller
from log import success, info, error, warning
import random
import string
import os
from faker import Faker
from pypinyin import pinyin, lazy_pinyin, Style
from PIL import Image
import _io


faker_langs = ["zh_CN", "zh_TW"]


def error_log(target="", default=None, raise_err=False):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error(f"[{target} {func.__name__}]: {e}")
                if raise_err:
                    raise e
                return default

        return wrapper

    return decorator


@error_log()
def make_new_tor_id():
    info("New Tor ID")
    controller = Controller.from_port(port=9151)
    try:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
        resp = requests.get(
            "https://ipinfo.info/html/my_ip_address.php",
            proxies={"https": "socks5://127.0.0.1:9150"},
        )
        success(f'Current IP: {jq(resp.text)("#Text10 > p > span > b").text()}')
    except Exception as e:
        raise
    finally:
        controller.close()


@error_log()
def init_path(root):
    if not os.path.exists(root):
        os.makedirs(root)


@error_log()
def random_key(length=20):
    return "".join(
        (
            random.choice(
                random.choice(
                    (
                        string.ascii_uppercase,
                        string.ascii_lowercase,
                        "".join(map(str, range(0, 9))),
                    )
                )
            )
            for i in range(1, length)
        )
    )


@error_log()
def fake_datas():
    target = Faker(random.choice(faker_langs))
    names = list(
        map(random.choice, pinyin(target.name(), style=Style.TONE2, heteronym=True))
    )
    names.append(random_key(5))
    return "".join(names)


@error_log()
def fix_nums(data, to=9_999_999, error=-1):
    """
        专治超量
    """
    try:
        nums = int(data)
        return nums if nums < to else to
    except Exception as e:
        return error


@error_log()
def float_format(data):
    try:
        return float(data)
    except Exception as e:
        return 0.0


def time_delay(seconds=120):
    """
        生效期，防止刚注册的账户被ban
    """
    return datetime.datetime.now() + datetime.timedelta(seconds=seconds)


def read_exif_gps(file: _io.BytesIO):
    def format(datas):
        return (
            datas[0][0]
            + (datas[1][0] // datas[1][1]) / 60
            + (datas[1][0] % datas[1][1]) / 3600
        )

    gps_key = 34853
    gps_data = Image.open(file).getexif().get(gps_key, None)
    if gps_data:
        return (
            (1 if gps_data[3] == "E" else -1) * format(gps_data[4]),
            (1 if gps_data[1] == "N" else -1) * format(gps_data[2]),
        )
