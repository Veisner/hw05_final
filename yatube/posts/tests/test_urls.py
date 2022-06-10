from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class ViewsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='author')
        cls.user_not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(ViewsURLTests.user_author)
        self.not_author_client = Client()
        self.not_author_client.force_login(ViewsURLTests.user_not_author)
        self.auth_url_templates = {
            '/posts/1/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }
        self.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}
                    ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                    'username': ViewsURLTests.user_author}
                    ): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 1}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 1}
                    ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_urls(self):
        """Страницы доступны любому пользователю"""
        for url in self.templates_page_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls(self):
        """Страницы доступны авторизованному пользователю"""
        for url in self.templates_page_names:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls(self):
        """Страницы create и post_edit перенаправят анонимного пользователя"""
        for url in self.auth_url_templates:
            with self.subTest(url=url):
                response = self.guest_client.post(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ вернет кастомную ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
