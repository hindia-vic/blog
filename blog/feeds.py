import markdown
from django.contrib.syndication.views import Feed
from django.urls import reverse_lazy
from django.template.defaultfilters import truncatewords_html
from .models import Post


class LatestPostsFeed(Feed):
    title = 'my blog'
    link = reverse_lazy('blog:post_list')
    description = 'new post'

    def items(self):
        return Post.published.all()[:5]
    

    def item_title(self,item):
        return item.title

    
    def item_description(self, item):
        return truncatewords_html(markdown.markdown(item.body),30)
    
    def item_updated(self,item):
        return item.publish