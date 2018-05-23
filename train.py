"""
Train Money Man Spiff with data gathered from Poloniex given a currency list

Author: Parker Timmerman
"""

import random
import getData
import pandas as pd
import numpy as np

from network import Network

class TrainingPipeline():

    def __init__(self, initial_model = None):
        self.learning_rate = 2e-3
        
        self.lr_multiplier = 1.0                        # Dynamically adjust learning rate using Kullbeck-Liebler
        self.kl_targ = 0.02

        self.batch_size = 8
        self.epochs = 32

        if initial_model:
            self.network = Network(model_file = initial_model)
        else:
            self.network = Network()

    def run(self):
        """
        Run the training pipeline
        """


