from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_default_roles_and_users(apps, schema_editor):
    Role = apps.get_model('users', 'Role')
    User = apps.get_model('users', 'User')

    default_roles = [
        (1, 'admin'),
        (2, 'teacher'),
        (3, 'student'),
    ]
    for role_id, role_name in default_roles:
        Role.objects.get_or_create(id=role_id, name=role_name)

    admin_role = Role.objects.get(id=1)
    teacher_role = Role.objects.get(id=2)
    student_role = Role.objects.get(id=3)

    default_users = [
        ('admin', 'admin@example.com', admin_role),
        ('teacher', 'teacher@example.com', teacher_role),
        ('student', 'student@example.com', student_role),
    ]

    for username, email, role in default_users:
        User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'password': make_password('atsats'),
                'role': role,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_roles_and_users),
    ]
