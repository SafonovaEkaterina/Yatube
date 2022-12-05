from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post
from .utils import show_post_count_in_page

User = get_user_model()


def index(request):
    posts = Post.objects.select_related(
        "author",
        "group"
    )
    page_obj = show_post_count_in_page(request, posts)
    template = 'posts/index.html'
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related(
        "author",
        "group"
    )
    page_obj = show_post_count_in_page(request, posts)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        "page_obj": page_obj,
    }
    return render(request, template, context)


def profile(request, username,):
    author = get_object_or_404(User, username=username)
    post_author = author.posts.select_related(
        "author",
        "group"
    )
    is_following = (
        request.user.is_authenticated
        and author != request.user
        and author.following.filter(user=request.user).exists()
    )
    template = 'posts/profile.html'
    page_obj = show_post_count_in_page(request, post_author)
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': is_following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_count = Post.objects.filter(author=post.author).count()
    template = 'posts/post_detail.html'
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'post_count': post_count,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
        return create_page_with_form(request, form)
    form = PostForm()
    return create_page_with_form(request, form)


def create_page_with_form(request, form):
    template = 'posts/create_post.html'
    context = {'form': form}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    template = 'posts/create_post.html'
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        return redirect('posts:post_detail', post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = show_post_count_in_page(request, posts)
    template = 'posts/follow.html'
    context = {
        'page_obj': page_obj,
        'follow': True,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    post_author = get_object_or_404(User, username=username)
    follow = (Follow.objects.filter(
        user=request.user,
        author=post_author
    ).exists())
    if request.user != post_author and not follow:
        Follow.objects.create(user=request.user, author=post_author)
    return redirect("posts:profile", username=username)


@login_required
def profile_unfollow(request, username):
    post_author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=post_author)
    if follower.exists():
        follower.delete()
    return redirect("posts:profile", username=username)
