# Method to extract values from dict measured which has parallel structure to dict validation
# measured must contain all keys that appear in validation
# Returns array values of all values in validation corresponding to endpoints in validation
def getParallelDictValues(validation,measured,values):
    if type(validation) is dict:
        # it's a dict!
        for key in validation.keys():
            # keep digging
            getParallelDictValues(validation[key],measured[key],values)
    else:
        # it's a val!
        values.append(measured)

# Method to build strings out of all keys in a nested dict
def getDictKeyString(dictionary,activeString,allStrings):
    if type(dictionary) is dict:
        # it's a dict!
        for key in dictionary.keys():
            # keep digging
            if len(activeString) > 0:
                getDictKeyString(dictionary[key],f'{activeString}: {str(key)}',allStrings)
            else:
                getDictKeyString(dictionary[key],str(key),allStrings)
    else:
        # end of keys
        allStrings.append(activeString)
