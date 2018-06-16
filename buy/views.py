from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

# Create your views here.
def choose(request):
    return render(request, "buy/choose.html")
    
@require_POST
def submit_account_name(request):
    account_name = request.POST['account_name']
    # test if valid eos account name
    
    # check if eos account name is still free
    
    # add chosen account name to session
    p = Purchase.objects.create(account_name=account_name)
    
    # if successful, redirect to /keys/
    return redirect("/keys/")
    
def keys(request):
    
    return render(request, "buy/keys.html")