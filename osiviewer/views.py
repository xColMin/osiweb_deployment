from django.shortcuts import render, redirect
from .forms import UploadFileForm
from .models import Ov
import os
import pandas as pd
import re
import json
from .building import Building
from .bulding_functions import merge_sniffers
from zipfile import ZipFile
from django.conf import settings
from django.urls import reverse_lazy
from django.http import HttpResponse, Http404, HttpResponseRedirect


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        for file in request.FILES.getlist('file'):
            ov = Ov.objects.create(document=file)
            ov.save()

        os.chdir(settings.MEDIA_ROOT)

        files = os.listdir()
        df_total = pd.DataFrame()
        export_name = ''

        for file in files:

            # Open 'Plantilla File'
            if 'Plantilla' in file and 'lock' not in file and 'Columns' not in file:
                export_name = str(file)

                # Check for multiple sheets
                excel_file = pd.ExcelFile(export_name)
                sheets = excel_file.sheet_names

                # Merge all sheets into one
                if len(sheets) > 1:
                    for sheet in sheets:
                        df = excel_file.parse(sheet_name=sheet)
                        df_total = df_total.append(df)
                else:
                    df_total = pd.read_excel(export_name)

        final_df = pd.DataFrame()

        final_df['Building'] = df_total['Building']
        final_df['METER NAME'] = df_total['METER NAME']

        def format_meter_name(s):

            if 'BAJO' in s:
                s = s.replace('BAJO', '0º')

            if 'SUB' in s:
                r = r'SUB\s*'
                s = re.sub(r, '-', s)

            if 'º' not in s:
                try:
                    r = r'\d+'
                    i = re.findall(r, s)
                    s = s[0: int(s.index(i[0])) + 1] + 'º' + s[int(s.index(i[0])) + 1: -1]
                except:
                    print('WARNING! Found weird METER NAME:')
                    print(s)

            return s

        df_total['METER NAME'] = df_total['METER NAME'].apply(lambda x: format_meter_name(x))

        def erase_building(s):

            r = r'\d+\s*\W\s*'

            return re.sub(r, '', s)

        df_total['METER NAME'] = df_total['METER NAME'].apply(lambda x: erase_building(x))
        df_total['METER NAME'] = df_total['METER NAME'].apply(lambda x: x.replace('  ', ' '))

        def meters_column(s):

            try:
                return s.split('-')[-1].lstrip()
            except:
                print('WARNING! Found weird METER NAME:')
                print(s)

        final_df['Meter'] = df_total['METER NAME'].apply(lambda x: meters_column(x))

        def floor_column(s):

            try:
                return s.split('º')[0].lstrip()
            except:
                return s[0]

        final_df['Floor'] = df_total['METER NAME'].apply(lambda x: floor_column(x))

        def flat_column(s):

            r = r'\s*-.*'

            try:
                x = s.split('º')[1].lstrip()

                return re.sub(r, '', x)
            except:
                print('WARNING! Found weird METER NAME:')
                print(s)

        final_df['Flat'] = df_total['METER NAME'].apply(lambda x: flat_column(x) if flat_column(x) else '-')

        final_df['Meter ID'] = df_total['Meter ID']

        final_df.to_csv('Columns')

        for file in os.listdir():
            if 'Plantilla' in file:
                os.remove(file)

        final_df.columns = ['Building','METER_NAME','Meter','Floor','Flat','Meter_ID']

        json_records = final_df.reset_index().to_json(orient='records')
        data = []
        data = json.loads(json_records)
        context = {'d': data}

        return render(request, 'osiviewer/ov2.html', context)
    else:
        form = UploadFileForm()
        return render(request, 'osiviewer/ov.html', {'form': form})


def ov_run(request):
    if request.method == 'POST':

        os.chdir(settings.MEDIA_ROOT)
        files = os.listdir()

        form = UploadFileForm(request.POST, request.FILES)
        for col in request.FILES.getlist('file'):
            for file in files:
                if 'Columns' in file:
                    os.remove(file)

            ov = Ov.objects.create(document=col)
            ov.save()




        df_total = pd.DataFrame()
        total_sniffers = set()
        total_buildings = {}
        total_floors = set()
        total_meters = []
        building_name = ''

        for file in files:

            if 'Columns' in file:
                df_total = pd.read_csv(file)

                buildings = df_total['Building'].unique()
                total_meters = df_total['Meter ID'].unique()

                for building in buildings:

                    my_building = Building(df_total[df_total['Building'] == building], total_meters)

                    building_name = my_building.name

                    total_buildings[building] = max(my_building.floors)
                    for x in my_building.floors:
                        total_floors.add(x)

                    sniffer_total = pd.DataFrame()

                    for file in files:

                        if 'sniffer' in file.lower() and 'lock' not in file and 'viewing' not in file:
                            template_name = str(file)
                            full_name = template_name[:-5]
                            df = pd.DataFrame()

                            # Check for multiple sheets
                            excel_file = pd.ExcelFile(template_name)
                            sheets = excel_file.sheet_names

                            # Add different sniffs
                            for sheet in sheets:
                                df_sheet = pd.read_excel(template_name, sheet_name=sheet)
                                # Erase useless columns
                                df_sheet.drop(df_sheet.columns[[0, 13]], inplace=True, axis=1)

                                if list(df_sheet.iloc[0]) != ['Time', 'RSSI', 'Length', 'Man', 'Serial',
                                                              'Ver', 'Type', 'RP: Last routed by', 'RP: Hop',
                                                              'RP: RX state', 'RP: Time to change', 'RP: RSSI']:
                                    df_sheet.columns = ['Time', 'RSSI', 'Length', 'Man', 'Serial',
                                                        'Ver', 'Type', 'RP: Last routed by', 'RP: Hop',
                                                        'RP: RX state', 'RP: Time to change', 'RP: RSSI']

                                my_building.sniffs_names.append(sheet)
                                my_building.sniffs.append(df_sheet)
                                total_sniffers.add(sheet)

                    my_building.export_building_viewing_info(total_meters)

        merge_sniffers(total_sniffers, total_buildings, total_floors)

        with ZipFile('Osiviewer ' + building_name + '.zip', 'w') as zipo:
            for file in os.listdir(settings.MEDIA_ROOT):
                if 'final' in file or 'Lost' in file:
                    zipo.write(file)

        myzip = open(settings.MEDIA_ROOT + '/Osiviewer ' + building_name + '.zip', 'rb')
        response = HttpResponse(myzip, content_type='application/force-download')
        response['Content-Disposition'] = f'attachment;filename=Osiviewer {building_name}.zip'

        for file in os.listdir():
            os.remove(file)

        return response


def columns(request):
    if request.method == 'POST':

        file_path = os.path.join(settings.MEDIA_ROOT, 'Columns')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response


def next(request):
    form = UploadFileForm()
    return render(request, 'osiviewer/ov3.html', {'form': form})

