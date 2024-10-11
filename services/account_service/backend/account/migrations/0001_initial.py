# Generated by Django 4.2.16 on 2024-10-10 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_number', models.CharField(max_length=20, unique=True)),
                ('user_id', models.IntegerField()),
                ('account_type', models.CharField(choices=[('Savings', 'Savings'), ('Checking', 'Checking'), ('Deposit', 'Deposit')], max_length=50)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=15)),
                ('currency', models.CharField(max_length=3)),
                ('interest_rate', models.DecimalField(decimal_places=2, default=0.0, max_digits=5)),
                ('opened_date', models.DateField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('Closed', 'Closed'), ('Suspended', 'Suspended')], default='Active', max_length=20)),
                ('overdraft_limit', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
