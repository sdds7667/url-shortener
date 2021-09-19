import datetime
import uuid
from abc import abstractmethod
import numpy as np


class URLShortener:

    @staticmethod
    @abstractmethod
    def get_max_url_length() -> int: pass

    @staticmethod
    @abstractmethod
    def get_shorter_url_for(url: str) -> str: pass


def alphabet_indexed(val: int) -> str:
    if val < 26:
        return chr(ord('A') + val)
    elif val < 52:
        return chr(ord('a') + val - 26)
    else:
        return chr(ord('0') + val - 52)


class UUID4BasedURLShortener(URLShortener):

    @staticmethod
    def get_shorter_url_for(url: str) -> str:
        rv = datetime.datetime.now().strftime("%Y-%m-%d") + str(uuid.uuid4()) + url

        digitNumber = np.array([ord(i) for i in rv])
        np.random.shuffle(digitNumber)
        intervalSize = len(digitNumber) // 6
        finalString = ""
        for k in range(6):
            charIndex = sum(digitNumber[(intervalSize * k):(intervalSize * (k + 1))]) % 62
            finalString += alphabet_indexed(charIndex)

        return finalString

    @staticmethod
    def get_max_url_length() -> int:
        return 6


if __name__ == '__main__':
    url = "https://www.amazon.com/deal/ec376f60/ref=gbps_img_m-9_475e_ec376f60?&moreDeals=598f3447,cdd0799c,1460cec4,d4a769d2,62a5e110&searchAlias=fashion&smid=ATVPDKIKX0DER&pf_rd_p=5d86def2-ec10-4364-9008-8fbccf30475e&pf_rd_s=merchandised-search-9&pf_rd_t=101&pf_rd_i=15529609011&pf_rd_m=ATVPDKIKX0DER&pf_rd_r=WQRP794HFWZXMMMYWXTC"
    print(UUID4BasedURLShortener.get_shorter_url_for(url))
