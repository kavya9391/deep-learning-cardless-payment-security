from django.contrib import admin
from .models import TokenCountModel,UserFilesModel,UserRegistrationModel,TransactionModel

# Register your models here.
admin.site.register(UserFilesModel)
admin.site.register(UserRegistrationModel)
admin.site.register(TransactionModel)


admin.site.register(TokenCountModel)
