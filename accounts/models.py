from django.db import models
from django.contrib.auth.models import User #django built in user facility
from .constants import ACCOUNT_TYPE,GENDER

# Create your models here.
class Bank(models.Model):
    name = models.CharField(max_length=255)
    is_bankrupt = models.BooleanField(default=False)
    
class UserBankAccount(models.Model):     
    user = models.OneToOneField(User, related_name='account',on_delete=models.CASCADE)
    account_type = models.CharField(max_length=10,choices=ACCOUNT_TYPE)
    account_no = models.IntegerField(unique = True)  # duijon user er account no kokhono same hote parbe na
    birth_date = models.DateField(null=True,blank=True)
    gender= models.CharField(max_length=10,choices=GENDER)
    initial_deposite_date = models.DateField(auto_now_add=True)
    balance = models.DecimalField(default=0, max_digits=12, decimal_places=2)

    def __str__(self):
        return str(self.account_no)

class UserAddress(models.Model):
    user = models.OneToOneField(User, related_name='address',on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    city =models.CharField(max_length=100)
    postal_code = models.IntegerField()
    country = models.CharField(max_length=100)
    
    def __str__(self):
        return str(self.user.email)
