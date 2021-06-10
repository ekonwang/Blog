# Yifou-Readme.txt

# 项目综述背景

一名良好的全栈工程师应当在掌握后端算法技能的同时，掌握一些前端知识，搭建公共博客涉及前端框架的使用、后端代码的编写、以及用户管理、文章管理等诸多细节，同时也使用到了数据库知识，以实现数据的持久化。

本项目实现了一个网络博客，并上线公网。前端使用vue.js框架，以实现高效渲染，后端使用django + rest_framework框架，实现高性能的请求处理。项目名称为Yifou blog，公网的访问IP为 1.15.33.167。主要功能包括：文章管理(文章发布、文章编辑)、标签管理(标签创造)、分类管理、用户信息管理(用户信息编辑、注册、登录、登出、注销)、文章标题图（图片上传、标题图编辑）、用户令牌（这个feature出于安全性引入）、评论功能（发表一般评论、多级评论）、公网访问（使用nginx负载均衡器部署）

# 开发环境

`开发环境：Windows 10 (python 3.9.1,	Node.js v14.17.0,`

`Django 3.1.3, 	npm 6.14.13)`

`部署环境：腾讯云一核2G云服务器`

`Linux/ubuntu20.04 (python3 3.8.10,	 Node.js v14.17.0,	`

`Django 3.1.3, 	npm 7.16.0)`

# 数据库设计

项目ER图如图所示，这些表作为model的对象在Django框架中定义，并通过Django的数据迁移操作实际落地，并储存在db.sqlite3，主要定义的数据表有Article, Tag, Category, Avatar, comment, User 以及Django 项目初始化自动生成的数据表：

![ER](image/ER.png)

本项目没有手写SQL语句，这得益于Django框架提供的高度抽象的ORM模型，其大致原理如图所示 :

![ORM](image/ORM.png)

ORM模型：在Django中，模型（model）被映射成数据表，处理与数据相关的事务。有了ORM这个工具，开发时就只需要面向对象编程，而不用拘泥于数据库的底层操作，减小了开发难度。

每次对model进行编辑之后，都应该进行数据迁移操作，这是Django框架将model的编辑转换成对数据库修改的机制。

# 系统设计

本项目的最终系统设计如图所示：

![arch](image/arch.png)

用户通过浏览器访问网站，由proxy转发代理请求，其中静态资源的请求被直接转发到collected_static文件夹下的index.html中；对动态资源的请求，被转发到由wsgi server代理的Django后端，Django后端通过接口接收或返回序列化的数据；并且媒体资源的请求，比如图片，会被转发到项目根目录下的media文件夹，后台将直接返回媒体文件。

# 后端开发

## article APP

### Category模块

为了搭建article模块，先声明Category类：

```python
'''article/models.py'''

from django.db import models

class Category(models.Model):
    """ 文章分类 """
    title = models.CharField(max_length=100)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering=['-created']
    def __str__(self):
        return self.title
```

在Django中，每个声明的model对应着一个数据表，model的名称正好对应数据表的表名，而其中声明的各个字段，则对应着数据表的各个Column。

首先，Python框架提供了一个基类Model，在此声明的Category也是继承它而来。其二：子类Meta中的ordering字段，表明数据的排列顺序，在这里我们选择按创建时间逆序返回Category数据。其三：该类定义的`__str__`方法定义了在管理站点各个Category对象的显示内容，这里就选择显示Category的直接内容title。

接着就需要定义Category的序列化器serializer：

```python
'''article/serializers.py'''

from rest_framework import serializers
from article.models import Article

class CategorySerializer(serializers.ModelSerializer):
    """分类的序列化器"""
    url = serializers.HyperlinkedIdentityField(view_name='category-detail')

    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created']
       
    
class CategoryDetailSerializer(serializers.ModelSerializer):
    """分类详情"""
    articles = ArticleCategoryDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            'id',
            'title',
            'created',
            'articles',
        ]
```

为什么要定义serializer? 因为这个项目中，前后端采用的是端口间json文本通信（至少在测试阶段是这样）。json 文件正是为此目的而创造的，它提供了一种通用的通信格式，采用类似key-value的形式储存数据。数据在后端传入前端需要转换成json文件，这个过程就称作**序列化**，而它的逆过程，就称为**逆序列化**。

这里的代码首先，声明两种serializer是为了满足不同场景的需要，一些场景下需要显示Category对象及其关联的文章（比如在显示文章列表时），为此就定义了 CategoryDetailSerializer ，而另一些场景中只需要所有category列表，其关联信息可以不显示（比如在编辑文章时，在旁边提供的供选择的category），为此就定义了 CategorySerializer。其二，Meta子类中fields中表明将会序列化哪些字段，model字段则表明序列化的类名。其三，为了保障安全性，可以在序列化器中声明一个read_only_fields，并加入仅可读的字段列表，表明serializer将不会接受对该字段的修改。

最后定义视图类：

```python
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'list':
            return CategorySerializer
        else:
            return CategoryDetailSerializer 
```

这里的代码有几点需要注意：首先，`get_serializer_class()`方法提供了根据不同需求选择不同`serializer`的手段；其二，`permission_classes` 提供了权限声明，即只有管理员和自己才能编辑Category对象；其三，`pagination_class = None` 表明序列化器返回的数据不会分页，这点和 `article` 不一样；`queryset`表明数据取用的对象，该类中对象是Category类的对象全体。

### Tag 模块 & Avatar 模块

model定义：

```python
class Tag(models.Model):
    """ 文章标签 """
    text = models.CharField(max_length=30)

    class Meta:
        ordering = ['-id']
    def __str__(self):
        return self.text
    
class Avatar(models.Model):
    content = models.ImageField(upload_to='avatar/%Y%m%d')
```

这里需要注意的是：`Avatar` 类中的 `content` 字段声明了图片上传路径为 `'avatar/%Y%m%d'`。

序列化器定义：

```python
class TagSerializer(serializers.HyperlinkedModelSerializer):
    """标签序列化器"""

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
        
class AvatarSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='avatar-detail')

    class Meta:
        model = Avatar
        fields = '__all__'
```

视图集定义：

```python
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = None
    
class AvatarViewSet(viewsets.ModelViewSet):
    queryset = Avatar.objects.all()
    serializer_class = AvatarSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    pagination_class = None
```

### Article模块

model定义：

```python
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
        ordering = ['created']
```

serializer定义:

```python
class ArticleBaseSerializer(serializers.HyperlinkedModelSerializer):
    """
    文章序列化器父类
    """
    id = serializers.IntegerField(read_only=True)
    author = UserDescSerializer(read_only=True)
    # category 的嵌套序列化字段
    category = CategorySerializer(read_only=True)
    # category 的 id 字段，用于创建/更新 category 外键
    category_id = serializers.IntegerField(write_only=True, allow_null=True, required=False)
    # tag 字段
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

    # 自定义错误信息
    default_error_messages = {
        'incorrect_avatar_id': 'Avatar with id {value} not exists.',
        'incorrect_category_id': 'Category with id {value} not exists.',
        'default': 'No more message here..'
    }

    def check_obj_exists_or_fail(self, model, value, message='default'):
        if not self.default_error_messages.get(message, None):
            message = 'default'

        if not model.objects.filter(id=value).exists() and value is not None:
            self.fail(message, value=value)

    def validate_avatar_id(self, value):
        self.check_obj_exists_or_fail(
            model=Avatar,
            value=value,
            message='incorrect_avatar_id'
        )

        return value

    # category_id 字段的验证器
    def validate_category_id(self, value):
        # 数据存在且传入值不等于None
        self.check_obj_exists_or_fail(
            model=Category,
            value=value,
            message='incorrect_category_id'
        )

        return value

    # 覆写方法，如果输入的标签不存在则创建它
    def to_internal_value(self, data):
        tags_data = data.get('tags')

        if isinstance(tags_data, list):
            for text in tags_data:
                if not Tag.objects.filter(text=text).exists():
                    Tag.objects.create(text=text)

        return super().to_internal_value(data)

class ArticleSerializer(ArticleBaseSerializer):
    class Meta:
        model = Article
        fields = '__all__'
        extra_kwargs = {'body': {'write_only': True}}
        
class ArticleDetailSerializer(ArticleBaseSerializer):
    id = serializers.IntegerField(read_only=True)
    body_html = serializers.SerializerMethodField()
    toc_html = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)

    def get_body_html(self, obj):
        return obj.get_md()[0]

    def get_toc_html(self, obj):
        return obj.get_md()[1]

    class Meta:
        model = Article
        fields = '__all__'
```

为什么对于`Article`这个模块定义三个`Serializer`？实际上定义了两个，原因和前面一样，是为了满足不同的需求而分别定义的。`ArticleBaseSerializer`是 `ArticleSerializer` 和 `ArticleDetailSerializer`类的基类，俗话说:"重复的代码是万恶之源"，虽然两个`serializer`是为了处理不同的需求，但也有不少重复的地方，引入一个`ArticleBaseSerializer`基类，让两个`serializer`从它继承方法，提高代码重用性、减轻维护难度，这样的处理是必要的。

视图集定义：

```python
class ArticleViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']
    # filterset_fields = ['author__username', 'title']
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_query(self):
        queryset = self.queryset
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = queryset.filter(author__username=username)
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleSerializer
        else:
            return ArticleDetailSerializer
```

之后用大致相同的思路定义user_info和comment 模块，分别实现用户管理功能以及用户评论。

## 路由注册及相关配置

路由注册这一步相当于给每一个API提供一个url，这一步有利于前后端的分离。

这一步使用了`rest_framework` 中的`router` 模块，一定程度上简化了路由配置:


```python
'''drf_vue_blog/urls.py'''

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'article', views.ArticleViewSet)
router.register(r'category', views.CategoryViewSet)
router.register(r'tag', views.TagViewSet)
router.register(r'avatar', views.AvatarViewSet)
router.register(r'comment', CommentViewSet)
router.register(r'user', UserViewSet)

urlpatterns = [
    ...
    path('api/', include(router.urls)),
    ...
]
```

相应的，也需要在Django主文件夹下的settings.py 中注册APP，以及进行其他必要的配置:

```python
'''drf_vue_blog/settings.py'''
...

INSTALLED_APPS = [
    ...
    'rest_framework',
    'article',
    'user_info',
    'comment',
]

...

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

# 前端开发

## 前端配置

安装必要的模块如Nodejs, vue-cli 以及 axios 之后，在根目录下输入`vue create frontend ` 开启前端项目。

Axios提供了前后端通信的手段，它使vue前端可以通过后端提供的已有接口获取数据，或者向后端发送数据。首先配置vue前端的conf文件，它在frontend目录下，名为vue.config.js。

```python
/* drf_vue_blog/frontend/vue.config.js */

module.exports = {
    devServer: {
        proxy: {
            // detail: https://cli.vuejs.org/config/#devserver-proxy
            '/api': {
                target: `http://127.0.0.1:8000/api`,
                changeOrigin: true,
                pathRewrite: {
                    '^/api': ''
                }
            }
        }
    }
};
```

由于测试阶段中Django运行在localhost的8000端口下，vue的配置也顺理成章地向该端口请求数据。

## 编写前端源文件

本次项目使用了vue作为前端框架，在vue中着重编写frontend/src下的components 以及 views 两个模块。components是项目中可以复用的组件，views中定义了最终项目中呈现给用户的界面，比如ArticleCreate.vue(文章编辑界面)、ArticleDetail.vue（文章查看界面）、ArticleEdit.vue（文章修改界面）、Home.vue（主页，即文章列表）、Login.vue（用户登录界面以及注册界面）、UserCenter.vue（用户信息修改界面）。

Vue编写起来更为“阳间”（相比较于bootstrap下编写html文件），代码一般分为三个部分：template、scripts、style，template 定义了界面的最终框架，style定义了渲染风格比如字体颜色等，scripts定义了数据交互的方法。前端代码比较繁琐，具体代码可以查看frontend/src下的源文件，这里就只展示各个页面的最终效果：

**登录界面**：

![login](image/login.png)

由于登录界面与注册界面高度同构，因此将二者合并成同一页面了。

用户登录后，原来在左上角显示登录的地方会变成一个下拉框，用户可以执行登出、文章发表以及进入用户中心的操作：

![bar](image/bar.png)

**文章创作：**

![create](image/create.png)

最上方提供了上传图片的接口，此接口只接收gif, jpg, png 以及 jpeg 文件，当然用户也允许上传其他格式的文件，但这些文件不会被传输到Django后端，新文章也是没有标题图的。

分类与标签都有外键约束，不同点在于分类只有管理员能创建，而且只能选一个分类；而标签是动态创建的，用户可以在输入栏中输入任意多个用逗号(全角/半角都兼容) 分隔开的标签。

**文章详情：**

![detail](image/detail.png)

文章正文支持markdown形式，也支持图片插入，对于markdown文本最终渲染的不光是正文，Django后端还会渲染出目录，用户可以通过目录跳转到对应位置。

此外文章末尾可以发表评论，但需要用户处于登录状态，评论可以是多级的，在底层Comment对象有一个parent字段表明自己的父评论。此外，只有管理员能删除评论: )

![comment](image/comment.png)

**文章修改：**

文章详情有一个**更新**入口，管理员与作者本人可以对文章执行修改操作，在这个界面也可以执行删除操作：

![edit](image/edit.png)

这一功能实际上有一个bug，那就是非本人用户，甚至未登录用户都可以通过url，进入已有文章的编辑页面。但他们的更改请求不会被后端接受，毕竟token不正确。

**用户资料更新：**

![update](image/update.png)

用户中心可以修改用户名和密码，但很可惜因为精力有限没有在这个页面实现更多功能(比如上传用户头像)。

# 核心Features

## 后台管理系统

有两种方式管理后台：

第一种方式是在服务器打开django服务器：在项目主目录下运行 `python3 manage.py runserver`，此时后台项目就运行在localhost的8000（默认）端口了，接着以管理员身份向localhost发送POST、PATCH、DELETE请求，就可以实现对任意文章、用户的信息进行增删改查，也可以新建对象。这种方式功能强大，但缺点是没有图形化界面。

第二种方式是打开根域名下的admin子域( 1.15.33.167/admin/ )：这是django框架自带的后台管理系统，提供了优美简洁的图形化界面，以实现用户管理，但实际功能有限，只能对用户进行操作。原因在于models中定义的视图集是rest_framework中的viewsets的继承子类，其接口与django本身并不兼容。因此对于文章、分类、标签、avatar的管理只能通过命令行界面实现。

![general](image/admin.png)

## Token

Web程序使用HTTP协议传输data，而HTTP协议是无状态的协议，对于事务没有记忆能力。也就是说，如果没有其他形式的帮助，服务器是没有办法知道前后两次请求是否由同一名用户发起的，也就无法对用户身份验证。

传统Web开发中，身份验证主要是基于session会话机制进行的，session对象储存会话中的用户信息，并不随用户的页面跳转而消失，而是伴随整个会话进程中持续存在。但是当会话较多时，维护session将给服务器带来压力。

比较常见的方式是JWT(Json Web Token)验证，JWT是一套通用的标准，保障安全的传输。由于Token是储存在客户端的，所以不会对服务器造成很大的压力。

比如我们可以在后台管理系统申请一个token，结果返回就是这样：

![token](image/token.png)

如图所示，token就是一串很长的字符，用户拿到token就像拿到自己的令牌，可以在权限范围内请求、编辑数据。

## vue框架的使用实现前后端分离

传统的Web开发前后端高度耦合，不便于维护，一旦出现问题前端和后端都返工。尤其对于大型项目，采用这种开发模式无疑提高了沟通成本，降低效率。

**Vue框架**是一个组件化的前端框架，引进Vue将实现一个重要的概念：**“前后端分离”**。在该模式下，前端与后端将通过有限的API关联，实现信息传递。这种方式下，前端工程师和后端工程师只需要约定几个API接口，并行开发互不影响，只要API需求不发生变更，即便一方需要修改代码，另一边也无需相应修改。

![vue](image/vue.png)

**vue框架**同样具有高效的渲染能力，在相同代码量下，经过实测认为vue的确在渲染方面更为出众，这也是项目最终采用Django + Vue 开发的原因所在。项目的最终渲染效果如图(也可[ctrl + click 1.15.33.167](http://1.15.33.167/)直接访问)：

![Home](image/Home.png)

## 云服务器部署

为了项目最终的完成度，最终选择将项目部署到云服务器上，实现公网访问。这也是这次项目最具成就感的一步; )

首先在腾讯云服务器上用教育优惠购买一个最低配的1核2G服务器(十分卑微)：

![tx](image/tx.png)

SSH连接服务器 `ssh user@<ip>`：

SSH是secure shell的简称，一种非对称加密来实现安全传输的加密协议，目前SSH最为常见的用途就是远程登录系统。

![SSH](image/SSH.png)

接着在本地(windows)将代码上传到github.com，这个过程将中间文件加入.ignore文件，保证代码的纯净。

这一步主要是为了将项目整体迁移到服务器上，应该算走了弯路。更直接的做法是通过ssh协议(scp)直接传输文件夹，但上传github.com本身也是为了更好的版本控制，以及分享，所以问题不大。

![github](image/git.png)

之后在服务器端直接找一个喜欢的文件夹，使用 `git clone git@<server>:<repository>`克隆库到服务器，但此时还剩下最后一个步: **nginx**

## nginx 模块

项目迁移之后是不是 `npm serve run` 加上 `python3 manage.py runserver` 就完事了？我当时就这么naive，然而这样做缺少了proxy 作为转发代理的 server，无论尝试多少次访问服务器公网 ip 任何端口都不会有任何结果。

nginx的官方描述是这样的：

> nginx [engine x] is an HTTP and reverse proxy server, a mail proxy server, and a generic TCP/UDP proxy server, originally written by [Igor Sysoev](http://sysoev.ru/en/). For a long time, it has been running on many heavily loaded Russian sites including [Yandex](http://www.yandex.ru/), [Mail.Ru](http://mail.ru/), [VK](http://vk.com/), and [Rambler](http://www.rambler.ru/). According to Netcraft, nginx served or proxied [22.87% busiest sites in May 2021](https://news.netcraft.com/archives/2021/05/31/may-2021-web-server-survey.html). Here are some of the success stories: [Dropbox](https://blogs.dropbox.com/tech/2017/09/optimizing-web-servers-for-high-throughput-and-low-latency/), [Netflix](https://openconnect.netflix.com/en/software/), [Wordpress.com](https://www.nginx.com/case-studies/nginx-wordpress-com/), [FastMail.FM](http://blog.fastmail.fm/2007/01/04/webimappop-frontend-proxies-changed-to-nginx/).

可见nignx十分强大，它在这次项目中不仅能够作为proxy承担代理的作用，更能作为负载均衡器，提升网站性能。

首先apt-get下载nginx，之后在/etc/nginx/sites-avalible增加一个配置文件vue_blog ，当然也可以另外取名:

![nginx](image/nginx.png)

大意是对来自网络的请求解析，并请求不同资源返回到client，比如请求静态资源时就转发到collected_static文件，请求动态资源就转发到默认的index.html，这个过程很好地完成了对请求的分流。

当然本人在配置nginx过程中犯下了一个困扰长达两天的问题，这个问题使得本人在配置nginx后依然面临404页面，之后查询nginx错误日志  `/var/log/nginx/error.log`  才最终定位到问题所在。

运行 `tail -f /var/log/nginx/error.log` 发现每次nginx的请求都被403 permission deny 13 了，经过一番查证认为是nginx配置不当缺乏权限造成的。之后改变 `vim /etc/nginx/nginx.conf` 中的user 为 root，就成功解决了。

之后运行最后两步:

`service nginx start`

`gunicorn --bind unix:/tmp/1.15.33.167.socket my_blog.wsgi:application` 

前一步是启用nginx服务，而后一步是将gunicorn绑定到后端Django框架代码中，至此就大！功！告！成！啦！已经可以正常访问公网IP并显示预期中的页面。

# 文档说明

上传的**压缩文件**包括

- 项目报告(本文件)；

- sql文件（Django后端提供了ORM抽象机制，此文件是通过修改setting，数据迁移时后端自动在terminal输出的结果）；

- 以及项目主体(Blog-Drf-Vue，因为vue 项目初始化产生大量build文件，因此压缩文件中仅给出了项目中编写过的文件，以保证文档的轻量化。完整项目文件在本人github上：`git@github.com:ekonwang/Blog-Drf-Vue.git`)

本项目文件Blog-Drf-Vue架构如图所示，通过tree指令生成文件树 ：

Blog-Drf-Vue
├── article
│   ├── admin.py
│   ├── apps.py
│   ├── failed_serializers.py
│   ├── __init__.py
│   ├── migrations
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── collected_static
│   ├── admin
│   ├── css
│   ├── favicon.ico
│   ├── index.html
│   ├── js
│   └── rest_framework
├── comment
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── tests.py
│   └── views.py
├── db.sqlite3
├── drf_vue_blog
│   ├── asgi.py
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── frontend
│   ├── babel.config.js
│   ├── dist
│   ├── node_modules
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   ├── README.md
│   ├── src
│   └── vue.config.js
├── manage.py
├── media
│   └── avatar
├── README.md
├── requirements.txt
└── user_info
    ├── admin.py
    ├── apps.py
    ├── __init__.py
    ├── migrations
    ├── models.py
    ├── permissions.py
    ├── serializers.py
    ├── tests.py
    └── views.py

解释一下各个一级文件/文件夹的作用：

frontend文件夹是前端文件夹，通过vue-cli的初始化生成，其中src是编辑对象文件，包含了渲染所需的源文件。dist是开发完毕后搜集的静态文件，其他文件夹包含了vue框架中必须的组件。

article是article APP对应的文件夹，实现文章管理。主要的文件是models.py、serializers.py、views.py，其余为框架生成的相应必须文件。models.py 定义了项目中用到的模型，包括Article，Category，Tag，以及 Avatar; serializers.py 定义了序列化各个模型的方法；views.py 则定义了视图集。此外同级user_info、comment分别实现用户管理以及评论管理，内部架构与article相同，这里就不再赘述。

media文件夹用来存放图片等媒体资源。

collected_static是项目搜集的全部静态资源，该文件夹下有index.html。

drf_vue_blog与项目文件夹名一致，是django框架的核心文件夹，包含setting.py（配置文件），urls.py（路由文件）。

db.sqlite3是数据库文件，项目数据储存在该文件中，包含用户数据、文章数据、评论、标签等所有可编辑的数据。

readme.md是说明文件，requirements.py 在部署时很有用，它记录了项目所有依赖。



