import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый пост {i}',
                group=cls.group
            )
            for i in range(13)
        ])
        cls.urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        )
        cls.posts_on_page = {
            1: settings.POST_COUNT,
            2: 3,
        }

    def setUp(self):
        cache.clear()
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_page_show_correct_count_posts(self):
        """Тест проверяет корректную работу пагинации на страницах."""
        for url in PaginatorViewsTest.urls:
            for page, count_post in self.posts_on_page.items():
                with self.subTest(page=page):
                    response = self.authorized_user.get(
                        f'{url}?page={page}')
                    count_obj = len(response.context['page_obj'])
                    self.assertEqual(count_obj, count_post)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
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
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.posts_urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug1'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
                'posts/profile.html',
                reverse('posts:post_detail', kwargs={'post_id': cls.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}):
                'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_posts_views_uses_correct_template(self):
        """Тест проверяет, что view использует правильный шаблон."""
        for name, template in PostsViewsTests.posts_urls.items():
            with self.subTest(name=name):
                response = self.authorized_user.get(name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def post_check(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Тест проверяет, что шаблон главной страницы
        сформирован с правильным контекстом."""
        response = self.authorized_user.get(reverse('posts:index'))
        self.post_check(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Тест проверяет, что шаблон группы
        сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug1'})
        )
        self.post_check(response.context['page_obj'][0])
        self.assertEqual(response.context['group'], self.group)

    def test_profile_page_show_correct_context(self):
        """Тест проверяет, что шаблон профиля
        сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        self.post_check(response.context['page_obj'][0])
        self.assertEqual(response.context['author'], self.user)

    def test_post_detail_page_show_correct_context(self):
        """Тест проверяет, что шаблон детали поста
        сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        post_response = response.context['post']
        self.post_check(post_response)

    def test_post_create_page_show_correct_context(self):
        """Тест проверяет, что шаблон создания и редактирования поста
        сформирован с правильным контекстом."""
        response = self.authorized_user.get(reverse('posts:post_create'))
        response_edit = self.authorized_user.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                form_field_edit = response_edit.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
                self.assertIsInstance(form_field_edit, expected)

    def test_post_with_group_is_on_pages(self):
        """Тест проверяет, что пост с группой появляется на страницах
        index, group_list, profile в нужной группе."""
        pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        ]
        for address in pages_names:
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertIn(self.post, response.context['page_obj'])

    def test_post_exist_in_group(self):
        """Тест проверяет, что при создании пост
        попадает в нужную группу."""
        another_group = Group.objects.create(
            slug='another_group_2',
            title='Другая тестовая группа 2',
            description='Тестовое описание другой группы 2'
        )
        another_url = reverse(
            'posts:group_list',
            kwargs={'slug': another_group.slug}
        )
        self.assertNotIn(
            self.post,
            self.authorized_user.get(another_url).context['page_obj']
        )

    def test_index_cache(self):
        """Кеширование index работает правильно."""
        response = self.authorized_user.get(reverse('posts:index'))
        context_count = response.context['page_obj'].count
        Post.objects.all().delete
        context_count_delete = response.context['page_obj'].count
        self.assertEqual(context_count, context_count_delete)


class FollowPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Author')
        cls.follower = User.objects.create_user(username='Follower')
        cls.not_follower = User.objects.create_user(username='NotFollower')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self):
        self.author_user = Client()
        self.follower_user = Client()
        self.not_follower_user = Client()
        self.author_user.force_login(FollowPagesTests.author)
        self.follower_user.force_login(FollowPagesTests.follower)
        self.not_follower_user.force_login(FollowPagesTests.not_follower)

    def test_authorized_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        self.follower_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowPagesTests.post.author}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                author=FollowPagesTests.post.author,
                user=FollowPagesTests.follower
            ).exists()
        )
        self.follower_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': FollowPagesTests.post.author}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=FollowPagesTests.post.author,
                user=FollowPagesTests.follower
            ).exists()
        )

    def test_new_post_appears_only_in_followers_list(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан.
        """
        self.follower_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowPagesTests.post.author}
            )
        )
        response_2 = self.follower_user.get(reverse('posts:follow_index'))
        response_3 = self.not_follower_user.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(
            response_2.context['page_obj']
            .paginator.page(1).object_list.count(), 1
        )
        self.assertEqual(
            response_3.context['page_obj']
            .paginator.page(1).object_list.count(), 0
        )
