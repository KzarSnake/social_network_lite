from core.models import CreationDateModel
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Название группы', max_length=200)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Идентификатор ссылки',
        help_text='Введите короткое слово на английском',
    )
    description = models.TextField('Описание группы')

    def __str__(self):
        return self.title


class Post(CreationDateModel):
    text = models.TextField('Текст записи', help_text='Введите ваш текст')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор записи',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа записи',
        help_text='Выберите группу',
    )
    image = models.ImageField('Картинка', upload_to='posts/', blank=True)

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'


class Comment(CreationDateModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментируемая запись',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )
    text = models.TextField('Комментарий', help_text='Введите ваш текст')

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписки',
    )
