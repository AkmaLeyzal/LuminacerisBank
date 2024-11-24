# Generated by Django 5.1.1 on 2024-11-13 02:33

import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('permissions', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('username', models.CharField(max_length=50, unique=True)),
                ('full_name', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('LOCKED', 'Locked'), ('SUSPENDED', 'Suspended'), ('BLOCKED', 'Blocked'), ('PENDING', 'Pending Verification')], default='PENDING', max_length=20)),
                ('last_login_ip', models.GenericIPAddressField(null=True)),
                ('last_login_date', models.DateTimeField(null=True)),
                ('failed_login_attempts', models.IntegerField(default=0)),
                ('last_failed_login', models.DateTimeField(null=True)),
                ('password_changed_at', models.DateTimeField(null=True)),
                ('is_email_verified', models.BooleanField(default=False)),
                ('is_phone_verified', models.BooleanField(default=False)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True)),
                ('email_verification_token', models.CharField(blank=True, max_length=100, null=True)),
                ('phone_verification_code', models.CharField(blank=True, max_length=6, null=True)),
                ('is_mfa_enabled', models.BooleanField(default=False)),
                ('mfa_secret', models.CharField(blank=True, max_length=32, null=True)),
                ('mfa_backup_codes', models.JSONField(default=list)),
                ('is_blocked', models.BooleanField(default=False)),
                ('blocked_at', models.DateTimeField(blank=True, null=True)),
                ('block_reason', models.TextField(blank=True, null=True)),
                ('blocked_by', models.CharField(blank=True, max_length=50, null=True)),
                ('block_expires_at', models.DateTimeField(blank=True, null=True)),
                ('preferred_language', models.CharField(default='en', max_length=20)),
                ('notification_preferences', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_activity', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
                ('roles', models.ManyToManyField(blank=True, related_name='users', to='authentication.role')),
            ],
            options={
                'db_table': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='SecurityAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('event_details', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'security_audit_logs',
            },
        ),
        migrations.CreateModel(
            name='TokenBlacklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token_jti', models.CharField(max_length=255, unique=True)),
                ('token_type', models.CharField(max_length=50)),
                ('blacklisted_by', models.CharField(max_length=50)),
                ('blacklist_reason', models.TextField()),
                ('metadata', models.JSONField(default=dict)),
                ('blacklisted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'token_blacklist',
            },
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_by', models.CharField(max_length=50)),
                ('assigned_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.role')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_roles',
            },
        ),
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('session_id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('refresh_token_jti', models.CharField(max_length=255)),
                ('access_token_jti', models.CharField(max_length=255)),
                ('device_id', models.CharField(max_length=255, null=True)),
                ('device_name', models.CharField(max_length=255, null=True)),
                ('device_type', models.CharField(max_length=50, null=True)),
                ('user_agent', models.CharField(max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('location', models.CharField(max_length=255, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_sessions',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='users_email_4b85f2_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['username'], name='users_usernam_baeb4b_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['status'], name='users_status_9ca66f_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_blocked'], name='users_is_bloc_7a912f_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['last_activity'], name='users_last_ac_a9fd4f_idx'),
        ),
        migrations.AddIndex(
            model_name='securityauditlog',
            index=models.Index(fields=['user', 'event_type'], name='security_au_user_id_e9a996_idx'),
        ),
        migrations.AddIndex(
            model_name='securityauditlog',
            index=models.Index(fields=['created_at'], name='security_au_created_263d61_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenblacklist',
            index=models.Index(fields=['token_jti'], name='token_black_token_j_9016ba_idx'),
        ),
        migrations.AddIndex(
            model_name='tokenblacklist',
            index=models.Index(fields=['user', 'blacklisted_at'], name='token_black_user_id_09e555_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='userrole',
            unique_together={('user', 'role')},
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['refresh_token_jti'], name='user_sessio_refresh_aecb8e_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['user', 'is_active'], name='user_sessio_user_id_bb1b83_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['device_id'], name='user_sessio_device__4ac8e0_idx'),
        ),
    ]
