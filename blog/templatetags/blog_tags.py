from django import template
from django.db.models import Count
from ..models import Post
import markdown
from django.utils.safestring import mark_safe

register=template.Library()

@register.simple_tag
def total_posts():
    return Post.published.count()

@register.simple_tag
def user_post_count(user):
    return Post.published.filter(author=user).count()

@register.inclusion_tag('blog/post/latest_post.html')
def show_latest_posts(count=5):
    latest_posts=Post.published.order_by('-publish')[:count]
    return {'latest_posts':latest_posts}

@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(
        total_comments=Count('comments')).order_by('-total_comments')[:count]
    
@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)