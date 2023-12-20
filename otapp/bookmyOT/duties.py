
import requests
from .config import domain_name
from django.contrib import messages


def get_status_duties_dash(request, type):
    data = requests.get(f'{domain_name.url}GetAllDutys?status=&type={type}&startdate=&enddate=').json()
    return data['ResultData']

def duties_list_get(request):
    Duties_URL = requests.get(f'{domain_name.url}GetAllDutys').json()
    if Duties_URL['Status'] == False:
        messages.info(request, 'Something went wrong..!')
    else:
        duties_result = Duties_URL['ResultData']
        return duties_result
    
def duties_filter_list(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        dtype = request.POST.get('dtype')
        stdate = request.POST.get('stdate')
        endate = request.POST.get('endate')
        print(stdate, endate, status, dtype)
        data = requests.get(f'{domain_name.url}GetAllDutys?status={status}&type={dtype}&startdate={stdate}&enddate={endate}').json()
        print(data)
        return data['ResultData']
    

def get_dash_duties_list(request):
    data = requests.get(f'{domain_name.url}GetAllDutys').json()
    return data['ResultData']