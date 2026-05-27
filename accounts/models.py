from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        MANAGER = 'manager', 'Менеджер'
        VIEWER = 'viewer', 'Наблюдатель'

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.MANAGER,
        verbose_name='Роль',
    )
    phone = models.CharField(max_length=32, blank=True, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_manager(self) -> bool:
        return self.role == self.Role.MANAGER or self.is_admin()

    def can_edit(self) -> bool:
        return self.role in (self.Role.ADMIN, self.Role.MANAGER) or self.is_superuser

    def __str__(self) -> str:
        return self.get_full_name() or self.username
