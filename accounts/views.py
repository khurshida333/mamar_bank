from django.shortcuts import render ,redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm
from django.urls import reverse_lazy

from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView,LogoutView

from django.http import HttpResponseRedirect
from django.views import View

from .forms import UserUpdateForm

# Create your views here.

class UserRegistrationView(FormView):
    template_name ='accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('register')

    def form_valid(self,form):
        user = form.save()  # save() will return our_user , which is a instance of the built in User
        login(self.request, user)
        return super().form_valid(form) #super calls FormView's   default actions

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
           return reverse_lazy('home')
    
# class UserLogoutView(LogoutView):
#     def get_success_url(self):
#         if self.request.user.is_authenticated:
#             logout(self.request)
#         return reverse_lazy('home')


class UserLogoutView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
           logout(request)
        return HttpResponseRedirect(reverse_lazy('home'))
    
class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user) # tells the form to use the current user's information to fill in the form fields.
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})