from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import EmailValidator
from .models import Comment,Post,Profile


class EmailPostForm(forms.Form):
    name=forms.CharField(max_length=250)
    email=forms.EmailField()
    to=forms.EmailField()
    comments=forms.CharField(required=False,widget=forms.Textarea)

class CommentForm(forms.ModelForm):
    class Meta:
        model=Comment
        fields=['body','parent']
        widgets = {
            'parent': forms.HiddenInput(),  # Hide parent field in form
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...'
            }),
        }


class SearchForm(forms.Form):
    query=forms.CharField()


class CustomerCreation(UserCreationForm):
    email=forms.EmailField(required=True)
    class Meta:
        model=User
        fields=['username','email','password1','password2']


class PostForm(forms.ModelForm):
    class Meta:
        model=Post
        fields=['title','body','featured_image','featured_image_caption','status','tags']
        widgets = {
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'data-markdown': True
            }),
            'status': forms.RadioSelect,
            'featured_image_caption': forms.TextInput(attrs={
                'placeholder': 'Optional image description...'
            })
        }
        help_texts = {
            'slug': 'Will be auto-generated from title if left blank',
            'featured_image': 'Recommended aspect ratio: 2:1 (1200x630px)',
        }
        def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          self.fields['featured_image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
          })

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    
    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'website', 'twitter', 'github']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            profile.save()
        return profile

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your name'
        })
    )
    email = forms.EmailField(
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your email address'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message...'
        })
    )
    cc_myself = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Send me a copy'
    )

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message) < 10:
            raise forms.ValidationError("Message is too short (minimum 10 characters)")
        return message 
