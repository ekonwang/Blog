""" import """
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

""" utils """
class Article(models.Model):
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
    avatar = models.ImageField()

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created']