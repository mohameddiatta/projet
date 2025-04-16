from django import forms
from .models import CustomUser

class StaffForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=150)
    address = forms.CharField(widget=forms.Textarea)

    def clean_username(self):
        username = self.cleaned_data['username']
        if CustomUser.objects.filter(username=username).exists():
            user = CustomUser.objects.get(username=username)
            if hasattr(user, 'staffs'):
                raise forms.ValidationError("Un staff avec ce nom d'utilisateur existe déjà")
        return username

    class Meta:
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'address']