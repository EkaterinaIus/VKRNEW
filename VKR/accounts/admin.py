from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Child


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'has_access_code', 'date_joined')
    fieldsets = UserAdmin.fieldsets + (
        ('Код доступа', {'fields': ('access_code_hash',)}),
    )

    def has_access_code(self, obj):
        return bool(obj.access_code_hash)
    has_access_code.boolean = True
    has_access_code.short_description = 'Есть код'


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'age', 'level', 'initial_level_source', 'created_at')
    list_filter = ('level', 'initial_level_source')
