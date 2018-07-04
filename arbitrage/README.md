Money Man Spiff's Arbitrage Arm

Author: Parker Timmerman

Based around the idea of being able to detect arbirage oppurtunities using Bellman-Ford to find negative cycles
in a graph. The graph.py file contains a Graph and Edge class. 
Edge: Used specifically to connect nodes of the graph, assuming those nodes are something the represents a currency
Graph: A dictionary of dictionaries. Keys are strings which are currencies, values are dictionaries whose keys are strings
which represent a second (different) currency, and values are now Edges, which contain all the important info for arbitrage.

NOTE: All money related numerical values are instances of the Decimal class from Python

Conventions:
Within the program I tried to use the same naming conventions, they are listed below:
a1 = asset 1
a2 = asset 2
xrate = exhange rate, the actual factor which to convert from one currency to another
weight = should always be -log(xrate), this is used to reduce shortest paths problem to arbitrage
vol = volume of a certain bid or ask
vol_sym = symbol for which the volume is in terms of
