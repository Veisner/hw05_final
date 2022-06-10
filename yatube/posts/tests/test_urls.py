from http import HTTPStatus

from django.test import Client, TestCase

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
        self.guest_url_templates = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }
        self.auth_url_templates = {
            '/posts/1/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
        }

    def test_urls(self):
        """Страницы доступны любому пользователю"""
        for url in self.guest_url_templates:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls(self):
        """Страницы доступны авторизованному пользователю"""
        for url in self.auth_url_templates:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls(self):
        """Страницы create и post_edit перенаправят анонимного пользователя"""
        for url in self.auth_url_templates:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates = self.guest_url_templates | self.auth_url_templates
        for url, template in url_templates.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(
                    response, template,
                )

    def test_unexisting_page_url_exists_at_desired_location(self):
        """Страница /unexisting_page/ вернет кастомную ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
