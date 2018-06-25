from requests.exceptions import HTTPError
from graph import Graph
import krakenex
import pprint
import pandas as pd

k = krakenex.API()

#try:
#    resp = k.query_public('AssetPairs')
#    asset_pairs = resp['result']
#    asset_pairs = list([asset_pair for asset_pair in asset_pairs.keys() if not '.d' in asset_pair])
#    print(asset_pairs)
    #for x in resp['result'].keys():
    #    print(x)
    #pprint.pprint(resp['result']['XETCZUSD'])
    
#    resp1 = k.query_public('Assets')
#    if resp1['error'] == []:
#        pprint.pprint(resp1)
#    
#    resp2 = k.query_public('Ticker', {'pair': resp['result']['XETCZUSD']['altname']})
#    pprint.pprint(resp2)
#except HTTPError as e:
#    print(str(e))

G = Graph()

G.addNode('USD')
G.addNode('EUR')
G.addNode('BTC')

G.addEdge('USD', 'EUR', 0.8)
G.addEdge('EUR', 'USD', 1.2)
G.addEdge('USD', 'BTC', 0.00016)
G.addEdge('BTC', 'USD', 6000)
G.addEdge('EUR', 'BTC', 0.0002)
G.addEdge('BTC', 'EUR', 5000)

G.print()
print(G.getNodes())
print(G.getEdges())

print("Edge weight from USD to EUR = {}".format(G.getWeight('USD', 'EUR')))


NC = Graph()
NC.addNode('A')
NC.addNode('B')
NC.addNode('C')
NC.addNode('D')
NC.addNode('E')

NC.addEdge('A', 'B', 7)
NC.addEdge('A', 'D', 3)
NC.addEdge('B', 'C', 4)
NC.addEdge('B', 'E', 3)
NC.addEdge('D', 'E', 2)
NC.addEdge('E', 'C', -8)
NC.addEdge('C', 'B', 1)

NC.print()
path = NC.BellmanFord('A')
print(path)
