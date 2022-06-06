import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsFormsTests(TestCase):
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(ViewsFormsTests.user_author)
        self.not_author_client = Client()
        self.not_author_client.force_login(ViewsFormsTests.user_not_author)

    def test_create_post(self):
        """при отправке валидной формы с картинкой со страницы создания
        поста создаётся новая запись в базе данных"""
        posts_count = Post.objects.count()
        small_gif_2 = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_2 = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif_2,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Самый новый пост',
            'group': self.group.pk,
            'image': uploaded_2,
            'author': self.post.author,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile', kwargs={
                             'username': self.user_author}), HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        #картинка появляется на страницах
        response1 = self.author_client.get(reverse('posts:index'))
        self.assertEqual(
            response1.context['page_obj'][0].image, f'posts/{uploaded_2.name}')
        response2 = self.author_client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test_slug'}))
        self.assertEqual(
            response2.context.get('page_obj')[0].image, f'posts/{uploaded_2.name}')
        response3 = self.author_client.get(reverse('posts:profile',
                                           kwargs={
                                               'username': self.user_author}))
        self.assertEqual(
            response3.context['page_obj'][0].image, f'posts/{uploaded_2.name}')
        response4 = self.author_client.get(reverse('posts:post_detail',
                                           kwargs={'post_id': 2}))
        self.assertEqual(
            response4.context['post'].image, f'posts/{uploaded_2.name}')

    def test_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста
           происходит изменение поста с post_id в базе данных."""
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
                             'posts:post_detail',
                             kwargs={'post_id': self.post.id}
                             ), HTTPStatus.FOUND)
        response1 = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual((response1.context.get('post').pk), self.post.id)
        self.assertEqual((response1.context.get('post').text
                          ), 'Тестовый текст')

    def test_post_edit_not_author(self):
        """при отправке формы со страницы редактирования поста не автором
           пост не меняет значение полей."""
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        response = self.not_author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertFalse(response.context.get('is_edit'))
        response1 = self.not_author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual((response1.context.get('post').pk), self.post.id)
        self.assertEqual((response1.context.get('post').text), self.post.text)

    def test_post_edit_guest(self):
        """при отправке формы со страницы редактирования поста анонимом
           пост не меняет значение полей."""
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertFalse(response.context.get('is_edit'))
        response1 = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual((response1.context.get('post').pk), self.post.id)
        self.assertEqual((response1.context.get('post').text), self.post.text)

    def test_create_post_guest(self):
        """при создании поста анонимом не создаётся новая запись
           в базе данных"""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFalse(response.context.get('is_edit'))
        self.assertEqual(Post.objects.count(), posts_count)


