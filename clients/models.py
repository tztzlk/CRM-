from django.conf import settings
from django.db import models
from django.urls import reverse


class Client(models.Model):
    class Source(models.TextChoices):
        WEBSITE = 'website', 'Сайт'
        REFERRAL = 'referral', 'Рекомендация'
        ADS = 'ads', 'Реклама'
        SOCIAL = 'social', 'Соцсети'
        OTHER = 'other', 'Другое'

    full_name = models.CharField('ФИО', max_length=200)
    company = models.CharField('Компания', max_length=200, blank=True)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Телефон', max_length=32, blank=True)
    source = models.CharField('Источник', max_length=16, choices=Source.choices, default=Source.OTHER)
    notes = models.TextField('Заметки', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='clients',
        verbose_name='Ответственный',
    )
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        indexes = [
            models.Index(fields=['full_name']),
            models.Index(fields=['company']),
        ]

    def __str__(self) -> str:
        return self.full_name

    def get_absolute_url(self) -> str:
        return reverse('clients:detail', kwargs={'pk': self.pk})
