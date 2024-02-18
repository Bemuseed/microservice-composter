from enum import Enum

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

    def __init__(self, classes):
        self.name = "microservice" + str(type(self)._microservice_counter)
        type(self)._microservice_counter += 1
        self.classes = classes
        self.isc = 0
        self.esc = 0
        self.updateCohesions()
    
    def updateCohesions(self):
        if (len(self.classes) == 1):
            self.isc = 0
            self.esc = 0
        else:
            internal_cohesion = 0
            for i in range(len(self.classes)-1):
                for j in range(i+1, len(self.classes)):
                    internal_cohesion += self.classes[i].intraSimilarity(self.classes[j], pr)
                    internal_cohesion += self.classes[j].intraSimilarity(self.classes[i], pr)
            self.isc = internal_cohesion / (len(self.classes) * (len(self.classes) - 1))

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


"""

for i in range(len(classes)-1):
    for j in range(i+1, len(classes)):
        intrasim = intraSimilarity(classes[i], classes[j], pr, lev_distances[(classes[i].name, classes[j].name)])
        print("sim_intra("+classes[i].name+", "+classes[j].name+") = "+str(intrasim))
        intrasim_swapped = intraSimilarity(classes[j], classes[i], pr, lev_distances[(classes[i].name, classes[j].name)]) #Lev-distance tuple-key isn't swapped because its order matters
        print("sim_intra("+classes[j].name+", "+classes[i].name+") = "+str(intrasim_swapped))
 
print("\n\n")

for i in range(len(classes)-1):
    for j in range(i+1, len(classes)):
        intersim = interSimilarity(classes[i], classes[j], pr, lev_distances[(classes[i].name, classes[j].name)])
        print("sim_inter("+classes[i].name+", "+classes[j].name+") = "+str(intersim))
        intersim_swapped = interSimilarity(classes[j], classes[i], pr, lev_distances[(classes[i].name, classes[j].name)])
        print("sim_inter("+classes[j].name+", "+classes[i].name+") = "+str(intersim_swapped))
"""

l = []
for c in classes:
    l.append(Microservice([c])) 

l_tmp = []
for i in range(len(l)-1):
    for j in range(i+1, len(l)):
        l_tmp.append(Microservice(l[i].classes + l[j].classes))
        print(l_tmp[-1].name, end="")
        print(" (ISC=" + str(l_tmp[-1].isc) + "):")
        for c in l_tmp[-1].classes:
            print("\t"+c.name)