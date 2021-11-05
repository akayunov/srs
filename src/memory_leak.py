import asyncio
import logging
import os
import signal

from aiohttp import web

from ss import SS_FAKE_TESTS_MODE
from ss.cli.command import AppCommand
from ss.common.metrics.server import MetricsServer
from ss.configuration import get_ss_config
from ss.web.context import Context
from ss.web.jobexecutors import init_job_executors
from ss.web.ready import Handler

LOG = logging.getLogger(__name__)


class AioHttpWorker(AppCommand):
    routes = []
    port = 8080
    web_app = web.Application(client_max_size=500 * 1024 ** 2)
    init_db_connection = False

    def __init__(self):
        super().__init__()
        self.ready = None

    @staticmethod
    async def turn_on_debug():
        # performance consuming operation
        # TODO How to turn it on for local mode?
        if SS_FAKE_TESTS_MODE:
            ioloop = asyncio.get_running_loop()
            ioloop.set_debug(True)
            logging.basicConfig(level=logging.DEBUG)
            # warnings.simplefilter('always', ResourceWarning)

    def get_on_startup_callbacks(self):
        return Context.init_connections(), self.turn_on_debug()

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('-p', '--port', metavar='port', type=int, default=self.port, help='server port')

    def init_app(self):
        super().init_app()
        self.ready = Handler()
        # TODO refactor this
        executors_spec = [('mysql', 'thread', self.config['worker_pool_size'])]
        if self.config.get('replication_worker_pool_size'):
            executors_spec.append(('replication', 'thread', get_ss_config()['replication_worker_pool_size']))
        if self.config.get('storage'):
            executors_spec.append(('requests', 'thread', self.config['worker_pool_size']))
        if self.config.get('crypt_worker_pool_size'):
            # TODO do it in another thread in subinterpritator to avoid block main thread
            executors_spec.append(('crypt', 'process', self.config['crypt_worker_pool_size']))
        init_job_executors(*executors_spec)

    def handle(self):
        self.init_app()
        self.web_app['metrics_server'] = MetricsServer(job_timeout=get_ss_config().get('job_timeout'))
        self.web_app['durations'] = {
            'framework': {'counter': 0, 'sum': 0},
            'handler': {'counter': 0, 'sum': 0},
            'mysql': {'counter': 0, 'sum': 0},
            'iorecv': {'counter': 0, 'sum': 0},
        }
        self.web_app.add_routes([
            web.route('*', r'/{path:ready}', self.ready.get),
            web.route('*', r'/{path:metrics}', self.web_app['metrics_server'].get),
            *self.routes
        ])
        for cb in self.get_on_startup_callbacks():
            self.web_app.on_startup.append(lambda app, _cb=cb: asyncio.create_task(_cb))
        self.web_app.on_startup.append(lambda app: asyncio.create_task(pg()))
        web.run_app(self.web_app, port=self.args.port)

    async def stop(self):
        # await self.web_app.shutdown()
        # await self.web_app.cleanup()
        LOG.debug('Application is stopping')
        os.kill(os.getpid(), signal.SIGINT)


async def pg(*args):
    asyncio.get_running_loop().call_later(10, print_garbage)


import gc

gc.set_debug(gc.DEBUG_SAVEALL)
# ids = {}
count_ids = {}
prev_count_id = {}
s_ids = set()
f = open('/tmp/look', 'w')


def print_garbage(*args):
    # breakpoint()
    global prev_count_id, count_ids
    for i in gc.garbage:
        s = str(id(i))

        t = type(i)
        if t not in count_ids:
            count_ids[t] = 0
            # ids[s] = True
        if t is dict and s not in s_ids:
            f.write(f'{i}\n')
            s_ids.add(s)
        # f.write(f'{i}\n')
        count_ids[t] += 1

    for i in sorted(count_ids, key=lambda x: count_ids[x], reverse=True):
        LOG.error(f'{i}: {count_ids[i]}')
        # if count_ids[i] - prev_count_id.get(i, 0):
        f.write(f'{i}: {count_ids[i] - prev_count_id.get(i, 0)} {count_ids[i]} {prev_count_id.get(i, 0)}\n')
    f.write('=========================================================================================\n')
    f.flush()
    prev_count_id = {}
    for k in count_ids:
        prev_count_id[k] = count_ids[k]
    count_ids = {}
    asyncio.get_running_loop().call_later(10, print_garbage)
