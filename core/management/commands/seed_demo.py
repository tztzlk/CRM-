"""Create a demo dataset for the CRM (users, stages, clients, deals, interactions)."""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from clients.models import Client
from deals.models import Stage, Deal
from interactions.models import Interaction
from leads.models import Lead

User = get_user_model()


STAGES = [
    {'name': 'Новая', 'order': 1, 'color': '#0d6efd'},
    {'name': 'Квалификация', 'order': 2, 'color': '#6f42c1'},
    {'name': 'Переговоры', 'order': 3, 'color': '#fd7e14'},
    {'name': 'Договор', 'order': 4, 'color': '#20c997'},
    {'name': 'Успех', 'order': 5, 'color': '#198754', 'is_won': True},
    {'name': 'Отказ', 'order': 6, 'color': '#6c757d', 'is_lost': True},
]

CLIENTS = [
    ('Асқар Нұрланұлы Жақсыбеков', 'ТОО Ромашка', 'askar@romashka.kz', '+7 700 100-10-10', 'website'),
    ('Петрова Анна Сергеевна', 'ИП Петрова', 'a.petrova@gmail.com', '+7 701 222-33-44', 'referral'),
    ('Бауыржан Сейітұлы Қасымов', 'АО Стройпром', 'bauryzhan@stroyprom.kz', '+7 702 555-77-99', 'ads'),
    ('Айгүл Маратқызы Дүйсенова', 'ТОО Цветочный мир', 'aigul@flowers.kz', '+7 705 333-22-11', 'social'),
    ('Дәурен Алмасұлы Байжанов', 'ТОО ТехноСтиль', 'dauren@technostyle.kz', '+7 707 777-88-99', 'website'),
    ('Лебедева Ольга', 'ИП Лебедева', 'olga.lebedeva@mail.ru', '+7 708 111-22-33', 'referral'),
    ('Нұржан Ерланұлы Сейітқали', 'ТОО АльфаТрейд', 'nurzhan@alfatrade.kz', '+7 747 444-55-66', 'ads'),
    ('Дина Қайратқызы Әбенова', 'ТОО Бьюти Студио', 'dina@beauty.kz', '+7 771 666-77-88', 'other'),
]

DEAL_TITLES = [
    'Поставка офисной мебели', 'Внедрение 1С', 'Разработка сайта',
    'Установка СКУД', 'Закупка оборудования', 'Сопровождение бухгалтерии',
    'Контракт на обслуживание', 'Рекламная кампания', 'Аудит безопасности',
    'Поставка канцтоваров', 'Внедрение CRM', 'Аренда сервера',
]


class Command(BaseCommand):
    help = 'Создаёт демо-данные для CRM'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Очистить данные перед заполнением')

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('Очищаю данные...')
            Interaction.objects.all().delete()
            Deal.objects.all().delete()
            Client.objects.all().delete()
            Lead.objects.all().delete()
            Stage.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        # Users
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={'role': User.Role.ADMIN, 'is_staff': True, 'is_superuser': True,
                      'first_name': 'Админ', 'last_name': 'Системы', 'email': 'admin@example.com'},
        )
        admin.set_password('admin123')
        admin.role = User.Role.ADMIN
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        manager, _ = User.objects.get_or_create(
            username='manager',
            defaults={'role': User.Role.MANAGER, 'first_name': 'Менеджер', 'last_name': 'Продаж',
                      'email': 'manager@example.com'},
        )
        manager.set_password('manager123')
        manager.role = User.Role.MANAGER
        manager.save()

        manager2, _ = User.objects.get_or_create(
            username='manager2',
            defaults={'role': User.Role.MANAGER, 'first_name': 'Елена', 'last_name': 'Иванова',
                      'email': 'elena@example.com'},
        )
        manager2.set_password('manager123')
        manager2.role = User.Role.MANAGER
        manager2.save()

        viewer, _ = User.objects.get_or_create(
            username='viewer',
            defaults={'role': User.Role.VIEWER, 'first_name': 'Наблюдатель',
                      'last_name': 'Отчётов', 'email': 'viewer@example.com'},
        )
        viewer.set_password('viewer123')
        viewer.role = User.Role.VIEWER
        viewer.save()

        # Stages
        for s in STAGES:
            Stage.objects.update_or_create(
                name=s['name'],
                defaults={
                    'order': s['order'],
                    'color': s['color'],
                    'is_won': s.get('is_won', False),
                    'is_lost': s.get('is_lost', False),
                },
            )
        stages = list(Stage.objects.order_by('order'))
        open_stages = [s for s in stages if not s.is_won and not s.is_lost]
        won_stage = next(s for s in stages if s.is_won)
        lost_stage = next(s for s in stages if s.is_lost)
        managers = [manager, manager2]

        # Clients
        clients = []
        for full_name, company, email, phone, source in CLIENTS:
            c, _ = Client.objects.update_or_create(
                full_name=full_name,
                defaults={'company': company, 'email': email, 'phone': phone,
                          'source': source, 'owner': random.choice(managers)},
            )
            clients.append(c)

        # Deals
        rnd = random.Random(42)
        now = timezone.now()
        for i in range(20):
            client = rnd.choice(clients)
            title = rnd.choice(DEAL_TITLES)
            amount = Decimal(rnd.randrange(15000, 500000, 5000))
            roll = rnd.random()
            if roll < 0.55:
                stage = rnd.choice(open_stages)
            elif roll < 0.85:
                stage = won_stage
            else:
                stage = lost_stage
            created = now - timedelta(days=rnd.randrange(0, 90))
            deal = Deal.objects.create(
                title=f'{title} ({client.company})',
                client=client,
                amount=amount,
                stage=stage,
                owner=rnd.choice(managers),
                expected_close_date=(created + timedelta(days=30)).date(),
                notes='Демо-сделка для дипломного проекта.',
            )
            deal.apply_stage_status()
            Deal.objects.filter(pk=deal.pk).update(
                created_at=created,
                status=deal.status,
                closed_at=deal.closed_at,
            )

        # Interactions
        types = ['call', 'email', 'meeting', 'note', 'message']
        for client in clients:
            for _ in range(rnd.randrange(1, 5)):
                deal = client.deals.order_by('?').first()
                Interaction.objects.create(
                    client=client,
                    deal=deal,
                    type=rnd.choice(types),
                    subject=rnd.choice(['Первый контакт', 'Обсуждение цены', 'Уточнение деталей',
                                        'Согласование договора', 'Звонок по статусу']),
                    content='Демо-запись истории взаимодействия.',
                    author=rnd.choice(managers),
                )

        # Leads
        LEAD_DATA = [
            ('Ерлан Серікұлы Мұқанов', 'ТОО МегаСтрой', 'erlan@megastroy.kz', '+7 776 100-20-30', 'ads', 'new'),
            ('Фролова Ксения', '', 'frolova@mail.ru', '+7 777 200-30-40', 'social', 'in_progress'),
            ('Попов Геннадий', 'ИП Попов', 'popov@gmail.com', '+7 778 300-40-50', 'website', 'qualified'),
            ('Зарина Болатқызы Сүлейменова', 'ТОО Цифра', 'zarina@tsifra.kz', '+7 747 400-50-60', 'referral', 'new'),
            ('Тимур Ғалымұлы Ахметов', 'АО Логик', 'timur@logik.kz', '+7 700 500-60-70', 'ads', 'in_progress'),
            ('Белова Светлана', 'ИП Белова', 'belova@mail.ru', '+7 701 600-70-80', 'other', 'rejected'),
        ]
        for full_name, company, email, phone, source, status in LEAD_DATA:
            Lead.objects.get_or_create(
                full_name=full_name,
                defaults={
                    'company': company, 'email': email, 'phone': phone,
                    'source': source, 'status': status,
                    'owner': rnd.choice(managers),
                    'notes': 'Демо-лид для дипломного проекта.',
                },
            )

        self.stdout.write(self.style.SUCCESS('Готово!'))
        self.stdout.write('Логины: admin/admin123, manager/manager123, manager2/manager123, viewer/viewer123')
