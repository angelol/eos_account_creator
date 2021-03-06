# Generated by Django 2.0.6 on 2018-06-19 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('buy', '0007_purchase_payment_received_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeCharge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('currency', models.CharField(max_length=512)),
                ('response', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='purchase',
            name='currency',
            field=models.CharField(default='usd', max_length=512),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchase',
            name='price_cents',
            field=models.IntegerField(null=True),
        ),
    ]
