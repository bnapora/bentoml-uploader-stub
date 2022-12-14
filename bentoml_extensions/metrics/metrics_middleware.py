import logging
from timeit import default_timer
import time
from typing import TYPE_CHECKING

from simple_di import inject, Provide

from bentoml._internal.configuration.containers import BentoMLContainer

if TYPE_CHECKING:
    from bentoml._internal import external_typing as ext
    from bentoml._internal.service import Service
    from bentoml._internal.server.metrics.prometheus import PrometheusClient

logger = logging.getLogger(__name__)


'''
Additional Metrics Middleware to monitor timings inside endpoints
'''
class MetricsMiddlewareTest:
    def __init__(self, app: "ext.ASGIApp", bento_service: "Service"):
        self.app = app
        self.bento_service = bento_service
        self._is_setup = False


    @inject
    def _setup(self, metrics_client: "PrometheusClient" = Provide[BentoMLContainer.metrics_client]):
        self.metrics_client = metrics_client
        service_name = self.bento_service.name

        service_name = service_name.replace('-',':').replace('.','::')
        self.metrics_registration_time = metrics_client.Histogram(
                name = service_name + '_registration_time',
                documentation = service_name + ' API HTTP registration time',
                labelnames=["endpoint", "service_version", "metric", "cross_host", 'request_time', 'origin_srvc', 'client_ip', 'num_users', 'test_id'],
        )
        self._is_setup = True

    '''
    Manually start a timer for timing a function call
    '''    
    def start_timer(self):
        return default_timer()

    '''
    Stop the timer after the function call and log it
    '''
    def log(self, timer_start, endpoint, metric, cross_host, request_time='unknown', origin_srvc='unknown', client_ip='unknown', num_users='unknown', test_id='unknown'):
        service_version = (
            self.bento_service.tag.version if self.bento_service.tag is not None else ""
        )
        total_time = max(default_timer() - timer_start, 0)
        # print(total_time, default_timer, START_TIME_REGISTRATION.get())
        self.metrics_registration_time.labels(  # type: ignore
            endpoint=endpoint,
            service_version=service_version,
            metric=metric,
            cross_host=cross_host,
            request_time=request_time,
            origin_srvc=origin_srvc,
            client_ip=client_ip,
            num_users=num_users,
            test_id=test_id
        ).observe(total_time)

    def log_cur_time(self, endpoint, metric, cross_host, request_time='unknown', origin_srvc='unknown', client_ip='unknown', num_users='unknown', test_id='unknown'):
        service_version = (
            self.bento_service.tag.version if self.bento_service.tag is not None else ""
        )
        t = time.time_ns()
        self.metrics_registration_time.labels(  # type: ignore
            endpoint=endpoint,
            service_version=service_version,
            metric=metric,
            cross_host=cross_host,
            request_time=request_time,
            origin_srvc=origin_srvc,
            client_ip=client_ip,
            num_users=num_users,
            test_id=test_id
        ).observe(t)



        

