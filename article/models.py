""" import """
from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import CASCADE
from django.utils import timezone
from markdown import Markdown

""" utils """
class Category(models.Model):
    """ 文章分类 """
    title = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering=['-created']
    def __str__(self):
        return self.title


class Tag(models.Model):
    """ 文章标签 """
    text = models.CharField(max_length=30)

    class Meta:
        ordering = ['-id']
    def __str__(self):
        return self.text


class Avatar(models.Model):
    content = models.ImageField(upload_to='avatar/%Y%m%d')


class Article(models.Model):
    category = models.ForeignKey(
        Category,
        null = True,
        blank = True,
        on_delete=models.SET_NULL,
        related_name='articles'
    )
    title = models.TextField(max_length=100)
    author = models.ForeignKey(
        User, 
        null=True,
        on_delete=models.CASCADE, 
        related_name='articles'
    )
    body = models.TextField()
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    avatar = models.ForeignKey(
        Avatar,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='article'
    ) 
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='articles'
    )

    def __str__(self):
        return self.title

    def get_md(self):
        md = Markdown(
            extensions=[
                'markdown.extensions.extra',
                'markdown.extensions.codehilite',
                'markdown.extensions.toc',
            ]
        )
        md_body = md.convert(self.body)
        return md_body, md.toc
    
    class Meta:
        ordering = ['-created']

