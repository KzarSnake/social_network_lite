import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Follow, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовая запись с текстом от Автора',
            author=cls.user,
            group=cls.test_group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', args=[self.test_group.slug]
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
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_show_correct_context(self):
        """Шаблон home сформирован со списком записей."""
        response = self.authorized_client.get(reverse('posts:index'))
        test_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(self.post, test_post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован со списком записей
        отфильтрованных по группе.
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.test_group.slug])
        )
        test_post = response.context.get('page_obj').object_list[0]
        self.assertEqual(self.test_group.slug, test_post.group.slug)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован со списком записей
        отфильтрованных по пользователю.
        """
        response = self.authorized_client.get(
            reverse('posts:profile', args=[self.user.username])
        )
        test_post = response.context['page_obj'].object_list[0]
        self.assertEqual(self.user.username, test_post.author.username)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с записями
        отфильтрованными по id.
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.id])
        )
        test_post = response.context.get('post')
        self.assertEqual(self.post.id, test_post.id)

    def test_post_edit_show_correct_context(self):
        """Форма post_edit сформирована с содержимым полей,
        взятым из записи, отфильтрованной по id.
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.id])
        )
        self.assertEqual(response.context['post'].id, self.post.id)
        self.assertEqual(
            response.context['form'].initial['text'], self.post.text
        )
        self.assertEqual(
            response.context['form'].initial['group'], self.post.group.id
        )

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильной формой."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertTrue('form' in response.context)
                self.assertIsInstance(response.context['form'], PostForm)
                self.assertTrue('is_edit' in response.context)

    def test_new_post_added_right_pages(self):
        """Новая запись появляется на главной странице,
        на странице группы и в профиле пользователя.
        """
        new_post = Post.objects.create(
            text='Очень важный текст новой записи!',
            author=self.user,
            group=self.test_group,
        )
        expected_pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.test_group.slug]),
            reverse('posts:profile', args=[self.user.username]),
        ]
        for reverse_page in expected_pages:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                self.assertIn(new_post, response.context['page_obj'])

    def test_post_not_in_wrong_group(self):
        """Новая запись не попала на страницу другой группы."""
        new_group = Group.objects.create(
            title='Новая группа',
            slug='new-slug',
            description='Тестовое описание для новой группы',
        )
        new_post = Post.objects.create(
            text='Новая запись в новой группе',
            author=self.user,
            group=new_group,
        )
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[self.test_group.slug])
        )
        self.assertNotIn(new_post, response.context['page_obj'])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_gif = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='author')
        cls.test_group = Group.objects.create(
            title='Группа с изображениями',
            slug='img-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовая запись с текстом от Автора',
            author=cls.user,
            group=cls.test_group,
            image=cls.uploaded_gif,
        )
        cls.page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[cls.test_group.slug]),
            reverse('posts:profile', args=[cls.user.username]),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_image_includes_in_context(self):
        """Изображение передается в контексте главной страницы,
        страницы группы и профиля пользователя."""
        for reverse_name in self.page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIsNotNone(response.context.get('page_obj')[0].image)

    def test_image_includes_in_post_detail(self):
        """Изображение передается в контексте страницы записи."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.id])
        )
        self.assertIsNotNone(response.context.get('post').image)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Запись для тестирования кэша.',
            author=cls.user,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_index(self):
        """Тест кэша на главной странице."""
        init_response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.get(pk=self.post.id).delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(init_response.content, response.content)
        cache.clear()
        clear_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(clear_response.content, response.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)

    def test_follow_available_for_auth_client(self):
        """Тестирование доступности функции подписки для
        авторизованного пользователя."""
        init_follow_count = len(Follow.objects.filter(user=self.follower))
        self.authorized_follower.get(
            reverse('posts:profile_follow', args=[self.author.username])
        )
        mod_follow_count = len(Follow.objects.filter(user=self.follower))
        self.assertGreater(mod_follow_count, init_follow_count)

    def test_unfollow_available_for_auth_client(self):
        """Тестирование доступности функции отписки для
        авторизованного пользователя."""
        Follow.objects.get_or_create(user=self.follower, author=self.author)
        init_follow_count = len(Follow.objects.filter(user=self.follower))
        self.authorized_follower.get(
            reverse('posts:profile_unfollow', args=[self.author.username])
        )
        mod_follow_count = len(Follow.objects.filter(user=self.follower))
        self.assertLess(mod_follow_count, init_follow_count)

    def test_new_post_get_to_follow_index(self):
        """Тестирование работоспособности ленты подписок:
        новая запись появилась в ленте подписки и не появилась в ленте
        того, кто не подписан."""
        self.not_follower = User.objects.create_user(username='not_follower')
        self.authorized_not_follower = Client()
        self.authorized_not_follower.force_login(self.not_follower)
        Follow.objects.get_or_create(user=self.follower, author=self.author)
        post = Post.objects.create(
            text='Запись для тестирования подписок.',
            author=self.author,
        )
        follower_response = self.authorized_follower.get(
            reverse('posts:follow_index')
        )
        self.assertIn(post, follower_response.context['page_obj'])
        not_follower_response = self.authorized_not_follower.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(post, not_follower_response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.test_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = Post.objects.bulk_create(
            [
                Post(
                    text='Тестовая запись с некоторым текстом',
                    author=cls.user,
                    group=cls.test_group,
                )
                for _ in range(settings.POSTS_PER_PAGE * 2 - 1)
            ]
        )
        cls.page_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[cls.test_group.slug]),
            reverse('posts:profile', args=[cls.user.username]),
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Первая страница содержит нужное количество записей."""
        for reverse_name in self.page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        """Вторая страница содержит нужное количество записей."""
        for reverse_name in self.page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    len(self.posts) - settings.POSTS_PER_PAGE,
                )
