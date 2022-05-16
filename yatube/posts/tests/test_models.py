from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись в базу данных',
            group=cls.group,
        )

    def test_post_str(self):
        """Выводит первые пятнадцать символов поста"""
        self.assertEqual(str(self.post), self.post.text[:15])

    def test_group_str(self):
        """Название группы совпадает"""
        self.assertEqual(str(self.group), self.group.title)
