import hashlib
import json
import threading
import time
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response


class InFlightRequestRegistry:
    def __init__(self):
        self._requests = {}
        self._lock = threading.Lock()

    def acquire(self, key):
        with self._lock:
            if key in self._requests:
                return False, self._requests[key]
            event = threading.Event()
            self._requests[key] = {
                'event': event,
                'result': None,
                'error': None,
            }
            return True, None

    def release(self, key, result=None, error=None):
        with self._lock:
            data = self._requests.pop(key, None)
        if data:
            data['result'] = result
            data['error'] = error
            data['event'].set()

    def wait(self, key, timeout=10):
        with self._lock:
            data = self._requests.get(key)
        if not data:
            return None, None
        data['event'].wait(timeout=timeout)
        return data['result'], data['error']


_inflight = InFlightRequestRegistry()


def _make_cache_key(prefix, *parts):
    raw = ':'.join(str(p) for p in parts)
    h = hashlib.md5(raw.encode('utf-8')).hexdigest()
    return f'{prefix}:{h}'


def cache_api_view(timeout=2, key_prefix='api'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            cache_key = _make_cache_key(
                key_prefix,
                request.method,
                request.path,
                request.GET.urlencode(),
                getattr(request.user, 'pk', ''),
            )

            cached = cache.get(cache_key)
            if cached is not None:
                if isinstance(cached, tuple):
                    status_code, data = cached
                    return Response(data, status=status_code)
                return Response(cached)

            inflight_key = 'inflight:' + cache_key
            acquired, _ = _inflight.acquire(inflight_key)

            if not acquired:
                result, error = _inflight.wait(inflight_key, timeout=15)
                if error:
                    return error
                if result is not None:
                    cache.set(cache_key, result, timeout)
                    if isinstance(result, tuple):
                        return Response(result[1], status=result[0])
                    return Response(result)

            try:
                response = view_func(request, *args, **kwargs)
                if isinstance(response, Response):
                    cache_value = (response.status_code, response.data)
                elif isinstance(response, JsonResponse):
                    cache_value = (response.status_code, json.loads(response.content))
                else:
                    return response

                cache.set(cache_key, cache_value, timeout)
                _inflight.release(inflight_key, result=cache_value)
                return response
            except Exception as e:
                _inflight.release(inflight_key, error=Response(
                    {'detail': str(e)}, status=500
                ))
                raise
        return wrapper
    return decorator


def invalidate_patterns(*patterns):
    cache.delete_many(list(patterns))


class BatchSubmittedCounter:
    @staticmethod
    def build_map(games):
        from decisions.models import Decision
        from django.db.models import Count, Q

        game_ids = [g.pk for g in games]
        if not game_ids:
            return {}

        conditions = Q()
        for g in games:
            if g.current_round > 0:
                conditions |= Q(game_id=g.pk, round_number=g.current_round)

        if not conditions:
            return {}

        qs = Decision.objects.filter(
            conditions, is_submitted=True
        ).values('game_id').annotate(cnt=Count('id'))

        result = {row['game_id']: row['cnt'] for row in qs}
        return result
