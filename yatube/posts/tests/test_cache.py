from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, User


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')

    def setUp(self):
        self.guest_client = Client()

    def test_index_cache(self):
        post = Post.objects.create(
            text='Тестовый пост',
            author=PostCacheTest.author,
        )
        response = self.guest_client.get(reverse('posts:index'))
        Post.objects.filter(pk=post.pk).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response.content, response2.content)
