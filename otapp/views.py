from django.shortcuts import render, redirect
from otapp.bookmyOT.config import *
from otapp.bookmyOT.duties import *
from otapp.bookmyOT.hospital import *
from otapp.bookmyOT.suergeries import *
from otapp.bookmyOT.utilities import send_email
from .bookmyOT.dashboard import *
from otapp.bookmyOT.doctors import *
import requests
from .decorators import session_required # My custom decorator
from django.contrib.auth import logout
import random
import pandas as pd
from django.http import JsonResponse
import io
from django.http import HttpResponse
from io import BytesIO



#  Views Starts from here..

def terms_and_conditions(request):
    return render(request, 'main/terms-and-conditions.html')

def privacy_policy(request):
    return render(request, 'main/privacy-policy.html')

def hospital_registration(request):
    url = f'{domain_name.url}adminorHospitalLogin'
    if request.method == 'POST':
        hospitalname = request.POST.get('hospitalname')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        pwd = mobile[-4:]
        user_data = {"inputdata": {"username": email, "password": pwd}}
        response = requests.post(url, json = user_data)
        res = response.json()
       
        if res['Status'] == True:
            messages.error(request, "Email already exists, try with another email..!")
            return redirect('hospital_registration')
        else:
            generated_otp = random.randint(100000, 999999)
            subject = 'Registration OTP'
            message_body = f'Your regestration OTP for BookMyOT is  {generated_otp}'
            send_email(subject, message_body, email)
            request.session['user_email'] = email
            request.session['pwd'] = pwd
            request.session['mobile_num'] = mobile
            request.session['hospital_name'] = hospitalname
            request.session['registration_otp'] = generated_otp
            request.session.set_expiry(60 * 5)
            messages.info(request, "Hospital registration in progress, Enter OTP for verification..")
            return redirect('verify_otp')
    return render(request, 'main/hospital-registration.html')

def verify_otp(request):
    reg_url = f'{domain_name.url}CreateHospitalProfile'
    email = request.session.get('user_email')
    pwd = request.session.get('pwd')
    hospital_name = request.session.get('hospital_name')
    mobile_num = request.session.get('mobile_num')
  
    if len(email) > 2:
        parts = email.split("@")
        if len(parts) == 2:
            change_email = f"{parts[0][:4]}{'*'*4}@{parts[1]}"
    if request.method == 'POST':
        first = request.POST.get('first')
        second = request.POST.get('second')
        third = request.POST.get('third')
        fourth = request.POST.get('fourth')
        fifth = request.POST.get('fifth')
        sixth = request.POST.get('sixth')
        stored_otp = request.session.get('registration_otp')
        user_entered_otp = int(f"{first}{second}{third}{fourth}{fifth}{sixth}")
        # stored_otp = 000000
        try:
            if user_entered_otp == stored_otp:
                del request.session['registration_otp']

                data = {
                    "inputdata": {
                        "hospitalname": hospital_name,
                        "mobile": mobile_num,
                        "email": email,
                        "username": email,
                        "psw": pwd,
                        "tier": None
                    }
                }
                a = requests.post(reg_url, json=data).json()
                
                messages.success(request, 'OTP authentication was successful; you may now proceed to log in.')
                return redirect('http://hospital.bookmyot.com/Account/Login')
            else:
                messages.error(request, 'Entered OTP did not match, please try again..!')
                return redirect('verify_otp')
        except:
            messages.error(request, 'Something went wrong, please try again.>!')
            return redirect('verify_otp')
    return render(request, 'main/verify_otp.html', {'email': change_email})

def resend_otp(request):
    if request.method == 'POST':
        generated_otp = random.randint(100000, 999999)
        email = request.session.get('user_email')
        request.session['registration_otp'] = generated_otp
        request.session.set_expiry(60 * 5)  
        subject = 'Registration OTP'
        message_body = f'Your regestration OTP for BookMyOT is  {generated_otp}'
        send_email(subject, message_body, email)
        messages.success(request, "OTP resent successfully. Enter the new OTP for verification.")
        return redirect('verify_otp')

    return render(request, 'main/verify_otp.html', {'email': email})

def authenticate_user(request):
    if request.method == 'POST':
        u_name = request.POST.get('Username')
        u_pwd = request.POST.get('Password')
        url = f'{domain_name.url}adminorHospitalLogin'
        data = {"inputdata": {"username": u_name, "password": u_pwd}}
        response = requests.post(url, json=data)
        res = response.json()

        if response.status_code == 200 and res.get('Status') and res['ResultData']['roleid'] == 3:
            user = res['ResultData']['username']
            request.session['username'] = user
            messages.success(request, 'Login successful..!')
            return redirect('home')

        message = res.get('Message', 'No Records Found')
    else:
        message = None

    return render(request, 'main/sign-in.html', {'mess': message})

# @session_required
def home(request):
    data = dashboard()
    return render(request, 'main/home.html', data)

# @session_required
def send_notification_to_all_physicians(request):
    send_notification_to_all_phys(request)
    return redirect('home')

# @session_required
def send_notification_to_all_hospitals(request):
    send_notification_to_all_hosp(request)
    return redirect('home')

# @session_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logout successfull..!')
    return redirect('admin_login')


from datetime import datetime
def generate_excel_content(columns, rows):
    # Create a DataFrame with the provided columns and rows
    df = pd.DataFrame(rows, columns=columns)

    # Create an in-memory Excel file
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return excel_buffer.read()


def download_excel(request):
    if 'excel_data' in request.session:
        # Retrieve Excel content from session
        excel_data = request.session['excel_data']
        file_name = request.session['file_name']

        # Prepare response for file download
        response = HttpResponse(excel_data, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={file_name}.xlsx'

        # Clear the session variable after download
        # del request.session['excel_data'], request.session['file_name']

        return response
    else:
        # Handle case where download is not yet ready
        return HttpResponse("Excel download is not yet ready. Please generate the data first.")
    



# Hospital functionality

def get_hos_dash_data(request):
    template_name = 'hospital/dashboard-hospital-list.html'
    dash_hos = get_dash_hospital_list(request)
    if dash_hos:  # Check if dash_hos is not empty
        # Assuming the keys of the first dictionary in the list represent column names
        original_columns = ['hospitalname', 'mobile', 'email', 'estdyear', 'city', 'address']

        # Mapping of original column names to new names
        column_mapping = {
            'hospitalname': 'Hospital Name',
            'mobile': 'Mobile',
            'email': 'Email',
            'estdyear': 'ESTD year',
            'city': 'City',
            'address': 'Address',
        }

        # Extract only the desired columns and their values
        filtered_data = [{column_mapping[key]: row[key] for key in original_columns} for row in dash_hos]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'hospitals_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []

    # Prepare context for rendering the template
    context = {
        'data': dash_hos,
        'columns': columns,
        'download_ready': True  # Flag to indicate that download is ready
    }
    return render(request, template_name, context)



# @session_required
def today_hospitals_list(request):
    data = get_Today_Register_Hospitals_List()
    print(data)
    context  = None
    if data:  # Check if data is not empty
        original_columns = ['hospitalname', 'email', 'mobile', 'estdyear', 'city', 'createdon', 'address']

        # Mapping of original column names to new names
        column_mapping = {
            'hospitalname': 'Hospital Name',
            'email': 'Email',
            'mobile': 'Mobile',
            'address': 'address',
            'estdyear': 'Estd Year',
            'city': 'city',
            'createdon': 'Created On',
            'address': 'Address',
        }

        # Extract only the desired columns and their values
        filtered_data = [{column_mapping[key]: row[key] for key in original_columns} for row in data]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'doctors_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []
    context = {
        'data' : data,
        'columns': columns,
        'download_ready': True,

    }
    return render(request, 'hospital/recent-registered-hopitals.html', context)
    
# # @session_required
def hospitals_list(request):
    template = 'hospital/hospital-list.html'
    if request.method == 'POST':
        data = hospital_filter_list(request)
        # Extract column names and rows from data
        if data:  # Check if data is not empty
            original_columns = ['hospitalname', 'mobile', 'email', 'estdyear', 'createdon', 'city', 'address']

            # Mapping of original column names to new names
            column_mapping = {
                'hospitalname': 'Doctor Name',
                'mobile': 'Mobile',
                'email': 'Email',
                'estdyear': 'ESTD Year',
                'createdon': 'Created On',
                'city': 'City',
                'address': 'Address',
            }

            # Extract only the desired columns and their values
            filtered_data = [{column_mapping[key]: row[key] for key in original_columns} for row in data]

            # Save the Excel content in the session
            request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
            request.session['file_name'] = 'doctors_data'

            # Set the columns and rows only if dash_hos is not empty
            columns = list(column_mapping.values())
            rows = filtered_data
        else:
            columns = []
            rows = []
        
            request.session['excel_data'] = generate_excel_content(columns, rows)
            request.session['file_name'] = 'hospitals_data'

        # Prepare context for rendering the template
        context = {
            'data': data,
            'columns': columns,
            'download_ready': True  # Flag to indicate that download is ready
        }

        return render(request, template, context)
    else:
        data = hospital(request)
        context = {
            'data': data['ResultData'],
            'download_ready': False  # Flag to indicate that download is not yet ready
        }
        return render(request, template, context)

# @session_required
def add_hospital(request):
    data = add_hospital_form(request)
    context = {
        'form' : data
    }
    return render(request, 'hospital/hospital_add.html', context)

# @session_required
def hospital_delete(request,id):
    delete_hospital(request, id)
    return redirect('hospitals_list', id)


# Edit Hospital

# @session_required
def hospital_profile_edit(request,id):
    data = hospital_edit_profile(request,id)
    return render(request, 'hospital/hospital-profile-edit.html', data)

# @session_required
def hospital_details_edit(request,id):
    data = hospital_edit_details(request,id)
    return render(request, 'hospital/hospital-details-edit.html', data)

# @session_required
def hospital_address_edit(request,id):
    data = hospital_edit_address(request,id)
    return render(request, 'hospital/hospital-address-edit.html', data)

# @session_required
def hospital_status_edit(request,id):
    data = hospital_edit_status(request,id)
    return render(request, 'hospital/hospital-status-edit.html', data)

# @session_required
def hospital_surgeons_edit(request,id):
    data = hospital_edit_surgeons(request,id)
    return render(request, 'hospital/hospital-surgeons-edit.html',data)

# @session_required
def hospital_add_surgeons(request,id):
    hospital_add_surgeon(request,id)
    return redirect('hospital_surgeons_edit', id)

def hospital_edit_surgeon_separately(request, id):
    hospital_edit_surgeon_separate(request, id)
    return render(request, 'hospital/hospital-surgeon-edit-separate.html')

# @session_required
def surgeon_edit(request,id):
    data = surgeonedit(request, id)
    return render(request, 'hospital/hospital-edit-particular-surgeon.html', data)

# @session_required
def hospital_surgeon_delete(request,id, hid):
    surgeon_delete(request, id, hid)
    return redirect('hospital_surgeons_edit', hid)

# @session_required
def hospital_equipment_edit(request,id):
    data = hospital_edit_equipment(request,id)
    return render(request, 'hospital/hospital-equipment-edit.html',data)

# @session_required
def hospital_add_equipment(request,id):
    hospital_equipment_add(request,id)
    return redirect('hospital_equipment_edit', id)

# @session_required
def hospital_equipment_delete(request,id, hid):
    equipment_delete(request, id, hid)
    return redirect('hospital_equipment_edit', hid)




# Hospital view

# @session_required
def hospital_profile_view(request, id):
    data = hospital_profile_view_get(request, id)
    return  render(request, 'hospital/hospital-profile-view.html', data)

# @session_required
def hospital_details_view(request, id):
    data = hospital_details_view_get(request, id)
    return  render(request, 'hospital/hospital-details-view.html', data)

# @session_required
def hospital_address_view(request, id):
    data = hospital_address_view_get(request, id)
    return  render(request, 'hospital/hospital-address-view.html', data)

# @session_required
def hospital_status_view(request, id):
    data = hospital_status_view_get(request, id)
    return  render(request, 'hospital/hospital-status-view.html', data)

# @session_required
def hospital_surgeon_view(request, id):
    data = hospital_surgeon_view_get(request, id)
    context = {
        'data' : data,'hosid':id
    }
    return  render(request, 'hospital/hospital-surgeon-view.html', context)

# @session_required
def hospital_equipment_view(request, id):
    data = hospital_equipment_view_get(request, id)
    context = {
        'data' : data,'hosid':id
    }
    return  render(request, 'hospital/hospital-equipment-view.html', context)

# @session_required
def hospital_transaction_view(request, id):
    data = hospital_transaction_view_get(request, id)
    context = {
        'data': data,'hosid': id
    }
    return  render(request, 'hospital/hospital-transaction-view.html', context)

# # @session_required
def hospital_near_by_physicians_view(request, id):
    data = hospital_near_physicians_view_get(request, id)
    context = {
        'data': data,
        'hosid':id,
    }
   
    return render(request, 'hospital/hospital-near-physicians-view.html', context)





# Doctors Functionality

def get_doc_dash_data(request):
    template_name = 'doctors/dashboard-doctor-list.html'
    dash_doc = get_dash_doctors_list(request)
    if dash_doc:  # Check if dash_doc is not empty
        original_columns = ['firstname', 'phone', 'emailid', 'experience', 'speciality', 'regno', 'address']

        # Mapping of original column names to new names
        column_mapping = {
            'firstname': 'Doctor Name',
            'phone': 'Mobile',
            'emailid': 'Email',
            'experience': 'Experience',
            'speciality': 'Speciality',
            'regno': 'Regno',
            'address': 'Address',
        }

        # Extract only the desired columns and their values
        filtered_data = [{column_mapping[key]: row[key] for key in original_columns} for row in dash_doc]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'doctors_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []

    # Prepare context for rendering the template
    context = {
        'data': dash_doc,
        'columns': columns,
        'download_ready': True  # Flag to indicate that download is ready
    }
    return render(request, template_name, context)

# @session_required
def today_doctors_list(request):
    data = get_Today_Register_Doctors_List()
    context = None
    if data:  # Check if data is not empty
        original_columns = ['firstname', 'phone', 'emailid', 'experience', 'speciality', 'regno', 'address']

        # Mapping of original column names to new names
        column_mapping = {
            'firstname': 'Doctor Name',
            'phone': 'Mobile',
            'emailid': 'Email',
            'experience': 'Experience',
            'speciality': 'Speciality',
            'regno': 'Regno',
            'address': 'Address',
        }

        # Extract only the desired columns and their values
        filtered_data = [{column_mapping[key]: row[key] for key in original_columns} for row in data]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'doctors_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []
    context = {
        'data': data, 
        'columns': columns,
        'download_ready': True,
    }

    return render(request, 'doctors/recent-registered-physicians.html', context)

# @session_required
def doctors_list(request):
    context = None
    if request.method == 'POST':
        data1, sub_api_data = doctors_filter_list(request)
        if data1:  # Check if data is not empty
            original_columns = ['firstname', 'phone', 'emailid', 'experience', 'speciality', 'regno', 'address']

            # Mapping of original column names to new names
            column_mapping = {
                'firstname': 'Doctor Name',
                'phone': 'Mobile',
                'emailid': 'Email',
                'experience': 'Experience',
                'speciality': 'Speciality',
                'regno': 'Regno',
                'address': 'Address',
            }

            # Extract only the desired columns and their values
            filtered_data = [{column_mapping[key]: row[key] for key in original_columns} for row in data1]

            # Save the Excel content in the session
            request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
            request.session['file_name'] = 'doctors_data'

            # Set the columns and rows only if dash_hos is not empty
            columns = list(column_mapping.values())
            rows = filtered_data
        else:
            columns = []
            rows = []

        # Prepare context for rendering the template
        context = {
            'data': data1,
            'columns': columns,
            'download_ready': True,  # Flag to indicate that download is ready
            'sub_api_data': sub_api_data,
        }
        
        return render(request, 'doctors/doctors-list.html', context)
    else:
        data, sub_api_data = get_All_Doctors_List()
        context = {
            'data': data,
            'sub_api_data': sub_api_data,  # Include Sub_Api data in the context
        }
        return render(request, 'doctors/doctors-list.html', context)

# @session_required
def doctors_delete(request, id):
    doctors_deletebtn(request, id)
    return redirect('doctors')

# @session_required
def doctor_send_notification(request):
    if request.method == 'POST':
        doc_send_noti(request)
    return redirect('doctors')

# # @session_required
def doctor_insert_subscription(request):
    if request.method == 'POST':
        doc_insert_subscription(request)
    return redirect('doctors')

# @session_required
def docter_edit_btn(request,id):
    data = doctors_profile_edit(request, id)
    return render(request, 'doctors/doctors-profile.html', data)

# @session_required
def doctots_edit_address(request, id):
    data = doctors_address_edit(request, id)
    return render(request, 'doctors/doctors-address.html', data)

# @session_required
def doctors_edit_kyc(request, id):
    data = doctors_kyc(request, id)
    return render(request, 'doctors/doctors-kyc.html', data)

# @session_required
def doctors_edit_bank_details(request, id):
    data = doctors_bank_details(request, id)
    return render(request, 'doctors/doctors-bank.html', data)

# @session_required
def doctors_edit_education_details(request, id):
    data = doctors_education_details(request, id)
    return render(request, 'doctors/doctors-education.html', data)

# @session_required
def doctors_edit_social_media(request, id):
    data = doctors_social_media(request, id)
    return render(request, 'doctors/doctors-social-media.html', data)

# @session_required
def doctors_edit_professional_info(request, id):
    data = doctors_professional_info(request, id)
    return render(request, 'doctors/doctors-professional-info.html', data)

# @session_required
def doctors_edit_trasanctions(request, id):
    data = doctors_trasanctions(request, id)
    download_url =requests.get(f'{domain_name.url}PhysicianTransactionPDF?pnum={id}').json()
    down = download_url['ResultData']
    context =  {
        'transactions':data,
        "pnum":id,
        "down": down,
        }
    return render(request, 'doctors/doctors-transaction.html', context)

# # @session_required
def doctors_edit_verify(request, id):
    data = doctors_verify(request, id)
    return render(request, 'doctors/doctors-verify.html', data)

def phyisacode_verify(request, id):
    if request.method == 'POST':
        isacode = request.POST.get('isacode')
        url = f'{domain_name.url}checkisacodes'
        data = {"code":isacode}
        result = requests.post(url, json = data).json()
        if result['ResultData'][0]['status'] == 0:
            messages.error(request, 'ISA Code not avilable in records..!')
        else:
            messages.success(request, 'ISA Code avilable in records..!')

    return redirect('doctors_edit_verify', id)

# Doctors view

# @session_required
def doctors_view(request, id):
    data = doctor_view_get(request, id)
    return render(request, 'doctors/doctors-profile-view.html', data)

# @session_required
def doctors_view_address(request, id):
    data = doctor_address_view_get(request, id)
    return render(request, 'doctors/doctors-address-view.html', data)

# @session_required
def doctors_view_kyc(request, id):
    data = doctor_kyc_view_get(request, id)
    return render(request, 'doctors/doctors-kyc-view.html', data)

# @session_required
def doctors_view_education(request, id):
    data = doctor_education_view_get(request, id)
    return render(request, 'doctors/doctors-education-view.html', data)

# @session_required
def doctors_view_documents(request, id):
    data = doctor_documents_view_get(request, id)
    context = {
        'education_result': data.get('education_result', None),
        'registration_result': data.get('registration_result', None),
        'pnum': id
    }
    return render(request, 'doctors/doctors-view-documents.html', context)

# @session_required
def doctors_view_personal_info(request, id):
    data = doctor_personal_info_view_get(request, id)
    return render(request, 'doctors/doctors-professional-view.html', data)

# @session_required
def doctors_view_bank(request, id):
    data = doctor_bank_details_view_get(request, id)
    return render(request, 'doctors/doctors-bank-details-view.html', data)

# @session_required
def doctors_view_transaction(request, id):
    data = doctor_transaction_view_get(request, id)
    result =  {'transactions':data,"pnum":id}
    return render(request, 'doctors/doctors-transactions-view.html', result)

# @session_required
def doctors_view_media(request, id):
    data = doctor_social_media_view_get(request, id)
    return render(request, 'doctors/doctors-social-media-view.html', data)

# @session_required
def doctors_view_verification(request, id):
    data = doctor_verification_view_get(request, id)
    return render(request, 'doctors/doctors-verification-view.html', data)

# @session_required
def doctors_view_awards(request, id):
    data = doctor_verification_view_get(request, id)
    return render(request, 'doctors/doctors-kyc-view.html', data)

# @session_required
def doctors_view_near_hospitals(request, id):
    data = doctor_near_hospitals_view_get(request, id)
    context = {
        'data': data,
        'pnum':id,
    }
    return render(request, 'doctors/doctors-near-hospitals-view.html', context)

# @session_required
def doctors_view_subscriptions(request, id):
    data = doctor_subscriptions_view_get(request, id)
    context = {
        'data': data,
        'pnum':id,
    }
    return render(request, 'doctors/doctors-view-subscriptions.html', context)








# Surgeries functionality

def get_surgeries_dash_data(request):
    template_name = 'surgeries/dashboard-surgeries-list.html'
    dash_surgery = get_dash_surgeries_list(request)
    if dash_surgery:  # Check if dash_surgery is not empty
        # Assuming the keys of the first dictionary in the list represent column names
        original_columns = ['casename', 'createdon', 'surgerydate', 'patientdiagnostics', 'hospitalname', 'patientname', 'physicianname', 'surgonname', 'status']

        # Mapping of original column names to new names
        column_mapping = {
            'casename': 'Case Name',
            'createdon': 'Created On',
            'surgerydate': 'Surgery date',
            'patientdiagnostics': 'Diagnostics',
            'hospitalname': 'Hospital Name',
            'patientname': 'Patient Name',
            'physicianname': 'Physician Name',
            'surgonname': 'Surgeon Name',
            'status': 'Status',
        }
        status_mapping = {
            0: 'New',
            1: 'Not Assigned',
            2: 'Confirmed',
            3: 'In Progress',
            4: 'In Review',
            5: 'Completed',
            6: 'Canceled',
        }

        # Extract only the desired columns and their values
        filtered_data = [
            {column_mapping[key]: status_mapping.get(row[key], row[key]) if key == 'status' else row[key] for key in original_columns}
            for row in dash_surgery
        ]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'surgeriess_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []

    # Prepare context for rendering the template
    context = {
        'data': dash_surgery,
        'columns': columns,
        'download_ready': True  # Flag to indicate that download is ready
    }
    return render(request, template_name, context)


# @session_required
def surgeries_list(request):
    if request.method == 'POST':
        data1 = surgeries_filter_list(request)
        if data1:  # Check if data is not empty
            original_columns = ['casename', 'createdon', 'surgerydate', 'patientdiagnostics', 'hospitalname', 'patientname', 'physicianname', 'surgonname', 'status']

            # Mapping of original column names to new names
            column_mapping = {
                'casename': 'Case Name',
                'createdon': 'Created On',
                'surgerydate': 'Surgery date',
                'patientdiagnostics': 'Diagnostics',
                'hospitalname': 'Hospital Name',
                'patientname': 'Patient Name',
                'physicianname': 'Physician Name',
                'surgonname': 'Surgeon Name',
                'status': 'Status',
            }
            status_mapping = {
                0: 'New',
                1: 'Not Assigned',
                2: 'Confirmed',
                3: 'In Progress',
                4: 'In Review',
                5: 'Completed',
                6: 'Canceled',
            }

            # Extract only the desired columns and their values
            filtered_data = [
                {column_mapping[key]: status_mapping.get(row[key], row[key]) if key == 'status' else row[key] for key in original_columns}
                for row in data1
            ]

            # Save the Excel content in the session
            request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
            request.session['file_name'] = 'surgeries_data'

            # Set the columns and rows only if dash_hos is not empty
            columns = list(column_mapping.values())
            rows = filtered_data
        else:
            columns = []
            rows = []
        context = {
            'data': data1, 
            'columns': columns,
            'download_ready': True,
        }
        return render(request, 'surgeries/surgeries-list.html', context)
    else:
        data = get_surgeries()
        context = {
            'data': data,
        }
        return render(request, 'surgeries/surgeries-list.html', context)

def surgeries_dash_status(request, status):
    template_name = 'surgeries/status-surgeries-dashboard.html'
    data = get_status_surgeries_dash(request, status)
    if data:  # Check if data is not empty
        original_columns = ['casename', 'createdon', 'surgerydate', 'patientdiagnostics', 'hospitalname', 'patientname', 'physicianname', 'surgonname', 'status']

        # Mapping of original column names to new names
        column_mapping = {
            'casename': 'Case Name',
            'createdon': 'Created On',
            'surgerydate': 'Surgery date',
            'patientdiagnostics': 'Diagnostics',
            'hospitalname': 'Hospital Name',
            'patientname': 'Patient Name',
            'physicianname': 'Physician Name',
            'surgonname': 'Surgeon Name',
            'status': 'Status',
        }
        status_mapping = {
            0: 'New',
            1: 'Not Assigned',
            2: 'Confirmed',
            3: 'In Progress',
            4: 'In Review',
            5: 'Completed',
            6: 'Canceled',
        }

        # Extract only the desired columns and their values
        filtered_data = [
            {column_mapping[key]: status_mapping.get(row[key], row[key]) if key == 'status' else row[key] for key in original_columns}
            for row in data
        ]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'surgeries_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []
    context = {
        'data': data, 
        'columns': columns,
        'download_ready': True,
    }
    return render(request, template_name, context)
   

# @session_required
def surgeries_edit_btn(request, id):
    data = surgery_details_edit(request, id)
    return render(request, 'surgeries/surgery-details-edit.html', data)

# @session_required
def surgery_physician_notes_edit(request, id):
    data, pay_data = physician_notes_edit(request, id)
    context = {
        'data' : data,
        'pay_data' : pay_data,
        'document_link': data['documentpath'],
    }
    return render(request, 'surgeries/surgery-physician-notes-edit.html', context)

# @session_required
def surgery_patient_diagnostics_edit(request, id):
    data = patient_diagnostics_edit(request, id)
    return render(request, 'surgeries/surgery-patient-diagnostics-edit.html', data)



# Duties functionality

def duties_dash_status(request, type):
    template_name = 'duties/status-duties-dashboard.html'
    data = get_status_duties_dash(request, type)
    if data:
        # Specify the columns you want to include in the output
        original_columns = ['dutyid', 'dutynum', 'physicianname', 'appdate', 'starttime', 'endtime', 'price', 'status']

        # Mapping of original column names to new names
        column_mapping = {
            'dutyid': 'Duty ID',
            'dutynum': 'Duty Number',
            'physicianname': 'Physician Name',
            'appdate': 'Appointment Date',
            'starttime': 'Start Time',
            'endtime': 'End Time',
            'price': 'Price',
            'status': 'Status',
        }
        status_mapping = {
            1: 'New',
            2: 'Confirmed',
            3: 'In progress',
            4: 'In progress',
            5: 'In progress',
            6: 'Reviewed',
            7: 'Completed',
            8: 'Canceled',
        }

        # Extract only the desired columns and their values
        filtered_data = [{column_mapping[key]: status_mapping.get(row[key], row[key]) if key == 'status' else row[key] for key in original_columns} for row in data]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'duties_data'

        # Prepare context for rendering the template
        context = {
            'data': data,
            'columns': list(column_mapping.values()),
            'download_ready': True  # Flag to indicate that download is ready
        }
        return render(request, template_name, context)
    else:
        columns = []
        rows = []

    # Prepare context for rendering the template
    context = {
        'data': data,
        'columns': columns,
        'download_ready': True  # Flag to indicate that download is ready
    }
    return render(request, template_name, context)


def get_duties_dash_data(request):
    template_name = 'duties/dashboard-duties-list.html'
    dash_duties = get_dash_duties_list(request)
    if dash_duties:  # Check if dash_duties is not empty
        original_columns = ['physicianname', 'starttime', 'endtime', 'phystarttime', 'phyendtime', 'price', 'apptype', 'status']

        # Mapping of original column names to new names
        column_mapping = {
            'physicianname': 'Physician Name',
            'starttime': 'Duty Starttime',
            'endtime': 'Duty Endtime',
            'phystarttime': 'Phy Starttime',
            'phyendtime': 'Phy Endtime',
            'price': 'Price',
            'apptype': 'Duty Type',
            'status': 'Status',
        }

        apptype_mapping = {
            1: 'CODEBLUE',
            2: 'NIGHTDUTYCALL',
            3: 'ICUDUTYCALL',
            4: 'DAYDUTYCALL',
            5: 'OTDUTYCALL',
            6: 'ICUOTCALL',
        }

        status_mapping = {
            1: 'New',
            2: 'Confirmed',
            3: 'In Progress',
            4: 'In Progress',
            5: 'In Progress',
            6: 'Reviewed',
            7: 'Completed',
            8: 'Canceled',
        }

        # Extract only the desired columns and their values
        filtered_data = [
            {
                column_mapping[key]: status_mapping.get(row[key], row[key]) if key == 'status' else
                apptype_mapping.get(row[key], row[key]) if key == 'apptype' else row[key]
                for key in original_columns
            }
            for row in dash_duties
        ]

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
        request.session['file_name'] = 'duties_data'

        # Set the columns and rows only if dash_hos is not empty
        columns = list(column_mapping.values())
        rows = filtered_data
    else:
        columns = []
        rows = []

    # Prepare context for rendering the template
    context = {
        'data': dash_duties,
        'columns': columns,
        'download_ready': True  # Flag to indicate that download is ready
    }
    return render(request, template_name, context)


# @session_required
def duties_list(request):
    context = None
    if request.method == 'POST':
        data1 = duties_filter_list(request)
        if data1:  # Check if data1 is not empty
            original_columns = ['physicianname', 'starttime', 'endtime', 'phystarttime', 'phyendtime', 'price', 'apptype', 'status']

            # Mapping of original column names to new names
            column_mapping = {
                'physicianname': 'Physician Name',
                'starttime': 'Duty Starttime',
                'endtime': 'Duty Endtime',
                'phystarttime': 'Phy Starttime',
                'phyendtime': 'Phy Endtime',
                'price': 'Price',
                'apptype': 'Duty Type',
                'status': 'Status',
            }

            apptype_mapping = {
                1: 'CODEBLUE',
                2: 'NIGHTDUTYCALL',
                3: 'ICUDUTYCALL',
                4: 'DAYDUTYCALL',
                5: 'OTDUTYCALL',
                6: 'ICUOTCALL',
            }

            status_mapping = {
                1: 'New',
                2: 'Confirmed',
                3: 'In Progress',
                4: 'In Progress',
                5: 'In Progress',
                6: 'Reviewed',
                7: 'Completed',
                8: 'Canceled',
            }

            # Extract only the desired columns and their values
            filtered_data = [
                {
                    column_mapping[key]: status_mapping.get(row[key], row[key]) if key == 'status' else
                    apptype_mapping.get(row[key], row[key]) if key == 'apptype' else row[key]
                    for key in original_columns
                }
                for row in data1
            ]

            # Save the Excel content in the session
            request.session['excel_data'] = generate_excel_content(list(column_mapping.values()), filtered_data)
            request.session['file_name'] = 'duties_data'

            # Set the columns and rows only if dash_hos is not empty
            columns = list(column_mapping.values())
            rows = filtered_data
            context = {
                'data': data1,
                'columns': columns,
                'download_ready': True 
            }
            return render(request, 'duties/duties-list.html', context)
      
    else:
        data = duties_list_get(request)
        context = {
            'data': data,
        }
    return render(request, 'duties/duties-list.html', context)





# Configs

# @session_required
def config_speciality_list(request):
    data = config_speciality_get()
    if request.method == 'POST':
        data = config_post_specialist(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-speciality-list.html', context)

# @session_required
def config_add_speciality(request):
    add_speciality_form(request)
    return redirect('config_speciality_list')

# @session_required
def config_speciality_delete(request, id):
    config_speciality_deletebtn(request, id)
    return redirect('config_speciality_list')

# @session_required
def config_surgery_list(request):
    data = config_surgery_get()
    if request.method == 'POST':
        data = config_post_surgery(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-surgery-list.html', context)

# @session_required
def config_add_surgery(request):
    add_surgery_form(request)
    return redirect('config_surgery_list')

# @session_required
def config_surgery_delete(request, id):
    config_surgery_deletebtn(request, id)
    return redirect('config_surgery_list')

# @session_required
def config_anetsthesia_list(request):
    data = config_anetsthesia_get()
    if request.method == 'POST':
        data = config_post_anesthesia(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-anesthesia-list.html', context)

# @session_required
def config_add_anesthesia(request):
    add_anesthesia_form(request)
    return redirect('config_anetsthesia_list')

# @session_required
def config_anesthesia_delete(request, id):
    config_anesthesia_deletebtn(request, id)
    return redirect('config_anetsthesia_list')

# @session_required
def config_pre_existing_conditions_list(request):
    data = config_pre_existing_get()
    if request.method == 'POST':
        data = config_post_config_pre_Existing(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-pre-existing.html', context)

# @session_required
def config_add_pre_existing_condition(request):
    add_pre_existing_condition_form(request)
    return redirect('config_pre_existing_conditions_list')

# @session_required
def config_pre_existing_condition_delete(request, id):
    config_pre_existing_condition_deletebtn(request, id)
    return redirect('config_pre_existing_conditions_list')

# @session_required
def config_ot_equipment_list(request):
    data = config_ot_equpiment_get()
    if request.method == 'POST':
        data = config_post_equipment_list(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-ot-equipment-list.html', context)

# @session_required
def config_add_equipment(request):
    add_equipment_form(request)
    return redirect('config_ot_equipment_list')

# @session_required
def config_equipment_delete(request, id):
    config_equipment_deletebtn(request, id)
    return redirect('config_ot_equipment_list')

# @session_required
def config_app_notification(request):
    data = config_noti_get()
    if request.method == 'POST':
        config_noti_post(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-app-notification.html', context)

# @session_required
def config_images(request):
    data = config_images_get()
    if request.method == 'POST':
        config_images_add_form(request)
        
    # context = {
    #     'data' : data['ResultData'],
    # }
    return render(request, 'config/config-images.html', data)

def config_image_delete(request, id):
    config_image_deletebtn(request, id)
    return redirect('config_images')

# @session_required
def config_app_settings(request):
    data = config_settings_get()
    if request.method == 'POST':
        data = config_settings_post(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-app-settings.html', context)






# FAQ'S

# # @session_required
def get_faq_category(request):
    template_name = 'faqs/get-faq-categories.html'
    # get_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=0').json()
    get_phy_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=1').json()
    get_hos_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=2').json()
    context = {
        # 'data': get_api['ResultData'],
        'hos_data': get_hos_api['ResultData'],
        'phy_data': get_phy_api['ResultData'],
    }
    return render(request, template_name, context)

# # @session_required
def admin_add_faq_category_type(request):
    add_faq_cat_api = (f'{domain_name.url}insertAndUpdateFaqscategory')
    if request.method == 'POST':
        name = request.POST.get('faqCatName')
        cattype = request.POST.get('cattype')
        data = {
            "faqsategoryid": 0,
            "name": name,
            "categorytype": cattype
        }
        a = requests.post(add_faq_cat_api, json = data)
        messages.success(request, 'Faq Category added successfully.')

        return redirect('get_faq_category')

# # @session_required
def admin_edit_faq_category(request):
    if request.method == 'POST':
        faqid = request.POST.get('hdnSettingsId')
        catid = request.POST.get('hdnCatTypeId')
        name = request.POST.get('settingsName')
        data = {
            "faqsategoryid":faqid,
            "name":name,
            "categorytype":catid
        }
        url = (f'{domain_name.url}insertAndUpdateFaqscategory')
        a = requests.post(url, json = data)
        messages.success(request, 'Category edited successfully..')
        return redirect('get_faq_category')
    return redirect('get_faq_category')

# # @session_required
def faq_category_delete(request, id):
    url =(f'{domain_name.url}deletefaqsategory')
    xyz = {
        "faqsategoryid": id
    }
    result = requests.post(url, json = xyz)
    result_json = result.json()
    if result_json['Status'] == True:
        messages.success(request, 'Category deleted successfully...!')
    else:
        messages.error(request, 'Try Again SomethingWent Wrong..!')
    return redirect('get_faq_category')

# # @session_required
def get_category_faqs(request):
    template_name = 'faqs/get-category-faqs.html'
    get_cat_types_phy_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=1').json()
    get_cat_types_hos_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=2').json()
    faq_cat_phy_api = requests.get(f'{domain_name.url}/FAQS?questionstype=1&faqscategoryid=0').json()
    faq_cat_hos_api = requests.get(f'{domain_name.url}/FAQS?questionstype=2&faqscategoryid=0').json()
    context = {
        'phy_cattypes': get_cat_types_phy_api['ResultData'],
        'hos_cattypes': get_cat_types_hos_api['ResultData'],
        'phy_faqs': faq_cat_phy_api['ResultData'],
        'hos_faqs': faq_cat_hos_api['ResultData'],
    }
    return render(request, template_name, context)

# # @session_required
def add_category_faq(request):
    if request.method == "POST":
        cattypefor = request.POST.get('cattypefor')
        cattype = request.POST.get('cattype')
        faqQuestion = request.POST.get('faqQuestion')
        faqAnswer = request.POST.get('faqAnswer')
        cleaned_answer = faqAnswer.replace('"', '').replace("'", '')
        cleaned_question = faqQuestion.replace('"', '').replace("'", '')

        data = {
            "id": 0,
            "questions": cleaned_question,
            "answers": cleaned_answer,
            "questionstype": cattypefor,
            "category": cattype
        }

        url = (f'{domain_name.url}insertAndUpdateFAQS')
        a = requests.post(url, json = data)

        messages.success(request, 'Faq added successfully.')
    return redirect('get_category_faqs')

# # @session_required
def admin_edit_category_faq(request):
    if request.method == 'POST':
        faqid = request.POST.get('hdnFaqId')
        catid = request.POST.get('hdnFaqcatId')
        qtype = request.POST.get('Qtype')
        question = request.POST.get('faqQuestion')
        answer = request.POST.get('faqAnswer')
        cleaned_answer = answer.replace('"', '').replace("'", '')
        cleaned_question = question.replace('"', '').replace("'", '')
        data = {
            "id": faqid,
            "questions": cleaned_question,
            "answers": cleaned_answer,
            "questionstype": qtype,
            "category": catid
        }
        url = (f'{domain_name.url}insertAndUpdateFAQS')
        a = requests.post(url, json = data)
        messages.success(request, 'Faq edited successfully..')
        return redirect('get_category_faqs')
    return redirect('get_category_faqs')

# # @session_required
def category_faq_delete(request, id):
    url =(f'{domain_name.url}deleteFAQS')
    xyz = {
        "id": id
    }
    result = requests.post(url, json = xyz)
    result_json = result.json()

    if result_json['Status'] == True:
        messages.success(request, 'Faq deleted successfully...!')
    else:
        messages.error(request, 'Try Again SomethingWent Wrong..!')
    return redirect('get_category_faqs')

# # @session_required
def admin_get_all_submission_faqs(request):
    template_name = 'faqs/admin-view-all-faqs-sumitions.html'
    # get_all_submited_faqs = requests.get(f'{domain_name.url}getAllSubmisionQuary').json()
    get_all_phy_submited_faqs = requests.get(f'{domain_name.url}getAllSubmisionQuary?type=1').json()
    get_all_hos_submited_faqs = requests.get(f'{domain_name.url}getAllSubmisionQuary?type=2').json()
    phy_result_data = get_all_phy_submited_faqs.get("ResultData", [])
    hos_result_data = get_all_hos_submited_faqs.get("ResultData", [])

    # Initialize counters
    phy_is_addressed_true_count = 0
    phy_is_addressed_false_count = 0
    phy_total_count = 0
    for item in phy_result_data:
        phy_total_count += 1
        if item.get("isaddressed"):
            phy_is_addressed_true_count += 1
        else:
            phy_is_addressed_false_count += 1

    hos_is_addressed_true_count = 0
    hos_is_addressed_false_count = 0
    hos_total_count = 0
    for item in hos_result_data:
        hos_total_count += 1
        if item.get("isaddressed"):
            hos_is_addressed_true_count += 1
        else:
            hos_is_addressed_false_count += 1
    context = {
        'phy_faqs': get_all_phy_submited_faqs['ResultData'],
        'hos_faqs': get_all_hos_submited_faqs['ResultData'],
        'phy_total_queries_count': phy_total_count,
        'phy_solved_queries_count': phy_is_addressed_true_count,
        'phy_unsolved_queries_count': phy_is_addressed_false_count,
        'hos_total_queries_count': hos_total_count,
        'hos_solved_queries_count': hos_is_addressed_true_count,
        'hos_unsolved_queries_count': hos_is_addressed_false_count,
    }
    return render(request, template_name, context)

# # @session_required
def admin_view_faq(request, id):
    template_name = 'faqs/admin-view-faq.html'
    get_view_faq_api = requests.get(f'{domain_name.url}getQuarySubmitedFullDetailsByid?raisedticketsid={id}').json()
    context = {
        'faq_1': get_view_faq_api['ResultData'][0],
        'faq': get_view_faq_api['ResultData'],
    }
    if request.method == 'POST':
        message = request.POST.get('message')
        cleaned_message = message.replace('"', '').replace("'", '')
        data = {
            "raisedticketsid": id,
            "sendertype": 2,
            "issue": cleaned_message
        }
        url = f'{domain_name.url}QuarySubmisionSendMessage'
        response = requests.post(url, json=data)
        if response.status_code == 200:
            # Assuming your API returns the updated FAQ data after sending the message
            updated_data = response.json().get('ResultData', {})
            context ={
                'faq_1': get_view_faq_api['ResultData'][0],
                'faq': updated_data,
            }
            return redirect('admin_view_faq', id)
        else:
            pass

    return render(request, template_name, context)

# # @session_required
def close_ticket(request, id):
    data = {
        "raisedticketsid": id
    }
    url = f'{domain_name.url}CloseQuarySubmision'
    a = requests.post(url, json=data) 
    messages.success(request, 'Ticket was closed successfully.')
    return redirect('admin_view_faq', id)



# faq's hospital

def hospital_get_faqs(request):
    template_name = 'faqs/hospital-get-faqs.html'
    get_categories_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=2').json()
    
    context = {
        'cat_types': get_categories_api['ResultData'],
    }
    return render(request, template_name, context)


def get_hos_cat_faqs(request, id):
    template_name = 'faqs/hospital-get-faqs.html'
    get_cat_faqs = requests.get(f'{domain_name.url}FAQS?questionstype=2&faqscategoryid={id}').json()
    get_categories_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype=2').json()
    context = {
        'faqs': get_cat_faqs['ResultData'],
        'cat_types': get_categories_api['ResultData']
    }
    return render(request, template_name, context)

def submit_faq(request, id, type):
    get_categories_api = requests.get(f'{domain_name.url}getfaqscategory?categorytype={type}').json()
    context = {
        'cat_types': get_categories_api['ResultData']
    }
    if request.method == 'POST':
        faqcatid = request.POST.get('faqcatid')
        message = request.POST.get('message')
        data = {
            "type": type,
            "typeid": id,
            "faqscategoryid": faqcatid,
            "message": message
        }
        url = (f'{domain_name.url}QuarySubmision')
        requests.post(url, json = data)
        context = {
        'cat_types': get_categories_api['ResultData']
        }
        messages.success(request, 'Your Query was submitted successfully. We will contact you soon.')
    return render(request, 'faqs/submit-query.html', context)

def hospital_get_submited_tickets(request, hnum):
    get_raised_tickets_api = requests.get(f'{domain_name.url}getAllHospitalSubmisionQuarys?hnum={hnum}').json()
    context = {
        'tickets_list': get_raised_tickets_api['ResultData'],
    }
    return render(request, 'faqs/hospital-view-submited-tickets.html', context)

def hospital_view_ticket(request, id):
    template_name = 'faqs/hospital-view-ticket.html'
    get_view_faq_api = requests.get(f'{domain_name.url}getQuarySubmitedFullDetailsByid?raisedticketsid={id}').json()
    context = {
        'faq_1': get_view_faq_api['ResultData'][0],
        'faq': get_view_faq_api['ResultData'],
    }

    if request.method == 'POST':
        message = request.POST.get('message')
        cleaned_message = message.replace('"', '').replace("'", '')
        data = {
            "raisedticketsid": id,
            "sendertype": 1,
            "issue": cleaned_message
        }
        url = f'{domain_name.url}QuarySubmisionSendMessage'
        response = requests.post(url, json=data)
        if response.status_code == 200:
            # Assuming your API returns the updated FAQ data after sending the message
            updated_data = response.json().get('ResultData', {})
            context ={
                'faq': updated_data
            }
            return redirect('hospital_view_ticket', id)
        else:
            pass

    return render(request, template_name, context)

def config_subscriptions(request):
    data = config_subscripotions_get(request)
    if request.method == 'POST':
        data = config_edit_subscription(request)
    context = {
        'data' : data,
    }
    return render(request, 'config/config-subscriptions.html', context)

def config_add_subscription(request):
    config_subscripotion_add(request)
    return redirect('config_subscriptions')

def config_delete_subscription(request, id):
    config_subscription_delete(request, id)
    return redirect('config_subscriptions')