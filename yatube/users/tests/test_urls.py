from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pages_guest_user = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse(
                'users:password_reset_form'
            ): 'users/password_reset_form.html',
            reverse(
                'users:password_reset_done'
            ): 'users/password_reset_done.html',
            reverse(
                'users:password_reset_complete'
            ): 'users/password_reset_complete.html',
        }
        cls.pages_authorized_user = {
            reverse(
                'users:password_change_form'
            ): 'users/password_change_form.html',
            reverse(
                'users:password_change_done'
            ): 'users/password_change_done.html',
            reverse('users:logout'): 'users/logged_out.html',
        }

    def setUp(self):
        self.user = User.objects.create_user(username='Auth')
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_url_exists_for_guest_user(self):
        """Тест проверяет доступность страниц для
        неавторизированного пользователя."""
        for address in UsersPagesTests.pages_guest_user:
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_for_authorized_user(self):
        """Тест проверяет доступность страниц для
        авторизированного пользователя."""
        for address in UsersPagesTests.pages_guest_user:
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        for address in UsersPagesTests.pages_authorized_user:
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_uses_correct_template_guest_user(self):
        """Тест проверяет корректность шаблонов для
        неавторизированного пользователя."""
        for address, template in UsersPagesTests.pages_guest_user.items():
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_authorized_user(self):
        """Тест проверяет корректность шаблонов для
        авторизированного пользователя."""
        for address, template in UsersPagesTests.pages_authorized_user.items():
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
        for address, template in UsersPagesTests.pages_guest_user.items():
            with self.subTest(address=address):
                response = self.authorized_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
