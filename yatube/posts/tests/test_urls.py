from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_accessible_for_guest(self):
        """Набор страниц доступен для любого пользователя"""
        testing_guest_urls = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        )
        for url in testing_guest_urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_accessible_for_authorized(self):
        """Страница /posts/1/edit/ доступна для автора, страница /create/
        доступна для авторизованного пользователя
        """
        testing_auth_urls = (
            f'/posts/{self.post.id}/edit/',
            '/create/',
        )
        for url in testing_auth_urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_wrong_url_get_404(self):
        """Страница /unexisting_page/ возвращает код 404
        и использует верный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_redirect_guest(self):
        """Страница /posts/1/edit/ перенаправит гостя на /posts/1/,
        страница /create/ перенаправит гостя на /auth/login/?next=/create/
        """
        urls_and_redirects = {
            f'/posts/{self.post.id}/edit/': f'/posts/{self.post.id}/',
            '/create/': '/auth/login/?next=/create/',
        }
        for url, redirect in urls_and_redirects.items():
            with self.subTest():
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """Страницы приложения используют верные шаблоны"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_comment_url_redirect_guest(self):
        response = self.client.get(f'/posts/{self.post.id}/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_comment_url_accept_authorized(self):
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
