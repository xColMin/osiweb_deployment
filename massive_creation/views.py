from django.shortcuts import render
from .forms import UploadFileForm
from .models import Mc
import os
import pandas as pd
from django.conf import settings
from django.http import HttpResponse, Http404


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        for file in request.FILES.getlist('file'):
            mc = Mc.objects.create(document=file)
            mc.save()

        os.chdir(settings.MEDIA_ROOT)

        for file in os.listdir():

            if 'Plantilla' in file and 'lock' not in file and 'Massive Creation' not in file:
                template_name = str(file)
                full_name = template_name[:-5]

                # Merge all sheets into one
                df_template = pd.DataFrame()
                excel_file = pd.ExcelFile(template_name)
                sheets = excel_file.sheet_names
                for sheet in sheets:
                    df = excel_file.parse(sheet_name=sheet)
                    df_template = df_template.append(df)

        df_total = pd.DataFrame()

        for file in os.listdir():

            if ('Barrido' in file or 'barrido' in file) and (
                    'xlsx' in file or 'xls' in file) and 'lock' not in file:
                export_name = str(file)
                export_full_name = export_name[:-5]

                # Merge all sheets into one
                excel_file = pd.ExcelFile(export_name)
                sheets = excel_file.sheet_names
                for sheet in sheets:
                    if sheet == 'Heat' or sheet == 'Water':
                        df = excel_file.parse(sheet_name=sheet)
                        df_total = df_total.append(df)

        df_template.drop(labels=['MANUFACTURER', 'VERSION'], axis=1, inplace=True)
        df_total = df_total[['Numero de serie del módullo', 'Fabricante', 'Version']]
        df_total.rename(
            columns={'Numero de serie del módullo': 'Meter ID', 'Fabricante': 'MANUFACTURER', 'Version': 'VERSION'},
            inplace=True)

        df_template = df_template.merge(df_total, on='Meter ID')

        df_template = df_template[
            ['Building', 'Postal Code', 'LOCATION', 'TENANT NAME (TREE)', 'METER NAME', 'TENANT NAME',
             'Country Tenant (Billing)', 'Energy', 'Building Entity', 'Meter ID',
             'SMC ID', 'MANUFACTURER',
             'VERSION', 'DEVICE', 'NOTE', 'AESKEY', 'TRACK ALARMS']]

        try:
            df_template['TENANT NAME'] = df_template['TENANT NAME'].apply(lambda x: x.replace(',', ''))
        except:
            pass

        df_template['METER NAME'] = df_template['METER NAME'].apply(lambda x: x.replace('\n', ''))
        df_template['METER NAME'] = df_template['METER NAME'].apply(lambda x: x.replace('"', ''))

        def energy_check(x):

            if x == 'WarmWater' or x == 'Agua caliente':
                return 'Agua Caliente'
            elif x == 'Agua':
                return 'Agua Fria'
            elif x == 'Energía' or x == 'Energia':
                return 'Calefacción'
            elif x == 'HCA':
                return 'HCA'
            else:
                return x

        df_template['Energy'] = df_template['Energy'].apply(lambda x: energy_check(x))
        df_template['VERSION'] = df_template['VERSION'].apply(lambda x: int(x))
        df_template['AESKEY'] = df_template['AESKEY'].apply(lambda x: df_template['AESKEY'][0])
        df_template['TRACK ALARMS'] = df_template['TRACK ALARMS'].apply(lambda x: df_template['TRACK ALARMS'][0])

        for y in df_template.columns:
            try:
                df_template[y] = df_template[y].apply(lambda x: x.replace('  ', ' '))
                df_template[y] = df_template[y].str.rstrip()
                df_template[y] = df_template[y].str.lstrip()
            except:
                pass

        df_template.to_csv('Massive Creation ' + full_name + '.csv', sep=';', index=False)

        file_path = os.path.join(settings.MEDIA_ROOT, 'Massive Creation ' + full_name + '.csv')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                for file in os.listdir():
                    os.remove(file)
                return response

    else:
        form = UploadFileForm()
        return render(request, 'massive_creation/mc.html', {'form': form})

