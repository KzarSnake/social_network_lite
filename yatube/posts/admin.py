from django.conf import settings
from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = settings.EMPTY_VALUE


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title',)
    list_filter = ('title',)
    empty_value_display = settings.EMPTY_VALUE


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'post', 'text')
    search_fields = ('author',)
    list_filter = ('created',)
    empty_value_display = settings.EMPTY_VALUE


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
