import operator
import sys


PredictionList = []
UniqueBranches = {}

'''Reads input file and setup PC addresses for branch prediction'''
def __predictor_setup(filepath, n):
    global PredictionList
    global UniqueBranches
    with open(filepath, 'r') as file:
        for line in file:
            temp = [x.strip() for x in line.split(',')]
            address = int(temp[0])
            bits = 1 << n
            last_n_address = address & (bits - 1) # calculate last n bits of a PC value
            new_array = [last_n_address, int(temp[1])]
            PredictionList.append(new_array)
            if (temp[0] not in UniqueBranches.keys()):
                UniqueBranches[temp[0]] = 0  # keep track of unique branch addresses


'''Least frequetly used strategy will be used when removing items from Buffers
   following implementation corresponds to a simple and naive implementation of LFU
'''
def __replace_LFU(BHTDic, AddressCountDic):
    sorted_x = sorted(AddressCountDic.items(), key=operator.itemgetter(1))
    min_ = min(sorted_x, key=operator.itemgetter(1))  # get minimum frequency from Buffer
    ut_tup = [i for i in sorted_x if i[1] == min_[1]]  # list of addresses with min frequency

    for k in ut_tup:
        BHTDic.pop(k[0], None)  # removes key from BHT
        AddressCountDic.pop(k[0], None)


'''Displays total number of branches'''
def __get_total_branches():
    global PredictionList
    print ("Total no of branches: ", len(PredictionList))

'''Displays total unique number of branches'''
def __get_unique_branches():
    global UniqueBranches
    print ("No of unique branches: ", len(UniqueBranches))

'''Displays Mis=prediction Rate'''
def __missPredictionRate(total_b , miss_b):
    print ("Mis-prediction rate: ",miss_b/float(total_b))


'''Default value of predict not-taken
    0 --> Not Taken
    1 --> Taken
'''
# 8,192 entry Branch History Table (BHT)
# total number of addresses being kept track = 8192
# at a BHT buffer overflow, it will remove least frequently used addresses
def __BHT_predictor():
    correctPredictions = 0
    incorrectPredictions = 0
    BHTDic = {}
    AddressCountDic = {}

    for address in PredictionList:
        if address[0] in BHTDic.keys():
            prediction = BHTDic[address[0]]
            AddressCountDic[address[0]] = AddressCountDic[address[0]] + 1  # increment count
        else:
            if (len(BHTDic) == 8192):
                __replace_LFU(BHTDic, AddressCountDic)  # remove least recently used from buffer
            prediction = 0  # predict not-taken
            BHTDic[address[0]] = address[1]
            AddressCountDic[address[0]] = 1  # keep track of new address
        if (prediction != address[1]):
            incorrectPredictions += 1
            BHTDic[address[0]] = address[1]
        else:
            correctPredictions += 1

    __get_total_branches()
    __get_unique_branches()
    print ("No of branches correctly predicted: ", correctPredictions)
    print ("No of branches incorrectly predicted: ", incorrectPredictions)
    __missPredictionRate(len(PredictionList),incorrectPredictions)


'''Default value of predict not-taken
    0 --> Not Taken
    1 --> Taken
'''
# 4096 entry Branch History Table (BHT)
# total number of addresses being kept track = 4096
# at a BHT buffer overflow, it will remove least frequently used addresses
def __2_bit_predictor():
    correctPredictions = 0
    incorrectPredictions = 0
    BHTDic = {}
    AddressCountDic = {}

    for k in PredictionList:
        address = k[0]
        actual = k[1]
        if address in BHTDic.keys():
            _bit_prediction = BHTDic[address]
            AddressCountDic[address] = AddressCountDic[address] + 1  # increment count
        else:
            if (len(BHTDic) == 4096):
                __replace_LFU(BHTDic, AddressCountDic)  # remove least recently used from buffer
            _bit_prediction = 0  # predict not-taken
            BHTDic[address] = 0
            AddressCountDic[address] = 1  # keep track of new address
        if _bit_prediction == 0 or _bit_prediction == 1:    # corresponds to 2-bit counter states
            prediction = 0
        elif _bit_prediction == 2 or _bit_prediction == 3:
            prediction = 1

        if actual != prediction:
            incorrectPredictions += 1
            if actual == 1:
                if _bit_prediction == 0:    # update state
                    BHTDic[address] = 1
                elif _bit_prediction == 1:
                    BHTDic[address] = 3
            elif actual == 0:
                if _bit_prediction == 2:
                    BHTDic[address] = 0
                elif _bit_prediction == 3:
                    BHTDic[address] = 2
        else:
            correctPredictions += 1
            if actual == 1:
                if _bit_prediction == 2:
                    BHTDic[address] = 3
            elif actual == 0:
                if _bit_prediction == 1:
                    BHTDic[address] = 0

    __get_total_branches()
    __get_unique_branches()
    print ("No of branches correctly predicted: ", correctPredictions)
    print ("No of branches incorrectly predicted: ", incorrectPredictions)
    __missPredictionRate(len(PredictionList),incorrectPredictions)


'''Default value of predict not-taken
    0 --> Not Taken
    1 --> Taken
Keeps track of global branch access pattern of 2 branches in a global register
'''
# 4, 2-bit  entry Branch History Tables (BHT)
# total number of addresses being kept track = 1024
# at a BHT buffer overflow, it will remove least frequently used addresses

def __correlatedPredictor():
    correctPredictions = 0
    incorrectPredictions = 0
    BHTDic = {}
    AddressCountDic = {}
    global_history = 0          # global pattern register representation

    for k in PredictionList:
        address = k[0]
        actual = k[1]
        prediction_index = global_history

        if address in BHTDic.keys():
            _bit_prediction = BHTDic[address][prediction_index]
        else:
            if (len(BHTDic) == 1024):
                __replace_LFU(BHTDic, AddressCountDic)
            BHTDic[address] = [0, 0, 0, 0]
            _bit_prediction = 0

        if _bit_prediction == 0 or _bit_prediction == 1:    # states of the 2 bit predictor
            prediction = 0
        elif _bit_prediction == 2 or _bit_prediction == 3:
            prediction = 1

        # move global history
        shift = global_history >> 1             # update global history register for prediction
        if actual:
            global_history = shift | 2
        else:
            global_history = shift | 0

        if actual != prediction:
            incorrectPredictions += 1
            if actual == 1:
                if _bit_prediction == 0:
                    temp = BHTDic[address]
                    temp[prediction_index] = 1
                    BHTDic[address] = temp

                elif _bit_prediction == 1:
                    temp = BHTDic[address]
                    temp[prediction_index] = 3
                    BHTDic[address] = temp
            elif actual == 0:
                if _bit_prediction == 2:
                    temp = BHTDic[address]
                    temp[prediction_index] = 0
                    BHTDic[address] = temp

                elif _bit_prediction == 3:
                    temp = BHTDic[address]
                    temp[prediction_index] = 2
                    BHTDic[address] = temp
        else:
            correctPredictions += 1
            if actual == 1:
                if _bit_prediction == 2:
                    temp = BHTDic[address]
                    temp[prediction_index] = 3
                    BHTDic[address] = temp

            elif actual == 0:
                if _bit_prediction == 1:
                    temp = BHTDic[address]
                    temp[prediction_index] = 0
                    BHTDic[address] = temp

    __get_total_branches()
    __get_unique_branches()
    print ("No of branches correctly predicted: ", correctPredictions)
    print ("No of branches incorrectly predicted: ", incorrectPredictions)
    __missPredictionRate(len(PredictionList),incorrectPredictions)


'''Implement branch predictor combining two branch predictors
combining 2 bit branch predictor with co-related branch predictor

    2 bit counter will keep track of 1024 entries --> local predictor --> predictor 1
    (2,2) counter will keep track of 1024 entries --> global predictor --> predictor 2

    predictor 1 will be chosen for values 3 or 4 or 5 of the meta register
    predictor 2 will be chosen for values 0 or 1 or 2 of the meta register
    for each predictions predictor will be chosen by a value in a meta register
    meta register value - 3,4,5 -> Predictor 1
    meta register value - 0,1,2 -> Predictor 2
    
    for each prediction and miss prediction both predictors are updated
    
    Meta register will be updates as follows
    Predictor 1     Predictor 2    Update to Selector
    correct         correct         no change
    correct         incorrect       increment
    incorrect       correct         decrement
    incorrect       incorrect        no change

    2 bit counter state transition is changed where
    01 state --1--> 10 state
    10 state --0--> 01 state
'''
def __custom_predictor():
    correctPredictions =0
    incorrectPredictions = 0

    localPredictor = {}
    globalPredictor = {}
    global_history = 0
    select_state = 0  # representation of meta register

    for k in PredictionList:
        address = k[0]
        actual = k[1]

        prediction_index = global_history

        if address in localPredictor.keys():
            local_bit_prediction = localPredictor[address]

            if local_bit_prediction == 0 or local_bit_prediction == 1:
                localPrediction = 0
            elif local_bit_prediction == 2 or local_bit_prediction == 3:
                localPrediction = 1

        else:
            localPrediction = 0  # default prediction
            localPredictor[address] = 0
            local_bit_prediction = 0

        if address in globalPredictor.keys():
            global_bit_prediction = globalPredictor[address][prediction_index]

            if global_bit_prediction == 0 or global_bit_prediction == 1:
                globalPrediction = 0
            elif global_bit_prediction == 2 or global_bit_prediction == 3:
                globalPrediction = 1
        else:
            globalPrediction = 0  # default prediction for global predictor
            global_bit_prediction = 0
            temp = [0, 0, 0, 0]
            globalPredictor[address] = temp

        # move global history , 2 bit branch history being kept
        shift = global_history >> 1
        if actual:
            global_history = shift | 2
        else:
            global_history = shift | 0

        if select_state == 3 or select_state == 4 or select_state == 5:  # predictor 1
            if actual == localPrediction:
                correctPredictions += 1
                if actual == 1:
                    if local_bit_prediction == 2:
                        localPredictor[address] = 3

                elif actual == 0:
                    if local_bit_prediction == 1:
                        localPredictor[address] = 0

                if localPrediction != globalPrediction:
                    if select_state == 3:
                        select_state = 4
                    elif select_state == 3:
                        select_state = 5

            else:
                incorrectPredictions += 1
                if actual == 1:
                    if local_bit_prediction == 0:
                        localPredictor[address] = 1
                    elif local_bit_prediction == 1:
                        localPredictor[address] = 2 #3
                elif actual == 0:
                    if local_bit_prediction == 2:
                        localPredictor[address] = 1 #0
                    elif local_bit_prediction == 3:
                        localPredictor[address] = 2

                if localPrediction != globalPrediction:
                    #if select_state == 3:
                    select_state -= 1

            ##################################  update global predictor ##########################################
            if actual == globalPrediction:
                if actual == 1:
                    if global_bit_prediction == 2:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 3
                        globalPredictor[address] = temp

                elif actual == 0:
                    if global_bit_prediction == 1:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 0
                        globalPredictor[address] = temp

            else:
                if actual == 1:
                    if global_bit_prediction == 0:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 1
                        globalPredictor[address] = temp

                    elif global_bit_prediction == 1:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 2 #3
                        globalPredictor[address] = temp

                elif actual == 0:
                    if global_bit_prediction == 2:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 1 #0
                        globalPredictor[address] = temp

                    elif global_bit_prediction == 3:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 2
                        globalPredictor[address] = temp

        #################################################################

        elif select_state == 0 or select_state == 1 or  select_state == 2 :    # global predictor
            if actual == globalPrediction:
                correctPredictions += 1
                if actual == 1:
                    if global_bit_prediction == 2:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 3
                        globalPredictor[address] = temp

                elif actual == 0:
                    if global_bit_prediction == 1:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 0
                        globalPredictor[address] = temp

                if localPrediction != globalPrediction:
                    if select_state == 1:
                        select_state = 0
                    elif select_state == 2:
                        select_state = 1

            else:
                incorrectPredictions += 1
                if actual == 1:
                    if global_bit_prediction == 0:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 1
                        globalPredictor[address] = temp

                    elif global_bit_prediction == 1:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 2 #3
                        globalPredictor[address] = temp

                elif actual == 0:
                    if global_bit_prediction == 2:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 1 #0
                        globalPredictor[address] = temp

                    elif global_bit_prediction == 3:
                        temp = globalPredictor[address]
                        temp[prediction_index] = 2
                        globalPredictor[address] = temp

                if globalPrediction != localPrediction:
                    #if select_state == 0:
                    select_state += 1

        #############################update local predictor ###########################################
            if actual == localPrediction:
                if actual == 1:
                    if local_bit_prediction == 2:
                        localPredictor[address] = 3

                elif actual == 0:
                    if local_bit_prediction == 1:
                        localPredictor[address] = 0

            else:
                if actual == 1:
                    if local_bit_prediction == 0:
                        localPredictor[address] = 1
                    elif local_bit_prediction == 1:
                        localPredictor[address] = 2  # 3
                elif actual == 0:
                    if local_bit_prediction == 2:
                        localPredictor[address] = 1  # 0
                    elif local_bit_prediction == 3:
                        localPredictor[address] = 2
        ################################################################################

    __get_total_branches()
    __get_unique_branches()
    print ("No of branches correctly predicted: ", correctPredictions)
    print ("No of branches incorrectly predicted: ", incorrectPredictions)
    __missPredictionRate(len(PredictionList),incorrectPredictions)


branch_predictor = int(sys.argv[1])
filename = str(sys.argv[2])

if branch_predictor == 1:
    print("=============================== 1 Bit Branch Predictor =========================")
    __predictor_setup(filename,13)
    __BHT_predictor()

elif branch_predictor == 2:
    print("=============================== 2 Bit Branch Predictor =========================")
    __predictor_setup(filename, 12)
    __2_bit_predictor()


elif branch_predictor == 3:
    print("=============================== (2,2)  Branch Predictor =========================")
    __predictor_setup(filename, 10)
    __correlatedPredictor()


elif branch_predictor == 4:
    print("=============================== Custom  Branch Predictor =========================")
    __predictor_setup(filename, 10)
    __custom_predictor()
