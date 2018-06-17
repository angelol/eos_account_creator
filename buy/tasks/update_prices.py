import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eos_accounts.settings")
sys.path.append(os.getcwd())
import django
django.setup()

def main():
    from buy.models import PriceData
    PriceData.update()
    
if __name__ == '__main__':
    
    main()