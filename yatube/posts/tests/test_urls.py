from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_is_not_author = User.objects.create_user(
            username='NotAuthor'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            group=cls.group,
            author=cls.user
        )
        cls.urls_list_public = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            ): 'posts/post_detail.html',
        }
        cls.urls_list_public_code = {
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'bad_slug'}
            ): HTTPStatus.NOT_FOUND,
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
            ): HTTPStatus.FOUND,
            reverse('posts:post_create'): HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        cls.urls_list_authorized_user = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            ): 'posts/post_detail.html',
        }
        cls.urls_list_authorized_user_code = {
            reverse('posts:post_create'): HTTPStatus.OK,
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
            ): HTTPStatus.OK,
            reverse('posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): HTTPStatus.OK,
            reverse(
                'posts:group_list',
                kwargs={'slug': 'bad_slug'}
            ): HTTPStatus.NOT_FOUND,
            reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
            ): HTTPStatus.OK,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.pk}
            ): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        cls.post_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.not_author_user = Client()
        self.authorized_user.force_login(self.user)
        self.not_author_user.force_login(
            PostsURLTests.user_is_not_author)
        cache.clear()

    def test_url_exists_for_guest(self):
        """Тест проверяет доступность страниц неавторизованному пользователю"""
        for address, code in PostsURLTests.urls_list_public_code.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertEqual(response.status_code, code)

    def test_url_exists_for_authorized(self):
        """Тест проверяет доступность страниц авторизованному пользователю"""
        for (
            address,
            code
        ) in PostsURLTests.urls_list_authorized_user_code.items():
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template_for_guest(self):
        """Тест на использование корректных шаблонов по адресам
        для неавторизованного пользователя приложения posts."""
        for address, template in PostsURLTests.urls_list_public.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_authorized(self):
        """Тест на использование корректных шаблонов по адресам
        для авторизованного пользователя приложения posts."""
        for (
            address,
            template
        ) in PostsURLTests.urls_list_authorized_user.items():
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_redirects_for_guest(self):
        """Тест на редирект неавторизованного пользователя
        на страницу авторизации."""
        urls_redirect_dict = {
            reverse('posts:post_create'): '/auth/login/?next=/create/',
            reverse('posts:post_edit', kwargs={'post_id': 1}):
                '/auth/login/?next=/posts/1/edit/',
        }
        for address, redirect in urls_redirect_dict.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, redirect)

    def test_url_redirect_for_authorized(self):
        """Тест на редирект не автора поста
        на страницу поста при редактировании."""
        response = self.not_author_user.get(PostsURLTests.post_edit_url)
        self.assertRedirects(
            response, PostsURLTests.post_url
        )
