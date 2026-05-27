import json

from django.contrib.auth import get_user_model
from django.test import TestCase, Client as TestClient
from django.urls import reverse

from clients.models import Client
from deals.models import Stage, Deal


User = get_user_model()


class SmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username='a', password='p', role=User.Role.ADMIN,
            is_staff=True, is_superuser=True,
        )
        cls.manager = User.objects.create_user(
            username='m', password='p', role=User.Role.MANAGER,
        )
        cls.viewer = User.objects.create_user(
            username='v', password='p', role=User.Role.VIEWER,
        )
        cls.s_open = Stage.objects.create(name='Новая', order=1)
        cls.s_won = Stage.objects.create(name='Успех', order=2, is_won=True)
        cls.client_obj = Client.objects.create(full_name='Тест', owner=cls.manager)
        cls.deal = Deal.objects.create(
            title='Тестовая', client=cls.client_obj, amount=100,
            stage=cls.s_open, owner=cls.manager,
        )

    def setUp(self):
        self.c = TestClient()

    def test_login_and_dashboard(self):
        self.assertTrue(self.c.login(username='m', password='p'))
        r = self.c.get('/')
        self.assertEqual(r.status_code, 200)

    def test_pages_load_for_admin(self):
        self.c.login(username='a', password='p')
        for path in ['/', '/clients/', '/deals/', '/deals/board/', '/reports/', '/auth/users/']:
            r = self.c.get(path)
            self.assertEqual(r.status_code, 200, f'{path} -> {r.status_code}')

    def test_kanban_move_ok_for_manager(self):
        self.c.login(username='m', password='p')
        r = self.c.post(
            reverse('deals:move', args=[self.deal.id]),
            data=json.dumps({'stage_id': self.s_won.id}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 200)
        self.deal.refresh_from_db()
        self.assertEqual(self.deal.stage_id, self.s_won.id)
        self.assertEqual(self.deal.status, 'won')

    def test_kanban_move_forbidden_for_viewer(self):
        self.c.login(username='v', password='p')
        r = self.c.post(
            reverse('deals:move', args=[self.deal.id]),
            data=json.dumps({'stage_id': self.s_won.id}),
            content_type='application/json',
        )
        self.assertEqual(r.status_code, 403)

    def test_admin_only_user_management(self):
        self.c.login(username='m', password='p')
        self.assertEqual(self.c.get('/auth/users/').status_code, 403)
        self.c.login(username='a', password='p')
        self.assertEqual(self.c.get('/auth/users/').status_code, 200)
