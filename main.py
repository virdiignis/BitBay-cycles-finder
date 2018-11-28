import json
import threading
from time import sleep, strftime

import requests

public_key = #######################
private_key = #######################


def log(string):
    with open('bitbay.log', 'a') as LOG:
        LOG.write(str(strftime('%H:%M:%S ')) + str(string) + '\n')
        print(str(strftime('%H:%M:%S ')) + str(string))


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper


class StatsGather:
    crypto = ('LSK', 'LTC', 'DASH', 'GAME')
    fiat = ('PLN', 'USD')

    def __init__(self):
        self.handles = dict()
        self.current_rates = dict()
        for c in self.crypto:
            self.current_rates[c] = dict()
            for f in self.fiat:
                self.current_rates[c][f] = 0
        self.open_logs()

    def open_logs(self):
        try:
            for c in self.crypto:
                self.handles[c] = dict()
                for f in self.fiat:
                    if c == f: break
                    self.handles[c][f] = open("{}{}.txt".format(c, f), 'a')
            return self.handles
        except Exception as e:
            log(e)
            quit(1)

    @threaded
    def gather_data(self):
        try:
            while True:
                for c in self.crypto:
                    for f in self.fiat:
                        if c == f: break
                        r = requests.get("https://bitbay.net/API/Public/{}{}/ticker.json".format(c, f))
                        if r.status_code != 200:
                            log("Status code: {}".format(r.status_code))
                            self.close_logs()
                            quit(2)
                        l = json.loads(r.text)
                        self.current_rates[c][f] = (l['bid'], l['ask'])
                        self.handles[c][f].write(','.join(str(l[k]) for k in l) + '\n')
                        self.handles[c][f].flush()
                sleep(12)
        except Exception as e:
            log(e)
        finally:
            self.close_logs()

    def close_logs(self):
        try:
            for c in self.crypto:
                for f in self.fiat:
                    if c == f: break
                    self.handles[c][f].close()
            return 0
        except Exception as e:
            log(e)
            quit(3)


class ProfitabilityCalc:
    def __init__(self, gather: StatsGather):
        self.current_rates = gather.current_rates
        self.crypto = gather.crypto
        self.fiat = gather.fiat

    def check_cycle(self, crypto1, crypto2):
        r = 100 / self.current_rates[crypto1]['PLN'][1]  # now we got 100PLN worth of C1
        r = r - 0.0043 * r  # provision
        r *= self.current_rates[crypto1]['USD'][0]  # getting USD
        r = r - 0.0043 * r  # provision
        r /= self.current_rates[crypto2]['USD'][1]  # getting C2
        r = r - 0.0043 * r  # provision
        r *= self.current_rates[crypto2]['PLN'][0]  # getting back to PLN
        return r

    def check_all_possible_cycles(self):
        max = 0
        while True:
            for c1 in self.crypto:
                for c2 in self.crypto:
                    r = self.check_cycle(c1, c2)
                    if r > max:
                        log('{} and {}: {}'.format(c1, c2, r))
                        max = r
            sleep(12)


class AutoTrader:
    def __init__(self, gather):
        self.current_rates = gather.current_rates


if __name__ == '__main__':
    # payload = {"method": 'cancel', "id": 12986304377829, "moment": int(time())}
    # headers = {"API-Key":public}
    # request = requests.Request(
    #     'POST', 'https://bitbay.net/API/Trading/tradingApi.php',
    #     data=payload, headers=headers)
    # prepped = request.prepare()
    # signature = hmac.new(private, prepped.body.encode(), digestmod=hashlib.sha512)
    # prepped.headers['API-Hash'] = signature.hexdigest()
    #
    # with requests.Session() as session:
    #     response = session.send(prepped)
    #     pprint(json.loads(response.text))

    g = StatsGather()
    g.gather_data()
    p = ProfitabilityCalc(g)
    sleep(3)
    p.check_all_possible_cycles()

