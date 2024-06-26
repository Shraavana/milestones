from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager,PermissionsMixin,Group,Permission
from django.core.validators import FileExtensionValidator
from django.utils.safestring import mark_safe
from django.utils import timezone


# Create your models here.




class UserManager(BaseUserManager):
    def create_user(self,first_name,last_name,username,email,phone,password=None):
        if not email:
            raise ValueError('User must an email address')
        if not username:
            raise ValueError('User must have a username')
        
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            phone = phone,
        )
        user.set_password(password)
        user.save(using = self._db)
        return user
    
    def create_superuser(self,first_name,last_name,username,phone,email,password=None):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
            phone = phone
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser,PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=100,unique=True)
    email = models.EmailField(max_length=200,unique=True)
    phone = models.CharField(max_length=12,blank=True)

    #required fiels
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','first_name','last_name', 'phone']
    objects=UserManager()

    def __str__(self):
        return self.email
    def has_perm(self, perm, obj=None):
        return self.is_admin
    def has_module_perms(self,app_lebel):
        return True
    

    
class category(models.Model):
    category_name=models.CharField(max_length=100,unique=True)
    is_deleted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    

    def __str__(self) :
        return self.category_name
    
class Brand(models.Model):
    brand_name = models.CharField(max_length=255,unique=True)
    is_active= models.BooleanField(default=True)

    def __str__(self) :
        return self.brand_name
    
class Color(models.Model):
    color_name = models.CharField(max_length=100)
    color_code = models.CharField(max_length=100)

    def color_bg(self):
        return mark_safe('<div style="width:50px; height:50px; background-color=%s"></div>' % (self.color_code))

    def __str__(self):
        return self.color_name


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    description = models.TextField(null=True)
    is_available=models.BooleanField(default=True)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    category = models.ForeignKey('category', on_delete=models.CASCADE)
    featured = models.BooleanField(default=False)
    specifications = models.TextField(null =True, blank =True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Products"

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def undo(self):
        self.is_deleted = False
        self.save()

    def __str__(self):
        return self.product_name
    
    def get_percentage(self):
        new_price = (self.price /self.old_price) * 100
        return new_price

class ProductImages(models.Model):
    product = models.ForeignKey(Product ,related_name='product_image',on_delete=models.SET_NULL, null = True)
    images = models.ImageField(upload_to='photo/product_images3',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'], message="Only JPG, JPEG, and PNG files are allowed.")
                    ])
    date = models.DateTimeField(auto_now_add= True)
    
    class Meta:
        verbose_name_plural = "Product Images"

class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    old_price = models.PositiveIntegerField()
    stock = models.IntegerField()
    is_available=models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    image = models.ImageField(upload_to='photo/product_images',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'], message="Only JPG, JPEG, and PNG files are allowed.")
                    ],
                    default=timezone.now  # Example default value using timezone.now
                    )
    def __str__(self):
        return f"{self.product} - {self.color} - ${self.price}"
    def image_tag(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % self.image.url)


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
