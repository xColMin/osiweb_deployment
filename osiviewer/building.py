from .bulding_functions import *
from statistics import mean
import os
import io
import pandas as pd
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.axes_grid1 import ImageGrid
from PIL import Image

import numpy as np
import matplotlib

warnings.simplefilter("ignore", UserWarning)
sns.set_style('whitegrid')


class Building:

    def __init__(self, df_total, total_meters):

        # str: 'building_name'
        self.name = df_total['Building'].unique()[0]

        # list: [floor1, floor2,...]
        self.floors = get_floors(df_total)

        # int: nº of floors
        self.floors_number = len(self.floors)

        # list: [flat1,flat2,...]
        self.flats = get_flats(df_total)

        # dict: {'flat_name': [flat_meter1, flat_meter2,...]}
        self.flats_meters_name = get_flats_and_meters(df_total, self.flats)

        # int: max nº of meter per flat
        self.meter_number = 0
        for key, value in self.flats_meters_name.items():
            if len(value) > self.meter_number:
                self.meter_number = len(value)

        # dict: {'meter_name': 'meter_id'}
        self.meters_name = get_meters_id(df_total)

        # dict: {'meter_id': 'meter_name'}
        self.meters_id = get_meters_name(df_total)

        # dict: {'floor': [flat_1,flat2,...]}
        self.flats_per_floor = get_flats_per_floor(self.floors, df_total)

        # list: [suffix1, suffix2]
        self.flats_suffixes = list(set([x for x in df_total['Flat']]))

        # int: max nº of flats per floor
        self.flats_number = 0
        for key, value in self.flats_per_floor.items():
            if len(value) > self.flats_number:
                self.flats_number = len(value)

        # dict: {'meter_id': [reading1,reading2,...]}
        self.meter_readings = get_meter_readings(self.meters_id)

        # dict: {'meter_id': mean_reading}
        self.meter_mean = get_meter_mean(self.meters_id)

        # placeholder for sniffer names
        self.sniffs_names = []

        # placeholder for sniffers dataframes
        self.sniffs = []

        # placeholder for flats count values viewing info dataframes
        self.flats_viewing_info_count = {}

        # placeholder for flats mean values viewing info dataframes
        self.flats_viewing_info_mean = get_flat_viewing_info(self.flats)

        # placeholder for flats images
        self.viewing_info_images = {}

        # dict: {'flat_name': [flat_meter_id1, flat_meter_id2,...]}
        self.flats_meters_id = {}
        for key, value in self.flats_meters_name.items():
            self.flats_meters_id[key] = [self.meters_name.get(key + '-' + meter) for meter in value]

        # placeholder for max number of readings in sniffer
        self.max_readings = 0

        # placeholder for min mean value of readings in sniffer
        self.min_mean_reading = 0

        # TODO Sniffer duration
        # placeholder for duration of sniffer
        self.sniffer_duration = 0

        # placeholder for meters read but not on template
        self.lost_meters = set()

    def fit_sniffer(self, sniff, total_meters):

        for key, value in self.meter_readings.items():
            self.meter_readings[key] = []

        #sniff['RSSI'] = sniff['RSSI'].apply(lambda x: abs(x))

        # TODO SNIFF OPTION CHOICE
        for index, row in sniff[['RSSI', 'Serial']].iterrows():
            try:
                self.meter_readings[row[1]].append(row[0])
            except:
                pass

        for index, row in sniff[['Serial', 'Type']].iterrows():
            if row[1] != 'U_REPEATER' and row[0] not in self.meters_id.keys():
                self.lost_meters.add(row[0])

        for reading in self.meter_readings.items():
            try:
                self.meter_mean[reading[0]] = mean(reading[1])
            except:
                self.meter_mean[reading[0]] = 0

        self.min_mean_reading = min(list(sniff['RSSI']))

        mt = list(sniff['Serial'])

        meters_buildings = [x for x in mt if x in total_meters]

        for m in meters_buildings:
            if meters_buildings.count(m) > self.max_readings:
                self.max_readings = meters_buildings.count(m)

    def set_viewing_info(self):

        for key in self.flats_viewing_info_mean.keys():
            means = []
            counts = []
            meter_list = self.flats_meters_name.get(key)

            for meter in meter_list:
                means.append(self.meter_mean.get(self.meters_name.get(key + '-' + meter)))
                counts.append(len(self.meter_readings.get(self.meters_name.get(key + '-' + meter))))

            self.flats_viewing_info_mean[key] = means
            self.flats_viewing_info_count[key] = counts

        for key, value in self.flats_viewing_info_mean.items():

            self.flats_viewing_info_mean[key] = pd.DataFrame(data=[self.flats_meters_id.get(key),
                                                                   self.flats_viewing_info_mean.get(key)],
                                                             index=['Meter ID', 'Mean'])

            self.flats_viewing_info_count[key] = pd.DataFrame(data=[self.flats_meters_id.get(key),
                                                                    self.flats_viewing_info_count.get(key)],
                                                              index=['Meter ID', 'Count'])

    def export_flat_viewing_info(self, key, sniff_name):

        value = self.flats_viewing_info_mean.get(key)

        value_means = value.transpose()
        value_counts = self.flats_viewing_info_count.get(key)
        value_counts = value_counts.transpose()

        value_counts['Meter ID'] = value_counts['Meter ID'].apply(lambda x: int(str(x)[-5:]))

        flat = pd.DataFrame(data=value_means['Mean'].tolist(),index=value_means['Meter ID'])
        flat_counts = pd.DataFrame(data=value_counts['Count'].tolist(),index=value_counts['Meter ID'])

        fig, (ax, ax2) = plt.subplots(2, 1, figsize=(0.5 + 1.5 * self.meter_number, 2.25))
        fig.subplots_adjust(hspace=0.000000001)

        sns.heatmap(data=flat.transpose(),
                    cmap=sns.color_palette([ "cyan", "darkturquoise", "skyblue", "royalblue", "midnightblue", "tomato"],
                                           as_cmap=True, desat=0.75, n_colors=10), ax=ax, cbar=False, annot=True, linecolor='black',
                    xticklabels=False, yticklabels=False, square=True, vmax=0, vmin=-133)

        sns.heatmap(data=flat_counts.transpose(), cmap="Greens", ax=ax2, cbar=False, annot=True, linecolor='black',
                    yticklabels=False, square=True, vmin=0, vmax=self.max_readings)

        ax2.set_ylabel('#')
        ax.set_ylabel('Mean')

        ax.set_xlabel('')
        ax2.set_xlabel('')

        plt.xticks(rotation=0)

        try:
            if key[0:key.index('º')+1] == sniff_name[sniff_name.index('º')-2:sniff_name.index('º')+1] and self.name.split('-')[1].lower() in sniff_name.lower():
                fig.patch.set_facecolor('xkcd:light yellow')
        except:
            pass

        ax.set_title(key)

        plt.close(fig)

        return fig

    def export_building_viewing_info(self, total_meters):

        for index, sniff_value in enumerate(self.sniffs):
            self.fit_sniffer(sniff_value, total_meters)

            self.set_viewing_info()

            fig2 = plt.figure(figsize=(2 * 0.9 * self.flats_number * self.meter_number,
                                       2.5 * self.floors_number))

            fig2.suptitle(self.name, y=0.1)

            grid = ImageGrid(fig2, 111,
                             nrows_ncols=(self.floors_number, self.flats_number),
                             axes_pad=0.00001, aspect=True, share_all=True)

            flats = [key for key in self.flats_viewing_info_mean.keys()]

            flats = sorted_flats(flats, self.floors)

            flat_holder = []
            floor_index = get_floor_number(flats[0])

            for ax in grid:

                if len(flat_holder) == self.flats_number:
                    floor_index = str(int(floor_index) - 1)
                    flat_holder = []

                if len(flat_holder) < len(self.flats_per_floor.get(floor_index)):

                    for flat in flats:

                        flat_im = self.export_flat_viewing_info(flat, self.sniffs_names[index])

                        buf = io.BytesIO()
                        flat_im.savefig(buf, format='png')
                        buf.seek(0)
                        im = Image.open(buf)
                        ax.imshow(im)
                        buf.close()

                        ax.grid(False)
                        ax.set_yticklabels([''])
                        ax.set_xticklabels([''])

                        flats.pop(0)
                        flat_holder.append(flat)

                        break

                else:

                    ax.grid(False)
                    flat_holder.append('0')

            plt.savefig(self.sniffs_names[index] + ' ' + self.name + "_connectivity_view.png", bbox_inches='tight')

            if len(self.lost_meters) != 0:
                text_file = open('Lost Meters' + self.sniffs_names[index] + ' ' + self.name, "w")
                n = text_file.write(str(self.lost_meters).replace(' ', ''))
                text_file.close()

            plt.close(fig2)


