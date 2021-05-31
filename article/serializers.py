from re import search
from rest_framework import serializers
from article.models import Article
from user_info.serializers import UserDescSerializer

""" class ArticleListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='article:detail')
    author = UserDescSerializer(read_only=True)
    class Meta:
        model = Article
        fields = [
            'url',
            # 'id',
            'title',
            'author',
            'created',
        ]
        # read_only_fields = ['author']

class ArticleDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__' """

class ArticleSerializer(serializers.HyperlinkedModelSerializer):
    author = UserDescSerializer(read_only=True)

    class Meta:
        model = Article
        fields = '__all__'