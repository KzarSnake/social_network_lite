from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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
        """Набор страниц доступен для неавторизованного пользователя."""
        testing_guest_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
            reverse('posts:post_detail', args=[self.post.id]),
        )
        for url in testing_guest_urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_accessible_for_authorized(self):
        """Страницы сайта доступны авторизованному пользователю."""
        testing_auth_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
            reverse('posts:post_detail', args=[self.post.id]),
            reverse('posts:post_edit', args=[self.post.id]),
            reverse('posts:post_create'),
            reverse('posts:add_comment', args=[self.post.id]),
            reverse('posts:follow_index'),
        )
        for url in testing_auth_urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_authorized(self):
        """Страницы подписки и отписки доступны авторизованному
        пользователю, но редиректят его на страницу автора."""
        urls_and_redirects = {
            reverse(
                'posts:profile_follow', args=[self.user.username]
            ): reverse('posts:profile', args=[self.user.username]),
            reverse(
                'posts:profile_unfollow', args=[self.user.username]
            ): reverse('posts:profile', args=[self.user.username]),
        }
        for url, redirect in urls_and_redirects.items():
            with self.subTest():
                response = self.authorized_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_wrong_url_get_404(self):
        """Страница /unexisting_page/ возвращает код 404
        и использует верный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_redirect_guest(self):
        """Страницы: редактирования и создания записи, ленты подписок,
        создания комментария, подписки и отписки перенаправят гостя
        на страницу авторизации."""
        # Здесь попытка записать /auth/login/?next= c добавлением reverse
        # приводит, на мой взгляд, к слишком некрасивому награмождению кода.
        urls_and_redirects = {
            reverse('posts:post_create'): '/auth/login/?next=/create/',
            reverse('posts:follow_index'): '/auth/login/?next=/follow/',
            reverse(
                'posts:post_edit', args=[self.post.id]
            ): f'/auth/login/?next=/posts/{self.post.id}/edit/',
            reverse(
                'posts:add_comment', args=[self.post.id]
            ): f'/auth/login/?next=/posts/{self.post.id}/comment/',
            reverse(
                'posts:profile_follow', args=[self.user.username]
            ): f'/auth/login/?next=/profile/{self.user.username}/follow/',
            reverse(
                'posts:profile_unfollow', args=[self.user.username]
            ): f'/auth/login/?next=/profile/{self.user.username}/unfollow/',
        }
        for url, redirect in urls_and_redirects.items():
            with self.subTest():
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """Страницы приложения используют верные шаблоны."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:follow_index'): 'posts/follow.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list', args=[self.group.slug]
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=[self.user.username]
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args=[self.post.id]
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', args=[self.post.id]
            ): 'posts/create_post.html',
            reverse(
                'posts:add_comment', args=[self.post.id]
            ): 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
