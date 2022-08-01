from django.shortcuts import render
from .forms import UploadFileForm
from .models import Cc
import os
import pandas as pd
from django.conf import settings
from django.http import HttpResponse, Http404


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        for file in request.FILES.getlist('file'):
            cc = Cc.objects.create(document=file)
            cc.save()

        flats = {2563: '4016-001 1º CD', 2553: '4016-001 1º CD', 2554: '4016-002 1º CI', 2963: '4016-002 1º CI',
                 2555: '4016-010 3º CI', 2964: '4016-010 3º CI', 2556: '4016-014 4º CI', 2965: '4016-014 4º CI',
                 2557: '4016-020 5º I', 2966: '4016-020 5º I', 2558: '4016-024 6º I', 2967: '4016-024 6º I',
                 2559: '4016-030 8º CI', 2968: '4016-030 8º CI', 2560: '4016-032 8º I', 2969: '4016-032 8º I',
                 2561: '4016-034 9º CI', 2970: '4016-034 9º CI', 2562: '4016-036 9º I', 2564: '4016-036 9º I',
                 2565: '4017-003 1º D', 2971: '4017-003 1º D', 2566: '4017-013 4º CD', 2972: '4017-013 4º CD',
                 2567: '4017-018 5º CI', 2973: '4017-018 5º CI', 2568: '4017-019 5º D', 2974: '4017-019 5º D',
                 2569: '4017-021 6º CD', 2975: '4017-021 6º CD', 2570: '4017-026 7º CI', 2976: '4017-026 7º CI',
                 2571: '4017-027 7º D', 2977: '4017-027 7º D', 2572: '4017-034 9º CI', 2978: '4017-034 9º CI',
                 2573: '4017-035 9º D', 2979: '4017-035 9º D', 2574: '4017-036 9º I', 2980: '4017-036 9º I',
                 2585: '4018-002 1º CI', 2981: '4018-002 1º CI', 2586: '4018-010 3º CI', 2982: '4018-010 3º CI',
                 2587: '4018-011 3º D', 2983: '4018-011 3º D', 2588: '4018-015 4º D', 2984: '4018-015 4º D',
                 2589: '4018-020 5º I', 2985: '4018-020 5º I', 2590: '4018-023 6º D', 2986: '4018-023 6º D',
                 2591: '4018-025 7º CD', 2987: '4018-025 7º CD', 2592: '4018-030 8º CI', 2988: '4018-030 8º CI',
                 2593: '4018-031 8º D', 2989: '4018-031 8º D', 2594: '4018-035 9º D', 2990: '4018-035 9º D',
                 2596: '4019-007 4º D', 2991: '4019-007 4º D', 2597: '4019-009 5º D', 2992: '4019-009 5º D',
                 2598: '4019-011 6º D', 2993: '4019-011 6º D', 2599: '4019-012 6º I', 2994: '4019-012 6º I',
                 2600: '4019-015 8º D', 2995: '4019-015 8º D'}

        df_final = pd.DataFrame()

        os.chdir(settings.MEDIA_ROOT)

        def format_date_no_zeros(s):
            if not pd.isna(s):
                s_list = s.split()
                d = s_list[0].split('/')
                for n in range(len(d) - 1):
                    if len(d[n]) < 2:
                        d[n] = '0' + d[n]
                return '/'.join(d) + ' ' + s_list[1]

        for file in os.listdir():
            if 'xls' in file and 'lock' not in file:
                df_data = pd.read_excel(file)
                df_final = pd.concat([df_final, df_data])

        df_final['Unnamed: 0'] = df_final['Unnamed: 0'].apply(lambda x: format_date_no_zeros(x))
        df_final.at[0, 'Unnamed: 0'] = 'Type'

        for c in df_final.columns:
            if c.startswith('Cal') or c.startswith('GV') or c.startswith('faci'):
                df_final.drop(c, axis=1, inplace=True)

        def format_date(s):
            s = s[:-7].replace('-', '/')
            s_list = s.split()
            d = s_list[0].split('/')
            d.reverse()
            dt = '/'.join(d)
            return dt + ' ' + s_list[1]

        for file in os.listdir():
            if 'csv' in file and 'lock' not in file:
                if os.path.getsize(file) > 0:
                    meter_id = file[3:-4]
                    df_ds = pd.read_csv(file, names=['Unnamed: 0', 'flats', 'Type'])
                    t = df_ds['Type'][0]
                    df_ds.columns = ['Unnamed: 0', flats.get(int(meter_id)), 'Type']
                    df_ds.drop('Type', axis=1, inplace=True)
                    df_ds['Unnamed: 0'] = df_ds['Unnamed: 0'].apply(lambda x: format_date(x))
                    df_ds.iloc[-1] = ['Type', t]
                    df_final = df_final.merge(df_ds, on='Unnamed: 0')

        df_final.drop_duplicates(inplace=True)
        df_final.at[0, 'Unnamed: 0'] = ''
        df_final = df_final.rename(columns={'Unnamed: 0': ''})

        for rowIndex, row in df_final.iterrows():
            for columnIndex, value in row.items():
                if isinstance(value, int) and value < 0:
                    df_final.at[rowIndex, columnIndex] = 0
                elif isinstance(value, float):
                    if value < 0:
                        df_final.at[rowIndex, columnIndex] = 0
                    else:
                        df_final.at[rowIndex, columnIndex] = round(value, 2)

        df_final = df_final.reindex(sorted(df_final.columns), axis=1)

        df_final.sort_values(by='', inplace=True)

        d = {'Hca': 'HCA (ud. HCA)', 'Water': 'Water (m³)', '%HR': 'HR (%)', '°C': 'Tª (°C)'}

        df_final.loc[0] = df_final.loc[0].apply(lambda x: d.get(x))

        df_final.to_excel('final.xls', index=False)

        file_path = os.path.join(settings.MEDIA_ROOT, 'final.xls')
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                for file in os.listdir():
                    os.remove(file)
                return response

    else:
        form = UploadFileForm()
        return render(request, 'consumer_care/cc.html', {'form': form})
