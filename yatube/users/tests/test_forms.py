from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from users.forms import CreationForm

User = get_user_model()


class UsersCreationFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.form = CreationForm()

    def setUp(self):
        self.guest_user = Client()

    def test_increase_count_users_after_signup(self):
        """Тест проверяет, что количество пользователей
        увеличивается после регистрации нового."""
        users_count = User.objects.count()
        context = {
            'first_name': 'Petr',
            'last_name': 'Petrov',
            'username': 'Petrusha',
            'email': 'petrusha@mail.ru',
            'password1': 'q1w2e3r4t',
            'password2': 'q1w2e3r4t',
        }
        response = self.guest_user.post(
            reverse('users:signup'),
            data=context,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                username=context['username'],
            ).exists()
        )

    def test_cant_create_existing_user(self):
        """Тест проверяет, что нельзя создать
        существующего пользователя."""
        users_count = User.objects.count()
        context = {
            'username': 'auth',
            'password1': 'q1w2e3r4',
            'password2': 'q1w2e3r4'
        }
        response = self.guest_user.post(
            reverse('users:signup'),
            data=context,
            follow=True,
        )
        self.assertEqual(User.objects.count(), users_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
