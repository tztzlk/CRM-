from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Stage(models.Model):
    name = models.CharField('Название', max_length=100)
    order = models.PositiveSmallIntegerField('Порядок', default=0)
    is_won = models.BooleanField('Финальный — успех', default=False)
    is_lost = models.BooleanField('Финальный — отказ', default=False)
    color = models.CharField('Цвет', max_length=20, default='#0d6efd',
                             help_text='HEX-цвет для шапки колонки')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Этап воронки'
        verbose_name_plural = 'Этапы воронки'

    def __str__(self) -> str:
        return self.name


class Deal(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Открыта'
        WON = 'won', 'Успех'
        LOST = 'lost', 'Отказ'

    title = models.CharField('Название', max_length=200)
    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE,
        related_name='deals', verbose_name='Клиент',
    )
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2, default=0)
    stage = models.ForeignKey(
        Stage, on_delete=models.PROTECT,
        related_name='deals', verbose_name='Этап',
    )
    status = models.CharField('Статус', max_length=10,
                              choices=Status.choices, default=Status.OPEN)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='deals', verbose_name='Ответственный',
    )
    expected_close_date = models.DateField('Ожидаемая дата закрытия', null=True, blank=True)
    notes = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    closed_at = models.DateTimeField('Закрыта', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('deals:detail', kwargs={'pk': self.pk})

    def apply_stage_status(self):
        """Sync status/closed_at with the current stage's flags."""
        if self.stage.is_won:
            self.status = self.Status.WON
            self.closed_at = self.closed_at or timezone.now()
        elif self.stage.is_lost:
            self.status = self.Status.LOST
            self.closed_at = self.closed_at or timezone.now()
        else:
            self.status = self.Status.OPEN
            self.closed_at = None
