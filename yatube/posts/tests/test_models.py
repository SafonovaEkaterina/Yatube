from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostsAndGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Новый тестовый пост',
        )
        cls.models_fields = {
            cls.group: cls.group.title,
            cls.post: cls.post.text[:15]
        }

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for value, expected in PostsAndGroupModelTest.models_fields.items():
            with self.subTest(value=value):
                self.assertEqual(str(value), expected)

    def test_verbose_name(self):
        """Проверяет соответствие verbos_name."""
        verbose_name_post = {
            'text': 'Текст поста',
            'author': 'Автор',
            'pub_date': 'Дата публикации',
            'group': 'Группа'
        }
        verbose_name_group = {
            'title': 'Заголовок',
            'slug': 'URL адрес группы',
            'description': 'Описание'
        }
        verbose_name = {
            self.post: verbose_name_post,
            self.group: verbose_name_group
        }
        for model, verbose in verbose_name.items():
            for value, expected in verbose.items():
                with self.subTest(value=value):
                    self.assertEqual(
                        model._meta.get_field(value).verbose_name,
                        expected
                    )

    def test_help_text(self):
        """Проверяет соответствие help_text."""
        help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for value, expected in help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)
