import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test.gif',
            content=cls.test_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_create_post(self):
        """Тест проверяет что, валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        context = {
            'text': 'Новый тестовый пост',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=context['text'],
                group=self.group,
                author=self.user,
                image='posts/test.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Тест проверяет что, валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='test-slug-new',
            description='Новое тестовое описание',
        )
        context = {
            'text': 'Новый тестовый пост изменен',
            'group': new_group.id
        }
        response = self.authorized_user.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ),
            data=context,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=context['text'],
                group=context['group'],
                author=self.user
            ).exists()
        )

    def test_guest_user_cant_publish_post(self):
        """Тест проверяет что, неавторизованный
        пользователь не может создать пост."""
        posts_count = Post.objects.count()
        context = {
            'text': 'Новый тестовый пост',
            'group': self.group.pk
        }
        response = self.guest_user.post(
            reverse('posts:post_create'),
            data=context,
            follow=True,
        )
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
        self.assertFalse(Post.objects.filter(
            text=context['text'],
            group=context['group']
        ).exists())
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )

    def test_guest_user_cant_publish_comment(self):
        """Неавторизованный пользователь
        не может опубликовать комментарий."""
        comment_count = Comment.objects.count()
        form = {
            'text': 'Новый тестовый комментарий'
        }
        response = self.guest_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form,
            follow=True,
        )
        self.assertNotEqual(Comment.objects.count(), comment_count + 1)
        self.assertFalse(Comment.objects.filter(
            text=form['text'],
            post=self.post.pk
        ).exists())
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse(
                'post:add_comment',
                kwargs={'post_id': self.post.id}
            )
        )

    def test_comment_push_and_shows_on_page(self):
        """После отправки комментарий попадает на страницу поста."""
        comment_count = Comment.objects.count()
        form = {
            'text': 'Новый тестовый комментарий'
        }
        response = self.authorized_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form,
            follow=True,
        )
        self.assertIn('form', response.context)
        last_comment = response.context['comments'][0]
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form['text'],
            post=self.post.pk
        ).exists())
        self.assertEqual(form['text'], last_comment.text)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        response = self.authorized_user.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        last_comment = response.context['comments'][0]
        self.assertEqual(form['text'], last_comment.text)
