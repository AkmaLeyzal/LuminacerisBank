# Generated by Django 4.2.16 on 2024-10-09 16:05

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('card_number', models.CharField(max_length=16, unique=True)),
                ('account_id', models.IntegerField()),
                ('card_type', models.CharField(choices=[('DEBIT', 'Debit'), ('CREDIT', 'Credit'), ('PREPAID', 'Prepaid')], max_length=7)),
                ('cardholder_name', models.CharField(max_length=255)),
                ('expiry_date', models.DateField()),
                ('cvv', models.CharField(max_length=4)),
                ('pin_hash', models.CharField(max_length=128)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('BLOCKED', 'Blocked'), ('CANCELLED', 'Cancelled')], default='ACTIVE', max_length=10)),
                ('issued_date', models.DateField(auto_now_add=True)),
                ('limit', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
