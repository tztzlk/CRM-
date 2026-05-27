from django.conf import settings
from django.db import models


class Interaction(models.Model):
    class Type(models.TextChoices):
        CALL = 'call', 'Звонок'
        EMAIL = 'email', 'Email'
        MEETING = 'meeting', 'Встреча'
        NOTE = 'note', 'Заметка'
        MESSAGE = 'message', 'Сообщение'

    client = models.ForeignKey(
        'clients.Client', on_delete=models.CASCADE,
        related_name='interactions', verbose_name='Клиент',
    )
    deal = models.ForeignKey(
        'deals.Deal', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='interactions', verbose_name='Сделка',
    )
    type = models.CharField('Тип', max_length=16, choices=Type.choices, default=Type.NOTE)
    subject = models.CharField('Тема', max_length=200, blank=True)
    content = models.TextField('Содержание')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='interactions', verbose_name='Автор',
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Взаимодействие'
        verbose_name_plural = 'История взаимодействий'

    def __str__(self) -> str:
        return f'{self.get_type_display()}: {self.subject or self.content[:30]}'

    def icon(self) -> str:
        return {
            'call': 'bi-telephone',
            'email': 'bi-envelope',
            'meeting': 'bi-people',
            'note': 'bi-sticky',
            'message': 'bi-chat-dots',
        }.get(self.type, 'bi-circle')
