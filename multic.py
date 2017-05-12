#!/usr/bin/env python3
import sys
import time
import queue
import argparse
import threading
import importlib


_DEFAULT_CONSUMER_NUMBER = 1


class BaseChannel:

    def get(self):
        """ Get message from channel  """
        raise NotImplementedError

    def put(self, msg):
        """ Put message to channel """
        raise NotImplementedError


class FileChannel(BaseChannel):

    def __init__(self, fpath):
        self._stdin = sys.stdin
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        self._fpath = fpath
        self._fd = open(fpath)

        self._iter = self._get()

    def _get(self):
        for line in self._fd:
            yield line

    def get(self):
        try:
            line = next(self._iter)
        except StopIteration:
            raise EOFError

        msg = line.rstrip()

        return msg if msg else None

    def put(self, msg):
        if not isinstance(msg, (bytes, str)):
            raise TypeError('parameter "msg" require bytes or str instead '
                            'of {}'.format(type(msg)))
        _msg = msg.decode() if isinstance(msg, bytes) else msg
        line = _msg + '\n'
        self._stdout.write(line)
        self._stdout.flush()


class PipeChannel(BaseChannel):

    def __init__(self):
        self._stdin = sys.stdin
        self._stdout = sys.stdout
        self._stderr = sys.stderr

        self._iter = self._get()

    def _get(self):
        for line in self._stdin:
            yield line

    def get(self):
        try:
            line = next(self._iter)
        except StopIteration:
            raise EOFError

        msg = line.rstrip()

        return msg if msg else None

    def put(self, msg):
        if not isinstance(msg, (bytes, str)):
            raise TypeError('parameter "msg" require bytes or str instead '
                            'of {}'.format(type(msg)))
        _msg = msg.decode() if isinstance(msg, bytes) else msg
        line = _msg + '\n'
        self._stdout.write(line)
        self._stdout.flush()


# TODO
class RedisChannel(BaseChannel):

    def __init__(self):
        pass

    def get(self):
        pass

    def put(self, msg):
        pass


class Consumer(object):
    def __init__(self, channel, exec_func,
                 consumer_number=_DEFAULT_CONSUMER_NUMBER):
        self._consumer_channel = channel
        self._consumer_number = consumer_number

        if not callable(exec_func):
            raise TypeError('parameter "exec_func" require callable type instead '
                            'of {}'.format(type(exec_func)))
        self._consumer_exec_func = exec_func

        self._consumer_threads = []
        self._preload_msgs_size = self._consumer_number
        self._preload_msgs_queue = queue.Queue()

        self._count = 0

    @property
    def consumer_channel(self):
        return self._consumer_channel

    @property
    def consumer_exec_func(self):
        return self._consumer_exec_func

    def _create_consumer_threads(self):
        if self._consumer_number and len(self._consumer_threads) == 0:
            self._consumer_threads = [
                threading.Thread(target=self._consumer_ioloop,
                                 name='Thread-{}'.format(_ix),
                                 daemon=True)
                for _ix in range(self._consumer_number)
            ]

    def _start_consumer_threads(self):
        for _ in self._consumer_threads:
            _.start()

    def _consumer_ioloop(self):
        while True:
            msg = self._preload_msgs_queue.get()
            if not msg:
                time.sleep(0.5)
                continue
            try:
                self._consumer_exec_func(self, msg)
            except Exception as ex:
                continue

    def run(self):
        self._create_consumer_threads()
        self._start_consumer_threads()
        # start_time = time.time()
        # _empty_x = 0
        while True:
            cur_preload_msgs_size = self._preload_msgs_queue.qsize()
            if cur_preload_msgs_size < self._preload_msgs_size:
                try:
                    msg = self.consumer_channel.get()
                    if not msg:
                        # _empty_x += 1
                        # if _empty_x > 60:
                        #     print('empty msg got 60 times, exit?')
                        #     _empty_x = 0
                        #     continue
                        time.sleep(0.5)
                        continue
                    # _empty_x = 0
                    self._preload_msgs_queue.put(msg)
                except KeyboardInterrupt:
                    # end_time = time.time()
                    # cost_time = end_time - start_time
                    exit(-1)
                except EOFError:
                    exit(0)
                except Exception:
                    continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--module', dest='EXECUTED', type=str,
                        help='the function executed module path (e.g. "m1.func1")')
    parser.add_argument('-c', '--count', dest='THREAD_COUNT', type=int, default=1,
                        help='the number of consumers to '
                             'process messages (default: 1)')
    parser.add_argument('-i', '--in', dest='INCHAN', type=str, default='-',
                        help='the input channel to get messages to process')
    args = parser.parse_args()

    _executed = args.EXECUTED
    _consumer_number = args.THREAD_COUNT

    if not _executed:
        print('executed not been set')
        exit(-1)

    _module_path, _exec_func_name = _executed.rsplit('.', 1)
    _module = importlib.import_module(_module_path)
    _exec_func = getattr(_module, _exec_func_name)
    _inchan = args.INCHAN
    if _inchan == '-':
        _channel = PipeChannel()
    else:
        _channel = FileChannel(_inchan)
    consumer = Consumer(_channel, _exec_func, _consumer_number)
    consumer.run()

