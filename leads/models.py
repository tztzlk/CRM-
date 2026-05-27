from django.conf import settings
from django.db import models
from django.urls import reverse


class Lead(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        IN_PROGRESS = 'in_progress', 'В работе'
        QUALIFIED = 'qualified', 'Квалифицирован'
        CONVERTED = 'converted', 'Конвертирован'
        REJECTED = 'rejected', 'Отказ'

    class Source(models.TextChoices):
        WEBSITE = 'website', 'Сайт'
        REFERRAL = 'referral', 'Рекомендация'
        ADS = 'ads', 'Реклама'
        SOCIAL = 'social', 'Соцсети'
        OTHER = 'other', 'Другое'

    class Priority(models.TextChoices):
        HOT = 'hot', '🔥 Горячий'
        WARM = 'warm', '🟡 Тёплый'
        COLD = 'cold', '🔵 Холодный'

    class Industry(models.TextChoices):
        IT = 'it', 'IT / Технологии'
        RETAIL = 'retail', 'Розничная торговля'
        MANUFACTURING = 'manufacturing', 'Производство'
        FINANCE = 'finance', 'Финансы / Банки'
        REAL_ESTATE = 'real_estate', 'Недвижимость'
        HEALTHCARE = 'healthcare', 'Здравоохранение'
        EDUCATION = 'education', 'Образование'
        CONSTRUCTION = 'construction', 'Строительство'
        LOGISTICS = 'logistics', 'Логистика / Транспорт'
        FOOD = 'food', 'Общепит / Продукты'
        BEAUTY = 'beauty', 'Красота / Здоровье'
        OTHER = 'other', 'Другое'

    class CompanySize(models.TextChoices):
        SOLO = 'solo', 'Самозанятый / ИП'
        SMALL = 'small', '2–10 человек'
        MEDIUM = 'medium', '11–50 человек'
        LARGE = 'large', '51–200 человек'
        ENTERPRISE = 'enterprise', '200+ человек'

    class ContactPreference(models.TextChoices):
        PHONE = 'phone', 'Телефон'
        EMAIL = 'email', 'Email'
        TELEGRAM = 'telegram', 'Telegram'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        ANY = 'any', 'Любой'

    class DealUrgency(models.TextChoices):
        IMMEDIATE = 'immediate', 'Срочно (до 1 недели)'
        MONTH = 'month', 'В этом месяце'
        QUARTER = 'quarter', 'В этом квартале'
        YEAR = 'year', 'В этом году'
        UNKNOWN = 'unknown', 'Не определено'

    # ── Контактная информация ─────────────────────────────────────────────────
    full_name = models.CharField('ФИО / Контактное лицо', max_length=200)
    position = models.CharField('Должность', max_length=120, blank=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    phone_alt = models.CharField('Доп. телефон', max_length=32, blank=True)
    email = models.EmailField('Email', blank=True)
    telegram = models.CharField('Telegram', max_length=64, blank=True,
                                help_text='@username или номер телефона')
    contact_preference = models.CharField(
        'Предпочтительный способ связи', max_length=16,
        choices=ContactPreference.choices, blank=True,
    )

    # ── Компания ──────────────────────────────────────────────────────────────
    company = models.CharField('Компания', max_length=200, blank=True)
    industry = models.CharField(
        'Отрасль', max_length=20, choices=Industry.choices, blank=True,
    )
    company_size = models.CharField(
        'Размер компании', max_length=16, choices=CompanySize.choices, blank=True,
    )
    city = models.CharField('Город / Регион', max_length=100, blank=True)
    website = models.URLField('Сайт компании', blank=True)

    # ── Сделка ────────────────────────────────────────────────────────────────
    source = models.CharField('Источник', max_length=16, choices=Source.choices, default=Source.OTHER)
    status = models.CharField('Статус', max_length=16, choices=Status.choices, default=Status.NEW)
    product_interest = models.TextField('Интерес / Потребность', blank=True,
                                        help_text='Что ищет клиент, какая задача')
    estimated_amount = models.DecimalField(
        'Потенциальная сумма (₽)', max_digits=12, decimal_places=2, null=True, blank=True,
    )
    deal_urgency = models.CharField(
        'Срочность сделки', max_length=16, choices=DealUrgency.choices,
        default=DealUrgency.UNKNOWN, blank=True,
    )
    next_contact_date = models.DateField('Дата следующего контакта', null=True, blank=True)
    notes = models.TextField('Заметки / Комментарии', blank=True)

    # ── UTM-метки ─────────────────────────────────────────────────────────────
    utm_source = models.CharField('UTM Source', max_length=100, blank=True)
    utm_medium = models.CharField('UTM Medium', max_length=100, blank=True)
    utm_campaign = models.CharField('UTM Campaign', max_length=100, blank=True)

    # ── Управление ────────────────────────────────────────────────────────────
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='leads',
        verbose_name='Ответственный',
    )
    converted_client = models.ForeignKey(
        'clients.Client',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='from_leads',
        verbose_name='Клиент после конвертации',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    # ── AI scoring ────────────────────────────────────────────────────────────
    score = models.IntegerField('AI-скоринг', default=0)
    priority = models.CharField(
        'Приоритет', max_length=8, choices=Priority.choices, default=Priority.COLD,
    )
    score_updated_at = models.DateTimeField('Скоринг обновлён', null=True, blank=True)
    first_contact_at = models.DateTimeField('Первый контакт', null=True, blank=True)
    response_speed_hours = models.FloatField('Скорость ответа клиента (ч)', null=True, blank=True)

    class Meta:
        ordering = ['-score', '-created_at']
        verbose_name = 'Лид'
        verbose_name_plural = 'Лиды'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['full_name']),
            models.Index(fields=['priority']),
            models.Index(fields=['-score']),
        ]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse('leads:detail', kwargs={'pk': self.pk})

    @property
    def status_badge_class(self) -> str:
        return {
            'new': 'bg-primary',
            'in_progress': 'bg-warning text-dark',
            'qualified': 'bg-info text-dark',
            'converted': 'bg-success',
            'rejected': 'bg-secondary',
        }.get(self.status, 'bg-light text-dark')

    @property
    def priority_badge_class(self) -> str:
        return {
            'hot': 'bg-danger',
            'warm': 'bg-warning text-dark',
            'cold': 'bg-secondary',
        }.get(self.priority, 'bg-secondary')

    @property
    def priority_row_class(self) -> str:
        return {
            'hot': 'table-danger',
            'warm': 'table-warning',
            'cold': '',
        }.get(self.priority, '')


class LeadInteraction(models.Model):
    class Type(models.TextChoices):
        CALL = 'call', 'Звонок'
        EMAIL = 'email', 'Email'
        MEETING = 'meeting', 'Встреча'
        NOTE = 'note', 'Заметка'
        MESSAGE = 'message', 'Сообщение'

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name='interactions', verbose_name='Лид',
    )
    type = models.CharField('Тип', max_length=16, choices=Type.choices, default=Type.NOTE)
    content = models.TextField('Содержание')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='lead_interactions', verbose_name='Автор',
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Взаимодействие с лидом'
        verbose_name_plural = 'Взаимодействия с лидами'

    def __str__(self) -> str:
        return f'{self.get_type_display()}: {self.content[:40]}'

    def icon(self) -> str:
        return {
            'call': 'bi-telephone',
            'email': 'bi-envelope',
            'meeting': 'bi-people',
            'note': 'bi-sticky',
            'message': 'bi-chat-dots',
        }.get(self.type, 'bi-circle')


class LeadScoreLog(models.Model):
    class Reason(models.TextChoices):
        NEW = 'new', 'Новый лид'
        INTERACTION = 'new_interaction', 'Новое взаимодействие'
        TIME_DECAY = 'time_decay', 'Таймер'
        MANUAL = 'manual', 'Вручную'
        DATA_CHANGE = 'data_change', 'Изменение данных'

    lead = models.ForeignKey(
        Lead, on_delete=models.CASCADE, related_name='score_logs', verbose_name='Лид',
    )
    score_before = models.IntegerField('Балл до')
    score_after = models.IntegerField('Балл после')
    reason = models.CharField('Причина', max_length=32, choices=Reason.choices)
    created_at = models.DateTimeField('Время', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Лог скоринга'
        verbose_name_plural = 'Логи скоринга'

    def __str__(self) -> str:
        return f'Lead #{self.lead_id}: {self.score_before} → {self.score_after}'


class Achievement(models.Model):
    slug = models.SlugField('Slug', unique=True)
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание')
    icon = models.CharField('Иконка', max_length=10)
    condition_code = models.CharField('Код условия', max_length=50)

    class Meta:
        verbose_name = 'Достижение'
        verbose_name_plural = 'Достижения'

    def __str__(self) -> str:
        return self.name


class ManagerStats(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='manager_stats', verbose_name='Менеджер',
    )
    month = models.DateField('Месяц')
    deals_closed = models.IntegerField('Закрыто сделок', default=0)
    revenue = models.DecimalField('Выручка', max_digits=14, decimal_places=2, default=0)
    avg_response_min = models.FloatField('Среднее время реакции (мин)', default=0)
    conversion_rate = models.FloatField('Конверсия (%)', default=0)
    points = models.IntegerField('Очки', default=0)

    class Meta:
        unique_together = [['user', 'month']]
        ordering = ['-month', '-points']
        verbose_name = 'Статистика менеджера'
        verbose_name_plural = 'Статистика менеджеров'

    def __str__(self) -> str:
        return f'{self.user} — {self.month.strftime("%Y-%m")}'


class ManagerAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='achievements', verbose_name='Менеджер',
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, verbose_name='Достижение')
    earned_at = models.DateTimeField('Получено', auto_now_add=True)

    class Meta:
        unique_together = [['user', 'achievement']]
        ordering = ['-earned_at']
        verbose_name = 'Бейдж менеджера'
        verbose_name_plural = 'Бейджи менеджеров'

    def __str__(self) -> str:
        return f'{self.user} — {self.achievement}'
