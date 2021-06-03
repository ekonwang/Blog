from rest_framework import serializers
from article.models import Article, Category, Tag, Avatar
from user_info.serializers import UserDescSerializer
from comment.serializers import CommentSerializer

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
class AvatarSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='avatar-detail')

    class Meta:
        model = Avatar
        fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='category-detail')

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created']


class TagSerializer(serializers.HyperlinkedModelSerializer):
    """ 标签序列化器 """
    def check_tag_obj_exists(self, validated_data):
        text = validated_data.get('text')
        if Tag.objects.filter(text=text).exists():
            raise serializers.ValidationError('Tag with text {} exists.'.format(text))

    def create(self, validated_data):
        self.check_tag_obj_exists(validated_data)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        self.check_tag_obj_exists(validated_data)
        return super().update(instance, validated_data)

    class Meta:
        model = Tag
        fields = '__all__'
    

class ArticleBaseSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    author = UserDescSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(
        write_only=True, 
        allow_null=True, 
        required=False
    )
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        slug_field='text'
    )
    avatar = AvatarSerializer(read_only=True)
    avatar_id = serializers.IntegerField(
        write_only=True,
        allow_null=True,
        required=False
    )
    # avatar = serializers.ImageField(allow_null=True)

    default_error_messages = {
        'incorrect_avatar_id': 'Avatar with id {value} not exists.',
        'incorrect_category_id': 'Category with id {value} not exists',
        'default': 'No more message here..'
    }

    def check_obj_exists_or_fail(self, model, value, message='default'):
        if not self.default_error_messages.get(message, None):
            message = 'default'
        if not model.objects.filter(id=value).exists() and value is not None:
            self.fail(message, value=value)

    def validate_category_id(self, value):

        self.check_obj_exists_or_fail(
            model=Category,
            value=value,
            message='incorrect_category_id'
        )
        """ if not Category.objects.filter(id=value).exists() and value is not None:
            raise serializers.ValidationError("Category with id {} not exists.".format(value))
        return value """

    def validate_avatar_id(self, value):

        self.check_obj_exists_or_fail(
            model=Avatar,
            value=value,
            message='incorrect_avatar_id'
        )
        """ if not Avatar.objects.filter(id=value).exists() and value is not None:
            raise serializers.ValidationError("AVatar with id {} not exists".format(value))
        return value """

    def to_internal_value(self, data):
        """ 覆写方法，如果标签不存在就创建它 """
        tags_data = data.get('tags')

        if isinstance(tags_data, list):
            for text in tags_data:
                if not Tag.objects.filter(text=text).exists():
                    Tag.objects.create(text=text)
        return super().to_internal_value(data)


class ArticleDetailSerializer(ArticleBaseSerializer):
    id = serializers.IntegerField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    body_html = serializers.SerializerMethodField()
    toc_html = serializers.SerializerMethodField()

    def get_body_html(self, obj):
        return obj.get_md()[0]
    
    def get_toc_html(self, obj):
        return obj.get_md()[1]
    
    class Meta:
        model = Article
        fields = '__all__'


class ArticleSerializer(ArticleBaseSerializer):
    class Meta:
        model = Article
        fields = '__all__'


class ArticleCategoryDetailSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='article-datail')

    class Meta:
        model = Article
        fields = [
            'url',
            'title',
        ]

class CategoryDetailSerializer(serializers.ModelSerializer):
    """ 分类详情 """
    articles = ArticleCategoryDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'title',
            'created',
            'articles',
        ]
