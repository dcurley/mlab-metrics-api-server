# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Dylan Curley

import logging
import pprint
import time

from google.appengine.ext import webapp
from google.appengine.api import runtime

import big_query_backend
import big_query_client
import cloud_sql_backend
import cloud_sql_client
import server


def HANDLERS():
    return [
        ('/_ah/start', StartupHandler),
        ('/_ah/task', TaskRequestHandler),
        ('/_ah/stop', ShutdownHandler),
    ]


class StartupHandler(webapp.RequestHandler):
    def get(self):
        logging.info('Received START request.')
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Started...')
        # Noop.  All work is done when the task is received.


class ShutdownHandler(webapp.RequestHandler):
    def get(self):
        logging.info('Received STOP request.')
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Shutting down.')
        # Noop.  Workers watch & catch runtime.is_shutting_down().


class TaskRequestHandler(webapp.RequestHandler):
    def post(self):
        request = self.request.get('request', default_value=None)
        metric = self.request.get('metric', default_value=None)
        logging.info('Received work task. {request: %s, metric: %s}'
                     % (request, metric))

        # Connect to BigQuery & CloudSQL.
        bq_client = big_query_client.AppAssertionCredentialsBQClient(
            big_query_backend.PROJECT_ID, big_query_backend.DATASET)
        bigquery = big_query_backend.BigQueryBackend(bq_client)

        cs_client = cloud_sql_client.CloudSQLClient(
            cloud_sql_backend.INSTANCE, cloud_sql_backend.DATABASE)
        cloudsql = cloud_sql_backend.CloudSQLBackend(cs_client)

        # Dispatch the task request.
        if request == 'delete_metric':
            _DeleteMetric(metric, cloudsql)
        elif request == 'refresh_metric':
            _RefreshMetric(metric, bigquery, cloudsql)
        elif request == 'update_metric':
            _UpdateMetric(metric, bigquery, cloudsql)
        elif request == 'update_locales':
            _UpdateLocales(cloudsql)
        else:
            logging.error('Unrecognized request: %s' % request)


def _DeleteMetric(metric, cloudsql):
    logging.info('Deleting metric: %s' % metric)

    if not runtime.is_shutting_down:
        _DeleteMetricInfo(cloudsql, metric)
        _DeleteMetricData(cloudsql, metric, date)

    if runtime.is_shutting_down():
        logging.info('Interrupted!  Shutting down.')
    else:
        logging.info('Work completed.')

def _RefreshMetric(metric, bigquery, cloudsql):
    bq_dates = bigquery.ExistingDates()
    cs_dates = cloudsql.ExistingDates()
    missing_cs_dates = set(bq_dates) - set(cs_dates)

    logging.info('Refreshing metric %s for dates: %s'
                 % (metric, sorted(missing_cs_dates)))

    for date in missing_cs_dates:
        if not runtime.is_shutting_down:
            _ComputeMetricData(bigquery, cloudsql, metric, date)

    if runtime.is_shutting_down():
        logging.info('Interrupted!  Shutting down.')
    else:
        logging.info('Work completed.')

def _UpdateMetric(metric, bigquery, cloudsql):
    logging.info('Updating (regenerating) metric: %s' % metric)

    for date in bigquery.ExistingDates():
        if not runtime.is_shutting_down:
            _DeleteMetricData(cloudsql, metric, date)
            _ComputeMetricData(bigquery, cloudsql, metric, date)

    if runtime.is_shutting_down():
        logging.info('Interrupted!  Shutting down.')
    else:
        logging.info('Work completed.')

def _DeleteMetricInfo(cloudsql, metric, date):
    cloudsql.DeleteMetricInfo(metric)

def _DeleteMetricData(cloudsql, metric, date=None):
    if date is None:
        cloudsql.DeleteMetricData(metric)
    else:
        cloudsql.DeleteMetricData(metric, (date.year, date.month))

def _ComputeMetricData(bigquery, cloudsql, metric, date):
    #todo
    pass

def _UpdateLocales(cloudsql):
    #todo
    pass

if __name__ == '__main__':
    server.start(HANDLERS())
