from article.permissions import IsAdminUserOrReadOnly
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from rest_framework import status, mixins, generics, viewsets, filters
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from article.permissions import IsOwnerOrAdminOrReadOnly
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse, Http404
from article.models import Article, Avatar, Category, Tag
#from article.serializers import ArticleListSerializer, ArticleDetailSerializer
from article.serializers import ArticleSerializer, CategoryDetailSerializer, CategorySerializer, TagSerializer, ArticleDetailSerializer, AvatarSerializer
# Create your views here.

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


class AvatarViewSet(viewsets.ModelViewSet):
    queryset = Avatar.objects.all()
    serializer_class = AvatarSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    pagination_class = None


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

        
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    pagination_class = None


""" @api_view(['GET', 'POST'])
def article_list(request):
    permission_classes = [IsAuthenticatedOrReadOnly]
    if request.method == 'GET':
        articles = Article.objects.all()
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ArticleListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.author = request.user
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) """

""" class ArticleList(generics.ListCreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)  """
    


""" class ArticleDetail(mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    generics.GenericAPIView):
                    
    queryset = Article.objects.all()
    serializer_class = ArticleDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs) """

""" class ArticleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly] 

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs) """