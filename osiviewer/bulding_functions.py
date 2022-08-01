from PIL import Image
import os


def get_floor_number(meter_name):

    return meter_name[0:meter_name.index('º')]


def get_floors(df):

    total_floors = list(set([str(x) for x in df['Floor']]))
    total_floors.sort()

    return total_floors


def get_meters_id(df):

    meters = {}

    for index, row in df[['Floor', 'Flat', 'Meter', 'Meter ID']].iterrows():
        meters[str(row[0]) + 'º' + row[1] + '-' + row[2]] = row[3]

    return meters


def get_meters_name(df):

    meters = {}
    for index, row in df[['Floor', 'Flat', 'Meter', 'Meter ID']].iterrows():
        meters[row[3]] = str(row[0]) + 'º' + row[1] + '-' + row[2]

    return meters


def get_flat_suffix(meter_name):

    split = meter_name.split('º')

    return split[1].split()[0]


def get_flats(df):

    flats = []

    for index, row in df[['Floor', 'Flat']].iterrows():
        flats.append(str(row[0]) + 'º' + row[1])

    return list(set(flats))


def get_flats_and_meters(df, flats):

    flats_meters_dic = {}

    for flat in flats:
        flats_meters_dic[flat] = []

    for index, row in df[['Floor', 'Flat', 'Meter']].iterrows():
        flats_meters_dic[str(row[0]) + 'º' + row[1]].append(row[2])

    return flats_meters_dic


def get_meter_readings(meters):

    meter_readings = {}

    for key in meters.keys():
        meter_readings[key] = []

    return meter_readings


def get_meter_mean(meters):

    meter_readings = {}

    for key in meters.keys():
        meter_readings[key] = ''

    return meter_readings


def get_flats_per_floor(floors, df):

    flats_per_floors = {}

    for floor in floors:
        flats_per_floors[floor] = set()

    for index, row in df[['Floor', 'Flat']].iterrows():
        flats_per_floors[str(row[0])].add(row[1])

    for key, value in flats_per_floors.items():
        flats_per_floors[key] = list(value)

    return flats_per_floors


def get_flat_viewing_info(flats):

    d = {}

    for flat in flats:
        d[flat] = ''

    return d


def sort_flats(flats):

    flats.sort(reverse=True)

    final_cols = []
    new_cols = []

    for x in flats:
        if len(x) == 4:
            final_cols.append(x)
        else:
            new_cols.append(x)

    new_cols.sort(reverse=True)

    for x in new_cols:
        final_cols.append(x)

    return final_cols


def merge_sniffers(total_sniffers, total_buildings, total_floors):

    os.chdir('/home/jarvis/osiveris/web/osiweb/media')
    files = os.listdir()
    files.sort()
    image_size_x = 0

    top_floor = max(total_buildings.values())

    for file in files:
        if '.png' in file and 'final' not in file and list(total_sniffers)[0] in file:
            image = Image.open(file)
            image_size_x += image.size[0]
            image.close()

    for x in total_sniffers:

        new_image = Image.new('RGB', (image_size_x, 176 * (len(total_floors) + 1)))
        counter = 0

        for f in files:

            center_height = 0

            if x in f and '.png' in f and 'final' not in f:

                for key, value in total_buildings.items():
                    if key in f:
                        if value != top_floor:
                            center_height = (int(top_floor) - int(value)) * 179

                sniffer_view = Image.open(f)
                if counter == 0:
                    new_image.paste(sniffer_view, (0, center_height))
                else:
                    new_image.paste(sniffer_view, (counter, center_height))
                counter += sniffer_view.size[0]
                sniffer_view.close()

        new_image.save(x + " final viewing info.png")
        new_image.close()


def sorted_flats(flats, floors):

    floor_numbers = [int(x) for x in floors]
    floor_numbers.sort(reverse=True)

    result = []

    for x in floor_numbers:
        floor_flats = []
        for f in flats:
            if str(x) == f.split('º')[0]:
                floor_flats.append(f)
        floor_flats.sort()
        for sorted_f in floor_flats:
            result.append(sorted_f)

    return result








