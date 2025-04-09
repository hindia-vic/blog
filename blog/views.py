from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank
from django.contrib import messages
from django.contrib.auth import login
from  django.views.generic import ListView
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count
from .forms import EmailPostForm,CommentForm,SearchForm,CustomerCreation,PostForm
from . models import Post

def post_list(request,tag_slug=None):
    post_list=Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    paginator=Paginator(post_list,3)
    page_number=request.GET.get('page',1)
    try:
        posts=paginator.page(page_number)
    except PageNotAnInteger:
        posts=paginator.page(1)
    except EmptyPage:
        posts=paginator.page(paginator.num_pages)
    return render(request,'blog/post/list.html',{'posts':posts,'tag':tag})

def post_detail(request,year,month,day,post):
    post=get_object_or_404(Post,
                           slug=post,
                           publish__year=year,
                           publish__month=month,
                           publish__day=day,
                           status=Post.Status.PUBLISHED)

    comments=post.comments.filter(active=True)
    form=CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(
    tags__in=post_tags_ids
    ).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
    same_tags=Count('tags')
    ).order_by('-same_tags', '-publish')[:4]
    return render(request,'blog/post/detail.html',{'post':post,'comments':comments,'form':form,'similar_posts': similar_posts})

def  post_share(request,post_id):
    post=get_object_or_404(Post,id=post_id,status=Post.Status.PUBLISHED)
    sent=False
    if request.method =='POST':
        form=EmailPostForm(request.POST)
        if form.is_valid():
            cd=form.cleaned_data
            post_url=request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject=(
                f"{cd['name']} ({cd['email']})"
                f"recommends you to read {post.title}"
            )
            message=(
                f'read {post.title} at {post_url}\n\n'
                f"{cd['name']}\'s comments:{cd['comments']}"
            )
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[cd['to']]
               )
            sent=True
    
    else:
        form=EmailPostForm()
    return render(request,'blog/post/share.html',{'form':form,'post':post,'sent':sent})


@require_POST
def post_comment(request,post_id):
    post=get_object_or_404(Post,id=post_id,status=Post.Status.PUBLISHED)
    comment=None
    form=CommentForm(data=request.POST)
    if form.is_valid():
        comment=form.save(commit=False)
        comment.post=post
        comment.save()

    return render(request,'blog/post/comment.html',{'post':post,'form':form,'comment':comment})

def post_search(request):
    form=SearchForm()
    query=None
    results=[]

    if 'query' in request.GET:
        form=SearchForm(request.GET)
        if form.is_valid():
            query=form.cleaned_data['query']
            searchvector=SearchVector('title',weight='A')+ SearchVector('body',weight='B')
            search_query=SearchQuery(query)
            results=(
                Post.published.annotate(
                    search=searchvector,
                    rank=SearchRank(searchvector,search_query)
                ).filter(rank__gte=0.2).order_by('-rank')
            )
    return render(request,'blog/post/search.html',{'form':form,'query':query,'results':results})

def post_create(request):
    form=PostForm()
    if request.method=='POST':
        form=PostForm(request.POST,request.FILES)
        if form.is_valid():
            post=form.save(commit=False)
            post.author=request.user
            post.save()
            return redirect(post.get_absolute_url())
    return render(request,'blog/post/create.html',{'form':form})

def confirm_delete(request, post_id):
    """Show confirmation page before deletion"""
    post = get_object_or_404(Post, id=post_id)
    
    # Check permissions
    if not (request.user == post.author or request.user.is_staff):
        messages.error(request, "You don't have permission to delete this post.")
        return redirect('blog:post_list')


@require_POST
@login_required
def delete_post(request,post_id):
    post=get_object_or_404(Post,id=post_id)
    post.delete()
    if not (request.user == post.author or request.user.is_staff):
        messages.error(request, "You don't have permission to delete this post.", extra_tags='alert-danger')
        return redirect('blog:post_list')
    try:
            post_title = post.title
            post.delete()
            messages.success(request, f'Post "{post_title}" was successfully deleted.', extra_tags='alert-success')
            return redirect('blog:post_list')
    
    except Exception as e:
           messages.error(request,f'Error deleting post: {str(e)}',extra_tags='alert-danger')
           return redirect('blog:post_detail', post_id=post.id)

def register(request):
    if request.method=='POST':
        form=CustomerCreation(request.POST)
        if form.is_valid():
            user=form.save()
            login(request,user)
            return redirect('post_list')
    else:
        form=CustomerCreation()
    return render(request,'registration/register.html',{'form':form})