from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import POST_PAGE

from .forms import PostForm, CommentForm
from .models import Group, Post


def index(request):
    posts = Post.objects.all()
    count = posts.count()
    template = 'posts/index.html'
    paginator = Paginator(posts, settings.POST_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'count': count,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    count = posts.count()
    template = 'posts/group_list.html'
    text = 'Записи сообщества'
    paginator = Paginator(posts, POST_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
        'text': text,
        'count': count,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count()
    paginator = Paginator(posts, POST_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'count': count,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    author = post.author.get_full_name
    count = post.author.posts.count()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'author': author,
        'count': count,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)

@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {'form': form,
               'is_edit': False,
               }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    if request.user.id != post.author_id:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(instance=post)
    context = {'post_id': post_id,
               'form': form,
               'is_edit': True,
               }
    return render(request, 'posts/post_create.html', context)
