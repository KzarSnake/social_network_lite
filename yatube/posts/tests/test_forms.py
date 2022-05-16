import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create_in_database(self):
        """Валидная форма создаёт запись в базе."""
        all_user_posts = len(self.user.posts.all())
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_gif = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'Создаем тестовую запись из формы',
            'image': uploaded_gif,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )

        self.assertGreater(len(response.context['page_obj']), all_user_posts)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=form_data['group'],
                image=f'posts/{form_data["image"]}',
            ).exists()
        )

    def test_post_edit_in_database(self):
        """Валидная форма изменяет запись в базе."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовая запись с текстом от Автора',
        )
        form_data = {
            'text': 'Новый текст, измененный через форму',
            'group': self.group.id,
        }
        post_old_id = post.id
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_edit', args=[post.id]),
            data=form_data,
        )
        post.refresh_from_db()
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.id, post_old_id)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.text, form_data['text'])


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_created_in_database(self):
        """Валидная форма создает комментарий к записи."""
        post = Post.objects.create(
            author=self.user,
            text='Тестовая запись с текстом от Автора',
            group=self.group,
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Наш очень важный комментарий!',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[post.id]),
            data=form_data,
            follow=True,
        )
        self.assertGreater(len(response.context['comments']), comments_count)
        self.assertEqual(
            response.context['comments'][0].text, form_data['text']
        )
