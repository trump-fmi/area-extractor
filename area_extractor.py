import geojson
import osmium as o

from geojson import Point, LineString, Feature, FeatureCollection



class _AreaFilter(o.SimpleHandler):

    def __init__(self):
        super(_AreaFilter, self).__init__()
        self.elements = []
        self.requiredNodes = {}
        self.wayCounter = 0

    def way(self, w):
        if 'admin_level' not in w.tags: return
        if not w.tags['admin_level'] == '8': return

        # Build object
        element = {
            'type': 'way',
            'id': w.id,
            'nodes': [None] * len(w.nodes)
        }

        self.elements.append(element)

        nodeIndex = 0
        for n in w.nodes:

            replaceInfo = {
                'element': element,
                'index': nodeIndex
            }

            if n in self.requiredNodes:
                self.requiredNodes[n.ref].append(replaceInfo)
            else:
                self.requiredNodes[n.ref] = [replaceInfo]
            nodeIndex += 1

        self.wayCounter += 1

    def relation(self, r):
        if not 'admin_level' in r.tags: return
        if not r.tags['admin_level'] == '8': return
        print("relation")


class _NodeFinder(o.SimpleHandler):

    def __init__(self, elements, requiredNodes):
        super(_NodeFinder, self).__init__()
        self.elements = elements
        self.requiredNodes = requiredNodes

    def node(self, n):
        if n.id not in self.requiredNodes: return
        replaceInfos = self.requiredNodes[n.id]

        for replaceInfo in replaceInfos:
            element = replaceInfo['element']

            index = replaceInfo['index']
            element['nodes'][index] = (n.location.lon, n.location.lat)


def generateGeoJSON(elementsList):
    featureList = []

    for element in elementsList:
        nodesList = [node for node in element['nodes'] if node is not None]

        if len(nodesList) < 2: continue

        if element['type'] == 'way':
            geometry = LineString(nodesList)
            feature = Feature(id=element['id'], geometry=geometry)
            featureList.append(feature)

    return FeatureCollection(featureList)


def parsePBFFile(filePath):
    ways = _AreaFilter()
    ways.apply_file(filePath)

    print(f"Elements: {len(ways.elements)}")
    print(f"Required nodes: {len(ways.requiredNodes)}")

    nodeFinder = _NodeFinder(ways.elements, ways.requiredNodes)
    nodeFinder.apply_file(filePath)

    jsonObject = generateGeoJSON(nodeFinder.elements)

    return geojson.dumps(jsonObject, sort_keys=False)
