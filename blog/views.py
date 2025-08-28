from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import login
from  django.views.generic import ListView
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail,mail_admins
from taggit.models import Tag
from django.db.models import Count,F
from .forms import EmailPostForm,CommentForm,SearchForm,CustomerCreation,PostForm,ProfileForm,ContactForm
from . models import Post,ReadingList,Comment,Reaction

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

#@cache_page(60 * 15) 
@never_cache
def post_detail(request, year, month, day, post):
    # Get the post with all necessary relationships
    post = get_object_or_404(
        Post.objects.select_related('author')
                   .prefetch_related('tags'),
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day,
        status=Post.Status.PUBLISHED
    )
    # Increment view count (excluding author views and duplicate refreshes)
    if not request.user.is_authenticated or request.user != post.author:
        # Using F() to avoid race conditions
        Post.objects.filter(pk=post.pk).update(view_count=F('view_count') + 1)
        # Refresh the post object to get updated view count
        post.refresh_from_db()

    # Get comments with author information and order by newest first
    comments = (post.comments.filter(active=True)
                           .select_related('author')
                           .order_by('-created'))

    # Get similar posts with optimized query
    similar_posts = (Post.published
                       .filter(tags__in=post.tags.values_list('id', flat=True))
                       .exclude(id=post.id)
                       .annotate(same_tags=Count('tags'))
                       .order_by('-same_tags', '-publish')[:4]
                       .select_related('author'))
    reaction_choices = Reaction.REACTION_CHOICES
    reaction_counts = (
        Reaction.objects.filter(post=post)
        .values('reaction')
        .annotate(count=Count('reaction'))
        .order_by('-count')
    )
    reaction_counts = {r['reaction']: r['count'] for r in reaction_counts}
    
    # Get user's reactions if authenticated
    user_reactions = []
    if request.user.is_authenticated:
        user_reactions = list(
            Reaction.objects.filter(post=post, user=request.user)
            .values_list('reaction', flat=True)
        )

    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm(),
        'similar_posts': similar_posts,
        'now': timezone.now(),
        'reaction_choices': reaction_choices,
        'reaction_counts': reaction_counts,
        'user_reactions': user_reactions,
    }
    
    return render(request, 'blog/post/detail.html', context)

@login_required
def reply_comment(request,comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    post = parent_comment.post
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.post = post
            reply.parent = parent_comment
            reply.save()
            messages.success(request, "Your reply has been posted!")
            return redirect(post.get_absolute_url() + f'#comment-{reply.id}')
    
    # If GET request or invalid form, redirect to post
    return redirect(post.get_absolute_url())

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
        if request.user.is_authenticated:
            comment.author = request.user
        comment.save()
        return redirect(post.get_absolute_url())
    return render(request,'blog/post/comment.html',{'post':post,'form':form,'comment':comment})


@login_required
def comment_delete(request, pk):
    """
    Deletes a comment after verifying ownership
    """
    comment = get_object_or_404(Comment, pk=pk)
    
    # Verify the request user is the comment author
    if request.user != comment.author:
        messages.error(request, "You can only delete your own comments!")
        return redirect(comment.post.get_absolute_url())
    
    if request.method == 'POST':
        post_url = comment.post.get_absolute_url()
        comment.delete()
        messages.success(request, "Comment deleted successfully!")
        return redirect(post_url)
    
    # If GET request, show confirmation template
    return render(request, 'blog/post/comment_confirm_delete.html', {
        'comment': comment
    })


@login_required
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk, author=request.user)
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.updated = timezone.now() 
            comment.save()
            return redirect(comment.post.get_absolute_url())
    else:
        form = CommentForm(instance=comment)
    return render(request, 'blog/post/comment_edit.html', {'form': form})
@require_POST
@login_required
def add_reaction(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    reaction_type = request.POST.get('reaction')
    
    # Validate reaction type
    valid_reactions = dict(Reaction.REACTION_CHOICES).keys()
    if reaction_type not in valid_reactions:
        messages.error(request, "Invalid reaction type")
        return redirect(post.get_absolute_url())
    
    # Toggle reaction
    reaction, created = Reaction.objects.get_or_create(
        post=post,
        user=request.user,
        reaction=reaction_type
    )
    
    if not created:
        reaction.delete()
        messages.success(request, f"Removed {reaction_type} reaction")
    else:
        messages.success(request, f"Added {reaction_type} reaction")
    
    return redirect(post.get_absolute_url())
    
    

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

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            # Set default status if not provided
            if not post.status:
                post.status = Post.Status.DRAFT
            
            post.save()
            
            # Save many-to-many relationships (like tags) after saving the post
            form.save_m2m()
            
            if post.status == Post.Status.DRAFT:
                messages.success(request, 'Draft saved successfully!')
                return redirect('blog:draft_detail', pk=post.pk)  # Redirect to drafts list
            else:
                messages.success(request, 'Post published successfully!')
                return redirect(post.get_absolute_url())
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm(initial={
            'status': Post.Status.DRAFT,  # Default to draft
            'author': request.user  # Pre-set author (though hidden in form)
        })
    
    return render(request, 'blog/post/create.html', {
        'form': form,
        'title': 'Create New Post'
    })


def confirm_delete(request, post_id):
    """Show confirmation page before deletion"""
    post = get_object_or_404(Post, id=post_id)
    # Check permissions
    if not (request.user == post.author or request.user.is_staff):
        messages.error(request, "You don't have permission to delete this post.")
        return redirect('blog:post_list')
    
    return render(request, 'blog/post/delete.html', {'post': post})


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
            return redirect('blog:post_list')
    else:
        form=CustomerCreation()
    return render(request,'registration/register.html',{'form':form})

def update_post(request,post_id):
    post = get_object_or_404(Post,id=post_id,author=request.user)
    if request.method=='POST':
        form=PostForm(request.POST,request.FILES,instance=post)
        if form.is_valid():
            post=form.save(commit=False)
            post.save()
            messages.success(request,'Post updated successfully')
            return redirect(post.get_absolute_url())
    else:
        form=PostForm(instance=post)
        return render(request,'blog/post/update.html',{'form':form,'post':post})

@login_required
def user_profile(request):
    user_posts = Post.published.filter(author=request.user)
    drafts = Post.objects.filter(author=request.user, status=Post.Status.DRAFT)
    user_comments = Comment.objects.filter(author=request.user).select_related('post')
    comment_paginator = Paginator(user_comments, 10)
    comments_page = comment_paginator.get_page(request.GET.get('comments_page'))
    return render(request, 'blog/post/profile.html', {
        'user': request.user,
        'user_posts': user_posts,
        'drafts': drafts ,
        'comments':comments_page
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('blog:user_profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    return render(request, 'blog/post/profile_edit.html', {'form': form})

@login_required
def post_draft_list(request):
    drafts = Post.objects.filter(
        author=request.user, 
        status=Post.Status.DRAFT
    ).order_by('-created')
    return render(request, 'blog/post/draft_list.html', {'drafts': drafts})


@login_required
def draft_detail(request, pk):
    """
    Displays a draft post for preview (only accessible to the author)
    """
    draft = get_object_or_404(
        Post.objects.filter(
            status=Post.Status.DRAFT,
            author=request.user
        ),
        pk=pk
    )
    
    # Add publish button logic if form submitted
    if request.method == 'POST' and 'publish' in request.POST:
        draft.status = Post.Status.PUBLISHED
        draft.save()
        return redirect(draft.get_absolute_url())
    
    return render(request, 'blog/post/draft_detail.html', {
        'draft': draft
    })

    

def post_archive(request):
    archive = Post.published.dates('publish', 'month', order='DESC')
    return render(request, 'blog/post/archive.html', {'archive': archive})

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            mail_admins(
                subject=f"Contact Form: {form.cleaned_data['subject']}",
                message=form.cleaned_data['message'],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent!')
            return redirect('blog:post_list')
    else:
        form = ContactForm()
    return render(request, 'blog/post/contact.html', {'form': form})


@login_required
@require_POST
def bookmark_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    request.user.profile.bookmarks.add(post)
    return JsonResponse({'status': 'ok'})

@login_required
def reading_list(request):
    reading_list = get_object_or_404(ReadingList, user=request.user)
    posts = reading_list.posts.filter(status=Post.Status.PUBLISHED).select_related('author').prefetch_related('tags')
    
    # Add pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    return render(request, 'blog/post/reading_list.html', {
        'reading_list': reading_list,
        'posts': posts,
        'section': 'reading_list'
    })

@login_required
@require_POST
def add_to_reading_list(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    reading_list, created = ReadingList.objects.get_or_create(user=request.user)
    
    if reading_list.posts.filter(id=post.id).exists():
        messages.warning(request, 'This post is already in your reading list')
    else:
        reading_list.posts.add(post)
        messages.success(request, f'"{post.title}" added to your reading list')
    
    if request.headers.get('HTTP_REFERER'):
        return redirect(request.headers.get('HTTP_REFERER'))
    return redirect(post.get_absolute_url())


@login_required
@require_POST
def remove_from_reading_list(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    reading_list = get_object_or_404(ReadingList, user=request.user)
    
    if reading_list.posts.filter(id=post.id).exists():
        reading_list.posts.remove(post)
        messages.success(request, f'"{post.title}" removed from your reading list')
    else:
        messages.warning(request, 'This post was not in your reading list')
    
    if request.headers.get('HTTP_REFERER'):
        return redirect(request.headers.get('HTTP_REFERER'))
    return redirect('blog:reading_list')