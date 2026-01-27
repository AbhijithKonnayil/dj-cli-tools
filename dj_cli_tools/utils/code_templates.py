class CodeTemplates:
    MODEL = """
class {model_name}(models.Model):
    # Define your model fields here
    pass
"""

    SERIALIZER = """
class {serializer_name}(serializers.ModelSerializer):
    class Meta:
        model = {model_name}
        fields = '__all__'
"""

    VIEWSET = """
class {viewset_name}(viewsets.ModelViewSet):
    queryset = {model_name}.objects.all()
    serializer_class = {serializer_name}
"""

    FACTORY = """
class {factory_name}(factory.django.DjangoModelFactory):
    class Meta:
        model = {model_name}
"""

    ADMIN = """
@admin.register({model_name})
class {model_name}Admin(admin.ModelAdmin):
    pass
"""

    URLS_INITIAL = """from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
]
"""

    URLS_ROUTER_DEF = "\nrouter = DefaultRouter()\n"
    
    URLS_ROUTER_IMPORT = "from rest_framework.routers import DefaultRouter\n"
