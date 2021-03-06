import unittest
from mock import patch, ANY
from lighter.datadog import Datadog
import lighter.main as lighter
from lighter.util import jsonRequest

class DatadogTest(unittest.TestCase):
    @patch('lighter.util.jsonRequest')
    def testNotify(self, mock_jsonRequest):
        Datadog('abc').notify(
            title='test title',
            message='test message',
            aggregation_key='/jenkins/test',
            tags=['environment:test'],
            priority='normal',
            alert_type='info')
        self.assertEquals(mock_jsonRequest.call_count, 2)
        mock_jsonRequest.assert_any_call('https://app.datadoghq.com/api/v1/events?api_key=abc', data=ANY, method='POST')
        mock_jsonRequest.assert_any_call('https://app.datadoghq.com/api/v1/series?api_key=abc', data=ANY, method='POST')

    @patch('lighter.util.jsonRequest')
    def testNoApiKey(self, mock_jsonRequest):
        Datadog('').notify(
            title='test title',
            message='test message',
            aggregation_key='/jenkins/test',
            tags=['environment:test'],
            priority='normal',
            alert_type='info')
        self.assertEquals(mock_jsonRequest.call_count, 0)

    @patch('lighter.util.jsonRequest')
    def testNoTitle(self, mock_jsonRequest):
        Datadog('abc').notify(
            title='',
            message='test message',
            aggregation_key='/jenkins/test',
            tags=['environment:test'],
            priority='normal',
            alert_type='info')
        self.assertEquals(mock_jsonRequest.call_count, 0)

    @patch('lighter.util.jsonRequest')
    def testNoMessage(self, mock_jsonRequest):
        Datadog('abc').notify(title='test title', message='', aggregation_key='/jenkins/test', tags=['environment:test'], priority='normal', alert_type='info')
        self.assertEquals(mock_jsonRequest.call_count, 0)

    @patch('lighter.util.jsonRequest')
    def testNoID(self, mock_jsonRequest):
        Datadog('abc').notify(title='test title', message='test message', aggregation_key='', tags=['environment:test'], priority='normal', alert_type='info')
        self.assertEquals(mock_jsonRequest.call_count, 0)

    def _createJsonRequestWrapper(self, marathonurl='http://localhost:1'):
        appurl = '%s/v2/apps/myproduct/myservice' % marathonurl

        def wrapper(url, method='GET', data=None, *args, **kwargs):
            if url.startswith('file:'):
                return jsonRequest(url, data, *args, **kwargs)
            if url == appurl and method == 'PUT' and data:
                return {}
            if url == appurl and method == 'GET':
                return {'app': {}}
            return None
        return wrapper

    def testDefaultTags(self):
        with patch('lighter.util.jsonRequest', wraps=self._createJsonRequestWrapper()) as mock_jsonRequest:
            lighter.deploy('http://localhost:1/', filenames=['src/resources/yaml/integration/datadog-default-tags.yml'])
            mock_jsonRequest.assert_any_call('https://app.datadoghq.com/api/v1/events?api_key=abc', data=ANY, method='POST')

            expected = [
                'environment:default',
                u'service:/myproduct/myservice',
                'source:lighter',
                'type:change']
            self.assertEquals(expected, mock_jsonRequest.call_args[1]['data']['tags'])

    def testConfiguredTags(self):
        with patch('lighter.util.jsonRequest', wraps=self._createJsonRequestWrapper()) as mock_jsonRequest:
            lighter.deploy('http://localhost:1/', filenames=['src/resources/yaml/integration/datadog-config-tags.yml'])
            mock_jsonRequest.assert_any_call('https://app.datadoghq.com/api/v1/events?api_key=abc', data=ANY, method='POST')

            expected = [
                'environment:default',
                u'service:/myproduct/myservice',
                'somekey:someval',
                'anotherkey:anotherval',
                'justakey',
                'source:lighter',
                'type:change']
            self.assertEquals(expected, mock_jsonRequest.call_args[1]['data']['tags'])

    def testDeploymentMetric(self):
        with patch('lighter.util.jsonRequest', wraps=self._createJsonRequestWrapper()) as mock_jsonRequest:
            lighter.deploy('http://localhost:1/', filenames=['src/resources/yaml/integration/datadog-config-tags.yml'])
            mock_jsonRequest.assert_any_call('https://app.datadoghq.com/api/v1/series?api_key=abc', data=ANY, method='POST')

            tags = [
                'environment:default',
                u'service:/myproduct/myservice',
                'somekey:someval',
                'anotherkey:anotherval',
                'justakey',
                'source:lighter',
                'type:change',
                'status:success']
            data = mock_jsonRequest.call_args_list[-2][1]['data']['series'][0]
            self.assertEquals('datadog.events', data['metric'])
            self.assertEquals(1, data['points'][0][1])
            self.assertEquals(tags, data['tags'])
