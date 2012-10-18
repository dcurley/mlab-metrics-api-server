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

"""This module ...

todo: Lots more text.
"""

import backend
import logging
from metrics import DetermineLocaleType
import pprint

LOCALES_TABLE = '_locales'
METADATA_TABLE = '_metadata'


class CloudSQLBackend(backend.Backend):
    def __init__(self, cloudsql):
        """Constructor.

        Args:
            cloudsql (object): CloudSQL client instance.
        """
        self._cloudsql = cloudsql
        super(CloudSQLBackend, self).__init__()

    def GetMetricInfo(self, metric_name=None):
        """Retrieves metadata for the specified metric, from CloudSQL.

        Args:
            metric_name (string): Name of the metric to query.  If None or not
                specified, retrieves info all metric.

        Raises:
            LoadError: If there was an error getting the metric info from
                CloudSQL.

        Returns:
            (dict): Collection of data for the requested metric, keyed by the
            data type.  If no metric was requested, returns a dict of these
            collections (a dict inside a dict), keyed by metric name.
        """
        query = ('SELECT *'
                 '  FROM %s' % METADATA_TABLE)
        if metric_name is not None:
            query += (' WHERE name="%s"' % metric_name)

        try:
            result = self._cloudsql.Query(query)
        except big_query_client.Error as e:
            raise backend.LoadError('Could not load metric info for "%s" from'
                                    ' BigQuery: %s' % (metric_name, e))

        if metric_name is None:
            # Create dict of info-dicts, indexed by metric name.
            infos = dict()
            for row in result['data']:
                row_dict = dict(zip(result['fields'], row))
                infos[row_dict['name']] = row_dict
            return infos
        else:
            # There should be only one row in the result.
            return dict(zip(result['fields'], result['data'][0]))

    def SetMetricInfo(self, request_type, metric_name, metrics_info):
        """Pushes the provided metric info to the backend data store.

        Args:
            request_type (RequestType): 
            metric_name (string): If provided, only update the specified metric.
            metrics_info (dict): Collection of updated metric info to send to
                the backend data store, keyed by metric name.

        Raises:
            EditError: If the requested updates could not be applied.
        """
        if request_type != backend.RequestType.DELETE:
            new_data = dict((k, v)
                            for (k, v) in metrics_info[metric_name].iteritems()
                            if k != 'name')

        if request_type == backend.RequestType.EDIT:
            self._cloudsql.Update(METADATA_TABLE, metric_name, new_data)
        elif request_type == backend.RequestType.NEW:
            self._cloudsql.Create(METADATA_TABLE, metric_name, new_data)
        elif request_type == backend.RequestType.DELETE:
            self._cloudsql.Delete(METADATA_TABLE, metric_name)
        else:
            raise backend.EditError('Unrecognized request type: %s' % request_type)

    def GetMetricData(self, metric_name, date, locale):
        """Retrieves data for this metric for the given 'date' and 'locale'.

        Args:
            date (tuple): Date for which data should be loaded, given as a tuple
                consisting of ints (year, month).
            locale (string): Locale for which data should be loaded.

        Raises:
            LoadError: If the requested metric data could not be read.  This may
                happen if, for example, a bogus locale was requested, or a bogus
                date.

        Returns:
            (dict): Result data from the query, with keys "locale" and "value".
        """
        query = ('SELECT locale, value'
                 '  FROM %s'
                 ' WHERE date="%s"' %
                 (metric_name, '%4d-%02d-01' % date))

        try:
            result = self._cloudsql.Query(query)
        except cloud_sql_client.Error as e:
            raise backend.LoadError('Could not load metric data for "%s" from'
                                    ' CloudSQL: %s' % (metric_name, e))
        return result

    def GetLocaleData(self, locale_type):
        """Retrieves all locale data for the given 'locale_type'.
        
        Args:
            locale_type (string): One of "country", "region", or "city" which
                specifies the type of locale to retrieve data on.

        Returns:
            (dict): Result data from the query, with keys "locale", "name",
            "parent", "lat" (latitude), and "lon" (longitude).
        """
        query = ('SELECT locale, name, parent, lat, lon'
                 '  FROM %s'
                 ' WHERE type="%s"' %
                 (LOCALES_TABLE, locale_type))

        try:
            result = self._cloudsql.Query(query)
        except cloud_sql_client.Error as e:
            raise backend.LoadError('Could not load locale info from CloudSQL:'
                                    ' %s' % e)
        return result