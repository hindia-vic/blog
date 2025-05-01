from django.contrib import admin
from .models import Post,Comment,Profile
from django.utils.html import format_html 
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display=['title','slug','author','publish','status']
    list_filter=['status','created','publish','author']
    search_fields=['title','body']
    prepopulated_fields={'slug':('title',)}
    raw_id_fields=['author']
    date_hierarchy='publish'
    ordering=['status','publish']
    show_facets=admin.ShowFacets.ALWAYS
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display=['name','email','post','created','active']
    list_filter=['active','created','updated']
    search_fields=['name','email','body']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'truncated_bio', 'website_link', 'twitter_handle', 'avatar_preview']
    list_filter = ['user__is_active', 'user__date_joined']
    search_fields = ['user__username', 'bio', 'website']
    raw_id_fields = ['user']
    readonly_fields = ['avatar_preview']
    fieldsets = (
        (None, {
            'fields': ('user', 'avatar', 'avatar_preview')
        }),
        ('Social Media', {
            'fields': ('website', 'twitter', 'github'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('bio',),
            'classes': ('wide',)
        }),
    )

    def truncated_bio(self, obj):
        return obj.bio[:50] + '...' if obj.bio else '-'
    truncated_bio.short_description = 'Bio Excerpt'

    def website_link(self, obj):
        if obj.website:
            return format_html('<a href="{0}" target="_blank">{0}</a>', obj.website)
        return '-'
    website_link.short_description = 'Website'
    website_link.allow_tags = True

    def twitter_handle(self, obj):
        if obj.twitter:
            return format_html('<a href="https://twitter.com/{0}" target="_blank">@{0}</a>', obj.twitter)
        return '-'
    twitter_handle.short_description = 'Twitter'
    twitter_handle.allow_tags = True

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{0}" width="100" height="100" style="object-fit: cover;"/>', obj.avatar.url)
        return '-'
    avatar_preview.short_description = 'Preview'


    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        queryset.update(user__is_active=True)
    activate_users.short_description = "Activate selected users' profiles"

    def deactivate_users(self, request, queryset):
        queryset.update(user__is_active=False)
    deactivate_users.short_description = "Deactivate selected users' profiles"

# Register your models here.
