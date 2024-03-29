from enum import Enum
import copy

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

lev_distances = {
    ('Controller', 'Role'): 6,
    ('Controller', 'Students'): 9,
    ('Controller', 'AcademicStaffMembers'): 16,
    ('Controller', 'Student'): 9,
    ('Controller', 'AcademicStaffMember'): 15,
    ('Controller', 'Module'): 7,
    ('Controller', 'ModuleCode'): 9,
    ('Students', 'AcademicStaffMembers'): 16,
    ('Students', 'Student'): 1,
    ('Students', 'AcademicStaffMember'): 16, 
    ('Students', 'Module'): 7,
    ('Students', 'ModuleCode'): 8,
    ('Students', 'Role'): 7,
    ('AcademicStaffMembers', 'Student'): 16,
    ('AcademicStaffMembers', 'AcademicStaffMember'): 1,
    ('AcademicStaffMembers', 'Module'): 18, 
    ('AcademicStaffMembers', 'ModuleCode'): 17,
    ('AcademicStaffMembers', 'Role'): 19,
    ('AcademicStaffMember', 'Student'): 16,
    ('AcademicStaffMember', 'Module'): 17,
    ('AcademicStaffMember', 'ModuleCode'): 16,
    ('AcademicStaffMember', 'Role'): 18,
    ('Student', 'Module'): 6,
    ('Student', 'ModuleCode'): 8,
    ('Student', 'Role'): 6,
    ('Module', 'ModuleCode'): 4,
    ('Module', 'Role'): 3,
    ('ModuleCode', 'Role'): 7,
} 

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
                            break
        
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

"""
def getSubOptimal(mic_list: list):
    random.shuffle(mic_list)
    globalCounter = -1
    for i in range(len(mic_list)):
        localMax = mic_list[i].ics
        localMin = mic_list[i].ecs
        mic = mic_list[i]
        for j in range(len(mic_list)):
            if (i != j):
                if (mic_list[j].ics >= localMax and mic_list[j].ecs <= localMin):
                    localMax = mic_list[j].ics
                    localMin = mic_list[j].ecs
                    mic = mic_list[j]

        printMicHeader(mic)
        print()
        localCounter = 0
        for j in range(len(mic_list)):
            if (mic_list[j].ics <= localMax and mic_list[j].ecs >= localMin and mic_list[j] != mic):
                localCounter += 1
        print(localCounter)
        print(globalCounter)
        if localCounter > globalCounter:
            print("WIN")
            globalCounter = localCounter
            globalMic = mic
    print("BIG WIN")
    printMicHeader(globalMic)
    return globalMic
"""
def getSubOptimal(mic_list: list):
    high_score = -1
    for i in range(len(mic_list)):
        localMax = mic_list[i].ics
        localMin = mic_list[i].ecs
        mic = mic_list[i]
        for j in range(len(mic_list)):
            if (i != j):
                if (mic_list[j].ics >= localMax and mic_list[j].ecs <= localMin):
                    localMax = mic_list[j].ics
                    localMin = mic_list[j].ecs
                    mic = mic_list[j]

        ics_score = 0
        ecs_score = 0
        for j in range(len(mic_list)):
            ics_score += localMax - mic_list[j].ics
            ecs_score += mic_list[j].ecs - localMin
        total_score = ics_score + ecs_score
        if total_score > high_score:
            high_score = total_score
            globalMic = mic
    return globalMic

def printMicHeader(mic):
    print(mic.name+"(ISC="+str(round(mic.ics, 6))+", ESC="+str(round(mic.ecs, 6))+"): ",end="")

def printSystem(sys):
    for mic in sys:
        print(mic.name+":")
        for c in mic.classes:
            print("  "+c.name)
            for rel in c.outgoing_relationships:
                print("    -> "+getMicForClass(rel[0], sys).name+"."+rel[0].name+" ["+rel[1].name+"]")


clsController = Class("Controller")
clsRole = Class("Role")
clsStudents = Class("Students")
clsStudent = Class("Student")
clsAcademicStaffMembers = Class("AcademicStaffMembers")
clsAcademicStaffMember = Class("AcademicStaffMember")
clsModule = Class("Module")
clsModuleCode = Class("ModuleCode")

clsController.addRelationship((clsRole, RelationshipType.ASSOCIATION))
clsController.addRelationship((clsStudents, RelationshipType.DEPENDENCY))
clsController.addRelationship((clsAcademicStaffMembers, RelationshipType.DEPENDENCY))
clsStudent.addRelationship((clsStudents, RelationshipType.COMPOSITION))
clsAcademicStaffMember.addRelationship((clsAcademicStaffMembers, RelationshipType.COMPOSITION))
clsModule.addRelationship((clsStudent, RelationshipType.COMPOSITION))
clsModule.addRelationship((clsAcademicStaffMember, RelationshipType.COMPOSITION))
clsModuleCode.addRelationship((clsStudent, RelationshipType.COMPOSITION))
clsModuleCode.addRelationship((clsAcademicStaffMember, RelationshipType.COMPOSITION))
clsModuleCode.addRelationship((clsModule, RelationshipType.COMPOSITION))

classes = [clsController, clsRole, clsStudents, clsAcademicStaffMembers, clsAcademicStaffMember, clsStudent, clsModule, clsModuleCode]

# Threshold constants
ics_min = 0.20
ecs_min = 0.1

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
        subOptimalMic = getSubOptimal(l_tmp)
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
"""

clsCalendar = Class("Calendar")
clsAgent = Class("Agent")
clsWriter = Class("Writer")
clsReader = Class("Reader")
clsBook = Class("Book")

clsAgent.addRelationship((clsCalendar, RelationshipType.ASSOCIATION))
clsAgent.addRelationship((clsWriter, RelationshipType.ASSOCIATION))
clsBook.addRelationship((clsWriter, RelationshipType.AGGREGATION))
clsBook.addRelationship((clsReader, RelationshipType.AGGREGATION))

l = [
    Microservice([clsCalendar], None),
    Microservice([clsReader], None),
    Microservice([clsAgent], None),
    Microservice([clsWriter, clsBook], None)
]

l[0].name = "microservice1"
l[1].name = "microservice3"
l[2].name = "microservice4"
l[3].name = "microservice13"
"""
# UML Validation

strong_relationships = [RelationshipType.REALIZATION,
                        RelationshipType.INHERITANCE,
                        RelationshipType.AGGREGATION,
                        RelationshipType.COMPOSITION]
weak_relationships = [RelationshipType.ASSOCIATION,
                      RelationshipType.DEPENDENCY]

def getMicForClass(c, mics):
    for mic in mics:
        if (c in mic.classes):
            return mic
    return None

def strongValidation(c1, mics):
    mic1 = getMicForClass(c1, mics)
    other_mics = [m for m in mics if m != mic1]
    for mic in other_mics:
        for c2 in mic.classes:
            for rel in c2.outgoing_relationships:
                if (rel[0] == c1 and (rel[1] in strong_relationships)):
                    return c2
    return None

# Filtering included here, rather than in its own function
def weakValidation(c2, mics):
    failing_class = None
    mic1 = getMicForClass(c2, mics)
    other_mics = [m for m in mics if m.name != mic1.name]
    for mic in other_mics:
        for c1 in mic.classes:
            for rel in c1.outgoing_relationships:
                if (rel[0] == c2 and (rel[1] in weak_relationships)):
                    if failing_class:
                        return None
                    else:
                        failing_class = c1
    return failing_class


# Initialization
print("\n\nUML Validation\n")
printSystem(l)

st = dict()
not_st = dict()

for mic in l:
    st[mic] = []
    not_st[mic] = []

for mic in l:
    for c in mic.classes:
        failing_class = strongValidation(c, l)
        if (failing_class):
            st[mic].append(failing_class)
        elif (len(mic.classes) == 1):
            failing_class = weakValidation(c, l)
            if (failing_class):
                not_st[getMicForClass(failing_class, l)].append(c)

print("\n\n----------")
print("To copy:")
for k, v in st.items():
    if (v != []):
        for c in v:
            print("  "+getMicForClass(c,l).name+"."+c.name+" -> "+k.name)

print("\nTo move:")
for k, v in not_st.items():
    if (v != []):
        for c in v:
            print("  "+getMicForClass(c,l).name+"."+c.name+" -> "+k.name)

print("----------\n")

# Filtering is included already
"""
# Copying
for k, v in st.items():
    target_mic = k
    for c in v:
        if (c != []):
            copy_c = copy.copy(c)
            new_rels = []
            for rel in copy_c.outgoing_relationships:
                if (getMicForClass(rel[0], l) == target_mic):
                    new_rels.append(rel)
            copy_c.outgoing_relationships = new_rels

            for cx in target_mic.classes:
                for rel in cx.outgoing_relationships:
                    if (rel[0] == c):
                        rel[0] = copy_c
            
            new_rels = []
            for rel in c.outgoing_relationships:
                if (getMicForClass(rel[0], l) != target_mic):
                    new_rels.append(rel)
            c.outgoing_relationships = new_rels

            target_mic.classes.append(copy_c)
            
printSystem(l)

# Copying - deletion

to_delete = []
for mic in l:
    externally_connected = False
    for c in mic.classes:
        for rel in c.outgoing_relationships:
            if (getMicForClass(rel[0], l) != mic):
                externally_connected = True
    if (not externally_connected):
        to_delete.append(mic)

# Moving


"""