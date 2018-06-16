from django.db import models

# Create your models here.
class Purchase(models.Model):
    account_name = models.CharField(max_length=12)
    public_key = models.CharField(max_length=53, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return account_name