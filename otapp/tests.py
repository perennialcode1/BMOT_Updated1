from django.test import TestCase

# Create your tests here.
def hospitals_list(request):
    template = 'hospital/hospital-list.html'

    if request.method == 'POST':
        data = hospital_filter_list(request)
        print(data)

        # Extract column names and rows from data
        if data:  # Check if data is not empty
            # Assuming the keys of the first dictionary in the list represent column names
            columns = list(data[0].keys())
            rows = [list(row.values()) for row in data]
        else:
            columns = []
            rows = []

        print(columns)
        print(rows)

        # Save the Excel content in the session
        request.session['excel_data'] = generate_excel_content(columns, rows)
        request.session['file_name'] = 'surgeries_data'
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


{% if download_ready %}
    <a href="{% url 'download_excel' %}" class='btn btn-light-info'> <i class="fa-solid fa-download fs-3 fw-bold"></i></a>
{% endif %}