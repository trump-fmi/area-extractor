import geojson
import osmium as o

from geojson import Point, LineString, Feature, FeatureCollection, Polygon

DEBUG_RELATIONS_NUMBER = 100000

class _RelationFilter(o.SimpleHandler):

    def __init__(self):
        super(_RelationFilter, self).__init__()
        self.relations = {}
        self.wayReplacements = {}
        self.relationsNumber = 0

    def relation(self, r):
        if self.relationsNumber >= DEBUG_RELATIONS_NUMBER: return
        if 'type' not in r.tags: return
        if not r.tags['type'] == 'boundary': return
        if 'admin_level' not in r.tags: return
        if not r.tags['admin_level'] == '8': return
        if not r.visible: return

        element = {
            'id': r.id,
            'ways': {}
        }

        for m in r.members:
            if m.role == 'outer' and m.type == 'w':
                element['ways'][m.ref] = []
                if m.ref in self.wayReplacements:
                    self.wayReplacements[m.ref].append(r.id)
                else:
                    self.wayReplacements[m.ref] = [r.id]

            elif m.role == 'admin_centre' and m.type == 'n':
                element['centre'] = m.ref

        self.relations[r.id] = element
        self.relationsNumber += 1


class _WayFilter(o.SimpleHandler):

    def __init__(self, relations, wayReplacements):
        super(_WayFilter, self).__init__()
        self.relations = relations
        self.wayReplacements = wayReplacements
        self.additionalWays = {}

    def way(self, w):
        if w.id in self.wayReplacements:
            for i, relationId in enumerate(self.wayReplacements[w.id]):
                self.relations[relationId]['ways'][w.id] = self.createCoordinatesList(w.nodes)
        elif 'type' in w.tags and w.tags['type'] == 'boundary' and 'admin_level' in w.tags \
                and w.tags['admin_level'] == '8':
            self.additionalWays[w.id] = self.createCoordinatesList(w.nodes)

    def createCoordinatesList(self, wayNodes):
        coordinatesList = []
        for node in wayNodes:
            location = node.location
            coordinatesList.append((location.lon, location.lat))

        return coordinatesList


def easifyWays(relationWays):
    while True:
        changed = False
        for wayId1, way1 in relationWays.items():
            if (len(way1)) < 2:
                del relationWays[wayId1]
                changed = True
                break

            endNode1 = way1[len(way1) - 1]
            for wayId2, way2 in relationWays.items():
                if wayId1 == wayId2 or len(way2) < 1: continue
                startNode2 = way2[0]
                if endNode1 == startNode2:
                    relationWays[wayId1] = way1 + way2[1:]
                    del relationWays[wayId2]
                    changed = True
                    break

            if changed: break
        if not changed: break


def generateGeoJSON(relationsList, additionalWayList):
    def createFeatures(ways):
        easifyWays(ways)
        features = []

        for wayId, way in ways.items():
            if len(way) < 2: continue

            startNode = way[0]
            endNode = way[len(way) - 1]

            # Start node equals end node
            if startNode == endNode:
                geometry = Polygon([way])
            else:
                geometry = LineString(way)

            feature = Feature(id=wayId, geometry=geometry)
            features.append(feature)

        return features

    featureList = []

    for relationId, relation in relationsList.items():
        relationFeatures = createFeatures(relation['ways'])
        featureList.extend(relationFeatures)

    additionalWayFeatures = createFeatures(additionalWayList)
    featureList.extend(additionalWayFeatures)

    print(f"Features: {len(featureList)}")
    print(f"Features from relations: {len(featureList) - len(additionalWayFeatures)}")
    print(f"Features from ways: {len(additionalWayFeatures)}")

    return FeatureCollection(featureList)


def parsePBFFile(filePath):

    relationFilter = _RelationFilter()
    relationFilter.apply_file(filePath)

    print(f"Relations: {relationFilter.relationsNumber}")

    wayFilter = _WayFilter(relationFilter.relations, relationFilter.wayReplacements)
    wayFilter.apply_file(filePath, locations=True)

    jsonObject = generateGeoJSON(wayFilter.relations, wayFilter.additionalWays)
    return geojson.dumps(jsonObject, sort_keys=False)
