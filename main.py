from enum import Enum
import math

class RelationshipType(Enum):
    INHERITANCE = 1
    REALIZATION = 2
    COMPOSITION = 3
    AGGREGATION = 4
    ASSOCIATION = 5
    DEPENDENCY = 6

internal_weightings = {
    RelationshipType.REALIZATION: 1,
    RelationshipType.INHERITANCE: 0.9,
    RelationshipType.COMPOSITION: 0.8,
    RelationshipType.AGGREGATION: 0.7,
    RelationshipType.ASSOCIATION: 0.4,
    RelationshipType.DEPENDENCY: 0.2
}

external_weightings = {
    RelationshipType.REALIZATION: 0,
    RelationshipType.INHERITANCE: 0,
    RelationshipType.COMPOSITION: 0.2,
    RelationshipType.AGGREGATION: 0.4,
    RelationshipType.ASSOCIATION: 0.8,
    RelationshipType.DEPENDENCY: 1
}

def levSimilarity(class_a, class_b):
    lev_dist = getLevDistance(class_a, class_b)
    len_a = len(class_a.name)
    len_b = len(class_b.name)
    if (len_a == len_b):
        return 1 - (lev_dist / len_a)
    else:
        return 1 - (lev_dist / (len_a + len_b))

def pr(list):
    product = list[0]
    for i in range(1, len(list)):
        product *= list[i] 
    return (list[0] + product) / 2


lev_distances = {('Student', 'DbStorage'): 7, ('Student', 'FileStorage'): 9, ('Student', 'DataParser'): 8, ('Student', 'Controller'): 9, ('Student', 'StorageType'): 9, ('DbStorage', 'FileStorage'): 6, ('DbStorage', 'DataParser'): 7, ('DbStorage', 'Controller'): 8, ('DbStorage', 'StorageType'): 8, ('FileStorage', 'DataParser'): 10, ('FileStorage', 'Controller'): 10, ('FileStorage', 'StorageType'): 8, ('DataParser', 'Controller'): 8, ('DataParser', 'StorageType'): 10, ('Controller', 'StorageType'): 10}

def getLevDistance(class_a, class_b):
    if ((class_a.name, class_b.name) in list(lev_distances.keys())):
        return lev_distances[(class_a.name, class_b.name)]
    else:
        return lev_distances[(class_b.name, class_a.name)]

class Class:
    def __init__(self, name):
        self.name = name
        # Relationships are tuples in the format (Class, RelationshipType)
        self.outgoing_relationships = []

    def addRelationship(self, rship):
        self.outgoing_relationships.append(rship)
    
    def getRelationshipsTo(self, other_class):
        relationships = []
        for r in self.outgoing_relationships:
            if r[0].name == other_class.name:
                relationships.append(r[1])
        return relationships
    
    def intraSimilarity(self, other_class, fsim):
        relationships = self.getRelationshipsTo(other_class)
        if (relationships == []):
            max_relationship = 0
        else:
            max_relationship = max(map(internal_weightings.get, relationships))
        
        return fsim([max_relationship, levSimilarity(self, other_class)])

    def interSimilarity(self, other_class, fsim):
        relationships = self.getRelationshipsTo(other_class)
        if (relationships == []):
            max_relationship = 0
        else:
            max_relationship = min(map(external_weightings.get, relationships))
        
        return fsim([max_relationship, 1 - levSimilarity(self, other_class)])


class Microservice:
    _microservice_counter = 1

    def __init__(self, classes, parents):
        self.name = "microservice" + str(type(self)._microservice_counter)
        type(self)._microservice_counter += 1
        self.classes = classes
        self.parents = parents
        self.ics = 0
        self.ecs = 0
    
    def updateInternalCohesion(self):
        if (len(self.classes) == 1):
            self.ics = 0
        else:
            internal_cohesion = 0
            for i in range(len(self.classes)-1):
                for j in range(i+1, len(self.classes)):
                    internal_cohesion += self.classes[i].intraSimilarity(self.classes[j], pr)
                    internal_cohesion += self.classes[j].intraSimilarity(self.classes[i], pr)
            self.ics = internal_cohesion / (len(self.classes) * (len(self.classes) - 1))
    
    def updateExternalCohesion(self, other_mics):
        children = []
        for mic in other_mics:
            for c in mic.classes:
                if (c in self.classes):
                    children.append(mic)

        clients = []
        for mic in other_mics:
            if (mic not in children):
                for c in mic.classes:
                    for r in c.outgoing_relationships:
                        if (r[0] in self.classes):
                            clients.append(mic)
        
        if (clients):
            external_cohesion = 0
            for mic in clients:
                x = 0
                for ci in mic.classes:
                    for cj in self.classes:
                        x += ci.interSimilarity(cj, pr)
                external_cohesion += x / len(self.classes)
            self.ecs = external_cohesion / len(clients)
        else:
            self.ecs = 0

def getSubObptimal(mic_list):
    globalCounter = -1
    globalMax = -1
    globalMin = math.inf
    for i in range(len(mic_list)):
        localMax = mic_list[i].ics
        localMin = mic_list[i].ecs
        mic = mic_list[i]
        for j in range(len(mic_list)):
            if (i != j):
                localMax = max(localMax, mic_list[j].ics)
                localMin = min(localMin, mic_list[j].ecs)

        localCounter = 0
        for j in range(1, len(mic_list)):
            if (mic_list[j].ics <= localMax and mic_list[j].ecs >= localMin and mic_list[j] != mic):
                localCounter += 1
        if localCounter > globalCounter:
            globalCounter = localCounter
            globalMax = localMax
            globalMin = localMin
            globalMic = mic
    return globalMic

def printMicHeader(mic):
    print(mic.name+"(ISC="+str(round(mic.ics, 2))+", ESC="+str(round(mic.ecs, 2))+"): ",end="")

clsController = Class("Controller")
clsStorageType = Class("StorageType")
clsDbStorage = Class("DbStorage")
clsFileStorage = Class("FileStorage")
clsDataParser = Class("DataParser")
clsStudent = Class("Student")

clsController.addRelationship((clsStorageType, RelationshipType.ASSOCIATION))
clsController.addRelationship((clsDbStorage, RelationshipType.DEPENDENCY))
clsController.addRelationship((clsFileStorage, RelationshipType.DEPENDENCY))
clsDataParser.addRelationship((clsDbStorage, RelationshipType.COMPOSITION))
clsDataParser.addRelationship((clsFileStorage, RelationshipType.COMPOSITION))
clsStudent.addRelationship((clsDbStorage, RelationshipType.COMPOSITION))
clsStudent.addRelationship((clsFileStorage, RelationshipType.COMPOSITION))

classes = [clsStudent, clsDbStorage, clsFileStorage, clsDataParser, clsController, clsStorageType]

# Threshold constants
ics_min = 0.29
ecs_min = 0.2

# Initialization
l = []
for c in classes:
    l.append(Microservice([c], None)) 
l_tmp = [1] # Dummy value because we need the below to run once and Python lacks 'do-while'
iter_count = 0

while (len(l_tmp) != 0):
    print("\n==========================")
    print("ITERATION " + str(iter_count+1))
    print("==========================\n")

    l_tmp = []
    for i in range(len(l)-1):
        for j in range(i+1, len(l)):
            new_mic = Microservice(l[i].classes + l[j].classes, [l[i], l[j]])
            new_mic.updateInternalCohesion()
            new_mic.updateExternalCohesion(l)
            print(l[i].name + " + " + l[j].name + " -> ",end="")
            printMicHeader(new_mic)
            if (new_mic.ics >= ics_min and new_mic.ecs >= ecs_min):
                l_tmp.append(new_mic)
                print("PASS")
            else:
                del new_mic
                print("FAIL")

    print("\n\n-------------------")
    print("Microservices in l_tmp: ")
    for mic in l_tmp:
        print("\t",end="")
        printMicHeader(mic)
        print()
        for c in mic.classes:
            print("\t\t"+c.name)

    print("-----------------")

    if (len(l_tmp) != 0):
        subOptimalMic = getSubObptimal(l_tmp)
        l.append(subOptimalMic)
        l.remove(subOptimalMic.parents[0])
        l.remove(subOptimalMic.parents[1])

        print("\nSelected microservice: " + subOptimalMic.name)
        print("\nNew list of L:")
        for mic in l:
            printMicHeader(mic)
            print()
            for c in mic.classes:
                print("\t"+c.name)
        
        input("\nPress [RETURN] to continue to the next iteration.")
        iter_count += 1
    else:
        input("Iterations COMPLETE!")