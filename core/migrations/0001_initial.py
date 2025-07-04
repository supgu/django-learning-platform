# Generated by Django 5.2.1 on 2025-05-30 09:59

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("content", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="设置键"
                    ),
                ),
                ("value", models.TextField(verbose_name="设置值")),
                (
                    "description",
                    models.CharField(blank=True, max_length=200, verbose_name="描述"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
            ],
            options={
                "verbose_name": "网站设置",
                "verbose_name_plural": "网站设置",
            },
        ),
        migrations.CreateModel(
            name="Recommendation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("score", models.FloatField(verbose_name="推荐分数")),
                ("reason", models.CharField(max_length=200, verbose_name="推荐理由")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="推荐时间"),
                ),
                (
                    "clicked",
                    models.BooleanField(default=False, verbose_name="是否点击"),
                ),
                (
                    "content",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="content.creativecontent",
                        verbose_name="推荐内容",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "推荐记录",
                "verbose_name_plural": "推荐记录",
                "ordering": ["-created_at"],
                "unique_together": {("user", "content")},
            },
        ),
        migrations.CreateModel(
            name="SiteVisit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("session_key", models.CharField(max_length=40, verbose_name="会话键")),
                ("ip_address", models.GenericIPAddressField(verbose_name="IP地址")),
                ("user_agent", models.TextField(blank=True, verbose_name="用户代理")),
                (
                    "visited_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="访问时间"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="用户",
                    ),
                ),
            ],
            options={
                "verbose_name": "网站访问",
                "verbose_name_plural": "网站访问记录",
                "unique_together": {("session_key", "ip_address")},
            },
        ),
    ]
