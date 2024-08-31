from django import forms
from .models import Transaction
from accounts.models import Bank
class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        
        self.account = kwargs.pop('account') # account value ke pop/get kore anlam
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True # ei field disable thakbe
        self.fields['transaction_type'].widget = forms.HiddenInput() # user er theke hide kora thakbe

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()

class DepositForm(TransactionForm):
    def clean_amount(self): # amount field ke filter korbo
        min_deposit_amount = 100
        amount = self.cleaned_data.get('amount') # user er fill up kora form theke amra amount field er value ke niye aslam, 50
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} $'
            )

        return amount
    
class SendMoneyForm(TransactionForm):
    def clean_amount(self): # amount field ke filter korbo
        bank = Bank.objects.first()  # Assuming there's only one bank. Adjust if necessary.
        if not bank or bank.is_bankrupt:
            raise forms.ValidationError(f'Mamar Bank is gone bankrupt.')
        min_amount = 50
        amount = self.cleaned_data.get('amount') # user er fill up kora form theke amra amount field er value ke niye aslam, 50
        if amount < min_amount:
            raise forms.ValidationError(
                f'You need to Send at least {min_amount} $'
            )

        return amount


class WithdrawForm(TransactionForm):
    def clean_amount(self):
        bank = Bank.objects.first()  # Assuming there's only one bank. Adjust if necessary.
        if not bank or bank.is_bankrupt:
            raise forms.ValidationError(f'Mamar Bank is gone bankrupt.')

        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} $ in your account. '
                'You cannot withdraw more than your account balance.'
            )

        return amount


class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        bank = Bank.objects.first()  # Assuming there's only one bank. Adjust if necessary.
        if not bank or bank.is_bankrupt:
            raise forms.ValidationError(f'Mamar Bank is gone bankrupt.')
        amount = self.cleaned_data.get('amount')
        user_balance = self.account.balance  # Assuming you have access to the user's balance

     # Check if the amount is greater than the user's balance
        if amount > user_balance:
            # Check if the amount is not more than 3 times the user's balance
            if amount <= 3 * user_balance:
                # Logic to send the request to admin (you can customize this part)
                # For example, you might save it with a special status
                self.instance.status = 'Pending Admin Approval'
            else:
                raise forms.ValidationError("The requested amount cannot exceed three times your balance.")
        
        return amount