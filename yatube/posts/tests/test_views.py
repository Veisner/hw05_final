from http import HTTPStatus

from django.conf import settings
from django.core.paginator import Paginator
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
        cls.group_2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.number_of_posts = 55
        Post.objects.bulk_create([Post(
                                  text=f'Тестовый пост {post_num}, группа 1',
                                  author=cls.user_author,
                                  group=cls.group
                                  ) for post_num in range(cls.number_of_posts)
                                  ])
        Post.objects.bulk_create([Post(text=f'Тестовый пост {i}, группа 2',
                                 author=cls.user_author,
                                 group=cls.group_2) for i in range(2)])

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(ViewsURLTests.user_author)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
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
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:group_list',
                                          kwargs={'slug': 'test_slug'}))
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:profile',
                                          kwargs={'username': self.user_author}
                                                  ))
        self.assertIn('page_obj', response.context)
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user_author)

    def test_post_detail_show_correct_contex(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual((response.context.get('post').pk), self.post.id)
        self.assertEqual((response.context.get('post').text), self.post.text)

    def test_post_edit_show_correct_contex(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_edit',
                                          kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context.get('post_id'), self.post.id)
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)

    def test_post_create_show_correct_contex(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)

    def test_index_paginator(self):
        """Cтраницы шаблона index содержат правильное кол-во постов."""
        paginator = Paginator(Post.objects.all(), settings.POST_PAGE)
        count = paginator.count
        num_pages = paginator.num_pages
        posts_last_page = count - ((num_pages - 1) * settings.POST_PAGE)
        if count < (settings.POST_PAGE + 1):
            response = self.author_client.get(reverse('posts:index'))
            self.assertEqual(len(response.context['page_obj']), count)
        response1 = self.author_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response1.context['page_obj']), settings.POST_PAGE)
        response2 = self.author_client.get(
            reverse('posts:index') + f'?page={num_pages}')
        self.assertEqual(len(response2.context['page_obj']), posts_last_page)

    def test_group_list_paginator(self):
        """Cтраницы шаблона group_list содержат правильное кол-во постов."""
        paginator = Paginator(Post.objects.filter(
            group=self.group), settings.POST_PAGE)
        count = paginator.count
        num_pages = paginator.num_pages
        posts_last_page = count - ((num_pages - 1) * settings.POST_PAGE)
        if count < (settings.POST_PAGE + 1):
            response = self.author_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test_slug'}))
            self.assertEqual(len(response.context['page_obj']), count)
        response1 = self.author_client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_slug'}))
        self.assertEqual(
            len(response1.context['page_obj']), settings.POST_PAGE)
        response2 = self.author_client.get(reverse('posts:group_list',
                                                   kwargs={'slug': 'test_slug'}
                                                   ) + f'?page={num_pages}')
        self.assertEqual(len(response2.context['page_obj']), posts_last_page)

    def test_profile_paginator(self):
        """Cтраницы шаблона profile содержат правильное кол-во постов."""
        paginator = Paginator(Post.objects.filter(
            author=self.user_author), settings.POST_PAGE)
        count = paginator.count
        num_pages = paginator.num_pages
        posts_last_page = count - ((num_pages - 1) * settings.POST_PAGE)
        if count < (settings.POST_PAGE + 1):
            response = self.author_client.get(reverse('posts:profile',
                                              kwargs={
                                                  'username': self.user_author}
            ))
            self.assertEqual(len(response.context['page_obj']), count)
        response1 = self.author_client.get(
            reverse('posts:profile', kwargs={'username': self.user_author}))
        self.assertEqual(
            len(response1.context['page_obj']), settings.POST_PAGE)
        response = self.author_client.get(reverse('posts:profile',
                                          kwargs={'username': self.user_author}
                                                  ) + f'?page={num_pages}')
        self.assertEqual(len(response.context['page_obj']), posts_last_page)

    def test_create_post_show(self):
        """При создании поста он появляет на главной странице,
           странице группы и в профиле автора, но не появляется
           в другой группе"""
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'author': self.post.author,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': self.user_author}),
                             HTTPStatus.FOUND
                             )

        response1 = self.author_client.get(reverse('posts:index'))
        self.assertEqual(response1.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response1.context['page_obj'][0].group.pk, self.group.pk)
        self.assertEqual(
            response1.context['page_obj'][0].author, self.post.author)

        response2 = self.author_client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_slug'}))
        self.assertEqual(response2.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response2.context['page_obj'][0].group.pk, self.group.pk)
        self.assertEqual(
            response2.context['page_obj'][0].author, self.post.author)

        response3 = self.author_client.get(reverse('posts:profile',
                                           kwargs={
                                               'username': self.user_author}))
        self.assertEqual(response3.context['page_obj'][0].text, self.post.text)
        self.assertEqual(
            response3.context['page_obj'][0].group.pk, self.group.pk)
        self.assertEqual(
            response3.context['page_obj'][0].author, self.post.author)
        response4 = self.author_client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_slug_2'}))
        self.assertNotIn(response4.context['page_obj'][0].text, self.post.text)
