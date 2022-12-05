from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.users_views_guest = {
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
        cls.users_views_authorized = {
            reverse(
                'users:password_change_form'
            ): 'users/password_change_form.html',
            reverse(
                'users:password_change_done'
            ): 'users/password_change_done.html',
            reverse('users:logout'): 'users/logged_out.html',
        }

    def setUp(self):
        self.guest_user = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    def test_users_views_uses_correct_template(self):
        for name, template in UsersViewsTests.users_views_guest.items():
            with self.subTest(name=name):
                response = self.authorized_user.get(name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
        for name, template in UsersViewsTests.users_views_authorized.items():
            with self.subTest(name=name):
                response = self.authorized_user.get(name)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_signup_view_show_correct_context(self):
        response = self.authorized_user.get(reverse('users:signup'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
