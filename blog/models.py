from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.db import models
from taggit.managers import TaggableManager
from django.urls import reverse



class PublishedManager(models.Manager):
    def get_queryset(self):
        return(
            super().get_queryset().filter(status=Post.Status.PUBLISHED)
        )


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT='DF','Draft'
        PUBLISHED='PD','Published'
    title=models.CharField(max_length=250)
    slug=models.SlugField(max_length=250,unique_for_date='publish')
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='blog_post')
    body=models.TextField()
    featured_image = models.ImageField(
        upload_to='posts/%Y/%m/%d/',
        blank=True,
        null=True,
    )
    publish=models.DateTimeField(default=timezone.now)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    status=models.CharField(max_length=2,choices=Status,default=Status.DRAFT)
    objects=models.Manager()
    published=PublishedManager()
    tags=TaggableManager()


    class Meta:
        ordering=['-publish']
        indexes=[
            models.Index(fields=['publish']),
        ]


    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail',args=[self.publish.year,
                                                self.publish.month,
                                                self.publish.day,
                                                self.slug])

    def save(self, *args, **kwargs):
        """Custom save method with example enhancements"""
        if not self.slug:
            # Auto-generate slug if not provided
            self.slug = slugify(self.title)
        
        # Calculate read time (example: 200 words per minute)
        word_count = len(self.body.split())
        self.read_time = max(1, round(word_count / 200))  # At least 1 minute
        
        super().save(*args, **kwargs)

class Comment(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    name=models.CharField(max_length=80)
    email=models.EmailField()
    body=models.TextField()
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    active=models.BooleanField(default=True)

    class Meta:
        ordering=['created']
        indexes=[
            models.Index(fields=['created'])

        ]
    def __str__(self):
        return f"Comment by {self.name} on {self.post}"