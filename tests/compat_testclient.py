from fastapi.testclient import TestClient


class CompatTestClient(TestClient):
    def delete(self, url, *args, **kwargs):
        if 'json' in kwargs:
            payload = kwargs.pop('json')
            if payload is not None:
                kwargs['params'] = {**(kwargs.get('params') or {}), **payload}
        return super().delete(url, *args, **kwargs)
