from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Comment,Post


class EmailPostForm(forms.Form):
    name=forms.CharField(max_length=250)
    email=forms.EmailField()
    to=forms.EmailField()
    comments=forms.CharField(required=False,widget=forms.Textarea)

class CommentForm(forms.ModelForm):
    class Meta:
        model=Comment
        fields=['name','email','body']


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
        fields=['title','body','featured_image','status']
