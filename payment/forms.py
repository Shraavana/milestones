from django import forms
from .models import *
import re


class AddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():  # Iterate over field name and field object
           field.widget.attrs['class'] = 'form-control'

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 3 or any(char.isdigit() for char in name):
            raise forms.ValidationError("Name must contain at least 3 letters and no numbers.")
        return name
   
    
    def clean_pincode(self):
        pincode = self.cleaned_data['pincode']
        if len(pincode) != 6 or not pincode.isdigit():
            raise forms.ValidationError("Pincode must contain 6 digits.")
        return pincode
    
   

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        phone_digits = re.sub(r'\D', '', phone)
        if len(phone_digits) != 10:
               raise forms.ValidationError("Phone number must contain exactly 10 digits.")
    
        if len(set(phone_digits)) == 1:
            raise forms.ValidationError("Phone number must contain different digits.")
        return phone

    
    class Meta:
        model = Address
        fields = ['name', 'address', 'phone', 'district', 'pincode']





class PaymentMethodForm(forms.Form):
    payment_method = forms.CharField(max_length=100)
