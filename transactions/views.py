from django.shortcuts import render ,get_object_or_404, redirect
from django.http import HttpResponse

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, TemplateView
from django.views.generic import CreateView, ListView
from django.views import View

from django.urls import reverse_lazy
from datetime import datetime
from django.contrib import messages
from django.db.models import Sum
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import Transaction,UserBankAccount
from accounts.models import Bank
from .forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
    SendMoneyForm,
)
from transactions.constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID , SEND_MONEY , RECIEVED_MONEY


# Create your views here.

def send_transaction_email(user,amount, subject, template):
        message = render_to_string(template,{
            'user' : user,
            'amount' : amount,
        })
        send_email = EmailMultiAlternatives(subject, '' , to=[user.email])
        send_email.attach_alternative(message, "text/html")
        send_email.send()
        

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transactions:transaction_report')
    
    
    def get_form_kwargs(self):   # Return the keyword arguments for instantiating the form.........."instantiating the form" refers to the process of creating a new form object using the parameters specified in kwargs.
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) # template e context data pass kora
        context.update({
            'title': self.title
        })

        return context
    
class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount') # user er fill up kora form theke amra amount field er value ke niye aslam
        account = self.request.user.account
        # if not account.initial_deposit_date:
        #     now = timezone.now()
        #     account.initial_deposit_date = now
        account.balance += amount # amount = 200, tar ager balance = 0 taka new balance = 0+200 = 200
        account.save(
            update_fields=[
                'balance'
            ]
        )
        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )

        #email sending oparation------->
        send_transaction_email(self.request.user,amount, "Deposite Message", "transactions/deposite_email.html")
    
        return super().form_valid(form)
    
class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
         # Retrieve the specific Bank instance
        bank = Bank.objects.first()  # Assuming there's only one bank. Adjust if necessary.
        
        if bank and not bank.is_bankrupt:
               self.request.user.account.balance -= form.cleaned_data.get('amount')
               self.request.user.account.save(update_fields=['balance'])

               messages.success(
               self.request,
               f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
               )   
               send_transaction_email(self.request.user,amount, "Withdrawal Message", "transactions/withdrawal_email.html")
               return super().form_valid(form)
        else:
               messages.error(self.request, "Sorry, the bank has gone bankrupt.")
               return self.form_invalid(form)
               

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        # Retrieve the specific Bank instance
        bank = Bank.objects.first()  # Assuming there's only one bank. Adjust if necessary.
        
        if bank and not bank.is_bankrupt:
             # Set the account on the form instance
            form.instance.account = self.request.user.account
             # Access the user's balance after the account is set
            user_balance = form.instance.account.balance


            amount = form.cleaned_data.get('amount')
            current_loan_count = Transaction.objects.filter(
            account=self.request.user.account, transaction_type=LOAN,loan_approve=True).count()
            if current_loan_count >= 3:
               return HttpResponse("You have cross the loan limits")
        
            messages.success(
               self.request,
               f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
               
            )
            send_transaction_email(self.request.user,amount, "Loan Request Message", "transactions/loan_request_email.html")

            return super().form_valid(form)
        else:
            # Error message if the bank is bankrupt
           messages.error(self.request, "Sorry, the bank has gone bankrupt.")
           return self.form_invalid(form)
    def get_success_url(self):
        return reverse_lazy('transactions:transaction_report')

class TransactionReportView(LoginRequiredMixin, ListView): # hee ListView will list 'Transaction' objects.
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0 # filter korar pore ba age amar total balance ke show korbe
    context_object_name = 'report_list'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter( account=self.request.user.account)

        start_date_str = self.request.GET.get('start_date')  #Django's self.request.GET is a dictionary-like object that holds all the GET parameters in the URL.
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct() # unique queryset hote hobe
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
  
        return context
    
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
                # Reduce the loan amount from the user's balance
                # 5000, 500 + 5000 = 5500
                # balance = 3000, loan = 5000
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('transactions:loan_list')
            else:
                messages.error(
            self.request,
            f'Loan amount is greater than available balance'
        )

        return redirect('transections:loan_list')


class LoanListView(LoginRequiredMixin,ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans' # loan list ta ei loans context er moddhe thakbe
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account,transaction_type=LOAN)
        print(queryset)
        return queryset

class SendMoneyPageView(LoginRequiredMixin, ListView):
    model = UserBankAccount
    template_name = 'transactions/send_money_page.html'
    context_object_name = 'user_accounts'  # Name to use in the template for the list of objects

class SendMoneyView(TransactionCreateMixin):
    form_class = SendMoneyForm
    title = 'Send_Money'

    def get_initial(self):
        # Set initial data for the form
        initial = super().get_initial()
        initial = {'transaction_type': SEND_MONEY}
        return initial

    def form_valid(self, form):
        # Retrieve the amount from the submitted form
        amount = form.cleaned_data.get('amount')
        sender_account = self.request.user.account  

        # Get recipient's account ID from the URL
        recipient_account_id = self.kwargs.get('user_account_id')
        recipient_account = get_object_or_404(UserBankAccount, id=recipient_account_id)   

        # Retrieve the specific Bank instance
        bank = Bank.objects.first()  # Assuming there's only one bank. Adjust if necessary.
        
        if bank and not bank.is_bankrupt:
            # Ensure the sender has enough balance
            if sender_account.balance < amount:
                form.add_error('amount', 'Insufficient balance to complete the transaction.')
                return self.form_invalid(form)
            # Deduct amount from sender's account
            sender_account.balance -= amount
            sender_account.save(update_fields=['balance'])

            # Add amount to recipient's account
            recipient_account.balance += amount
            recipient_account.save(update_fields=['balance'])

            # Call the parent form_valid to create the sender's transaction
            response = super().form_valid(form)

            # Create a transaction record for the recipient
            Transaction.objects.create(
                account=recipient_account,
                amount=amount,  # Positive amount for receiving money
                balance_after_transaction=recipient_account.balance,
                transaction_type=RECIEVED_MONEY  # Assuming RECIEVED_MONEY corresponds to the correct transaction type
            )
             # Success message for the user
            
            messages.success(
               self.request,
               f"{'{:,.2f}'.format(float(amount))}$ was deposited to your friend's account successfully"
            )

            return response
        else:
           # Error message if the bank is bankrupt
           messages.error(self.request, "Sorry, the bank has gone bankrupt.")
           return self.form_invalid(form)