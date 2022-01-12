from threading import Thread

__all__ = ('run_non_blocking',)


def run_non_blocking(method, args, callback):
    def wrapper():
        callback(method(*args))

    Thread(target=wrapper).start()
