from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.db import models
from taggit.managers import TaggableManager
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    view_count = models.PositiveIntegerField(default=0, editable=False)
    featured_image = models.ImageField(
        upload_to='posts/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Featured image for the post (1200x630px recommended)",
    )
    featured_image_caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional caption for the featured image"
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
    author = models.ForeignKey(settings.AUTH_USER_MODEL, 
                             on_delete=models.CASCADE,
                             null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
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
        try:
            author_name = self.author.username if self.author else self.name
            return f"Comment by {author_name}"
        except AttributeError:
            return "Comment (author unknown)"
    '''def __str__(self):
        return f"Comment by {self.author.username if self.author else self.name}"'''
    
    @property
    def is_reply(self):
        return self.parent is not None

    def get_replies(self):
        return self.replies.filter(active=True).select_related('author')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=50, blank=True)
    github = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
      if created:
        Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()    

class ReadingList(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_list'
    )
    posts = models.ManyToManyField(
        'Post',
        related_name='in_reading_lists',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Reading List"

    def add_post(self, post):
        self.posts.add(post)
        self.save()

    def remove_post(self, post):
        self.posts.remove(post)
        self.save()

    @property
    def post_count(self):
        return self.posts.count()   

class Reaction(models.Model):
    REACTION_CHOICES = [
        ('👍', 'Like'),
        ('❤️', 'Love'),
        ('😲', 'Wow'),
        ('😄', 'Happy'),
        ('😢', 'Sad'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction = models.CharField(max_length=2, choices=REACTION_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user', 'reaction')
        ordering = ['-created']
