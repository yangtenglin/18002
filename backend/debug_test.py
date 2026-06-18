from django.test import TestCase, Client
from django.core.cache import cache
from users.models import User


class DebugTest(TestCase):
    def test_classroom_creation(self):
        cache.clear()
        self.client = Client()
        self.teacher = User.objects.create_user(
            username='teacher_test', password='testpass123',
            role='teacher', email='teacher@test.com'
        )
        self.client.login(username='teacher_test', password='testpass123')
        resp = self.client.post('/api/classrooms/', {'name': 'test_class', 'description': 'test'})
        print('Status:', resp.status_code)
        print('Data:', resp.data)
        if resp.status_code == 201:
            classroom_id = resp.data['id']
            resp2 = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': 'Team A'})
            print('Team Status:', resp2.status_code)
            print('Team Data:', resp2.data)
