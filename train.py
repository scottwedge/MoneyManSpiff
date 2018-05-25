"""
Train Money Man Spiff with data gathered from Poloniex given a currency list

Author: Parker Timmerman
"""

import random
import math
import os
import sys
import getData
import pandas as pd
import numpy as np

from collections import deque
from network import Network

class TrainingPipeline():

    def __init__(self, initial_model = None):
        self.learning_rate = 2e-3
        
        self.lr_multiplier = 1.0                        # Dynamically adjust learning rate using Kullbeck-Liebler
        self.kl_targ = 0.02

        self.batch_size = 64
        self.epochs = 20

        if initial_model:
            self.network = Network(model_file = initial_model)
        else:
            self.network = Network()

    def verifyData(self, pairs):
        """ Verifies that the data for the given currencies exists, if it doesn't then it gets it"""
        if not os.path.exists("data"):
            getData.getPairs(pairs)
            return True

        for pair in pairs:
            # If there is no data for a given pair, get the data
            if not os.path.isfile("data/{}".format(pair)):
                getData.getData(pair)

        return True

    def move_to_loc(self, move, width, height):
        row = move // width
        col = move % height
        return [row, col]

    def buildImages(self, pairs, fields):
        """ Turn the CSV data into "images" which we can later build videos out of and train the network with """
        images = deque()
        width = height = int(math.sqrt(len(pairs) + 1))
        channels = len(fields)

        print("Building {} x {} images with {} channels...".format(width, height, channels))

        # Open each file (careful with memory here if you want to use a lot of currencies
        data_frames = [pd.read_csv("data/{}.csv".format(pair)) for pair in pairs]

        start_time = max([int(df['date'][0]) for df in data_frames])
        end_time = min([int(open("data/{}".format(pair)).readline()) for pair in pairs])

        for time in range(1464066600, 1464066600 + end_time, 300):
            if time % (300 * 5000) == 0:
                print("{} : {}".format(time, end_time))

            image = np.zeros((channels, width, height), dtype=float)
            for idx, df in enumerate(data_frames):
                row = df.loc[df['date'] == time]
                for channel, field in enumerate(fields):
                    r, c = self.move_to_loc(idx, width, height)
                    if not row.empty:
                        image[channel][r][c] = row[field]
                    else:
                        image[channel][r][c] = 0
            images.append((time,image))
        return images

    def run(self):
        # Check to make sure currency pair file is given
        if (len(sys.argv)) != 2:
            print("Need to provide one argument, the CSV file of currency pairs!")
            sys.exit(0)

        # Read given currency pairs
        cp_df = pd.read_csv(sys.argv[1])
        given_pairs = [pair for pair in cp_df.columns]

        # Check for data for each currency pair if it doesnt exist then get it
        self.verifyData(given_pairs) 

        # Build a feed of "images" that we can feed to the network
        images = self.buildImages(given_pairs, ['volume', 'quoteVolume', 'weightedAverage'])
        numImgs = len(images)

        print("Finished building images! Beginning to create vidoes and train the network...")

        video_buffer = []

        # Initialize the video with the first 48 images
        video = deque()
        for i in range(0, 48):
            video.append(images.popleft()[1])
        price = images[11][1][2][0][0]               # This is the price of ETH an hour ahead

        video_buffer.append((np.array(video), price))

        # Pop off the first (earliest) frame from the video, and push on the next one from images
        while len(images) >= 12:
            video.popleft()                         # Remove earliest frame
            video.append(images.popleft()[1])       # Add on the latest image
            price = images[11][1][2][0][0]          # Get the price for an hour ahead for ETH

            video_buffer.append((np.array(video), price))           # Add videos to a buffer to 

            if (len(video_buffer) >= self.batch_size):
                videos = np.array([data[0].reshape(3, 6, 6, 48) for data in video_buffer])
                prices = np.array([data[1] for data in video_buffer])
                    
                self.network.train_step(videos, prices, self.learning_rate, self.epochs)
                print("Trained {} videos so far! {}% of the data set".format((numImgs - len(images)), (( 1 - (len(images)/numImgs)) *100 ) )) 
                video_buffer.clear()
                self.network.save_model("current.model")

        self.network.save_model("end.model")

if __name__ == '__main__':
    training_pipeline = TrainingPipeline()
    training_pipeline.run()
