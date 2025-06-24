from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserActionLog
from .forms import CustomUserCreationForm, CustomUserChangeForm
@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'employee_code', 'role', 'profile_picture', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'first_name', 'last_name', 'employee_code', 'role', 'profile_picture')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'employee_code', 'role', 'profile_picture', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name', 'employee_code')
    ordering = ('email',)

@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'method','data', 'path', 'get_local_timestamp', 'ip_address')
    list_filter = ('method', 'timestamp', 'user')
    search_fields = ('path', 'data', 'changes', 'user__email')

    readonly_fields = ('user', 'method', 'path', 'timestamp', 'ip_address', 'user_agent', 'data', 'changes')

    def get_local_timestamp(self, obj):
        return obj.get_local_timestamp()
    get_local_timestamp.short_description = "Timestamp (IST)"