import django
import mock
import pytest
from django.core import signals
from django.core.cache.backends.base import BaseCache
from django.core.exceptions import ImproperlyConfigured

from cacheback.utils import enqueue_task, get_cache, get_job_class


class DummyClass:
    pass


class TestGetCache:

    def test_cache_instance(self):
        assert isinstance(get_cache('default'), BaseCache)

    @pytest.mark.skipif(django.VERSION[:2] == (1, 5), reason='Not supported in Django 1.5')
    def test_signal(self):
        cache = get_cache('default')
        assert signals.request_finished.receivers[-1][1]() == cache.close


class TestGetJobClass:

    @mock.patch('cacheback.utils.logger')
    def test_invalid_module(self, logger_mock):
        assert get_job_class('tests.foo.DummyClass') is None
        assert 'Error importing job module' in logger_mock.error.call_args[0][0]
        assert logger_mock.error.call_args[0][1] == 'tests.foo'

    @mock.patch('cacheback.utils.logger')
    def test_invalid_class(self, logger_mock):
        assert get_job_class('tests.test_utils.OtherDummyClass') is None
        assert 'define a \'%s\' class' in logger_mock.error.call_args[0][0]
        assert logger_mock.error.call_args[0][1] == 'tests.test_utils'
        assert logger_mock.error.call_args[0][2] == 'OtherDummyClass'

    def test_class(self):
        assert get_job_class('tests.test_utils.DummyClass') == DummyClass


class TestEnqueueTask:

    @mock.patch('cacheback.utils.rq_refresh_cache')
    @mock.patch('cacheback.utils.celery_refresh_cache')
    def test_celery(self, celery_mock, rq_mock, settings):
        settings.CACHEBACK_TASK_QUEUE = 'celery'
        enqueue_task(kwargs={'bar': 'baz'})
        assert celery_mock.apply_async.called is True
        assert celery_mock.apply_async.call_args[1] == {'kwargs': {'bar': 'baz'}}
        assert rq_mock.delay.called is False

    @mock.patch('cacheback.utils.rq_refresh_cache')
    @mock.patch('cacheback.utils.celery_refresh_cache')
    def test_rq(self, celery_mock, rq_mock, settings):
        settings.CACHEBACK_TASK_QUEUE = 'rq'
        enqueue_task(kwargs={'bar': 'baz'})
        assert celery_mock.apply_async.called is False
        assert rq_mock.delay.called is True
        assert rq_mock.delay.call_args[1] == {'bar': 'baz'}

    def test_unkown(self, settings):
        settings.CACHEBACK_TASK_QUEUE = 'unknown'
        with pytest.raises(ImproperlyConfigured) as exc:
            enqueue_task('foo')

        assert 'Unkown task queue' in str(exc.value)
