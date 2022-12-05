from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.about_url = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def setUp(self):
        super().setUp()
        self.guest_user = Client()

    def test_exists_about_url(self):
        """Тест на доступность адресов проекта about."""
        for address in AboutTests.about_url:
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """Тест на использование корректных шаблонов
        по адресам приложения about."""
        for address, template in AboutTests.about_url.items():
            with self.subTest(address=address):
                response = self.guest_user.get(address)
                self.assertTemplateUsed(response, template)
