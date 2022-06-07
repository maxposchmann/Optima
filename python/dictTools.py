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

# Writes a nested dict from list of keys
def nestedDictWriter(dictionary,value,*keylist):
    currentDict = dictionary
    lastKey = ''
    for key in keylist:
        if not key:
            # If the current key is blank, the list terminated early
            currentDict[lastKey] = value
            return
        # Otherwise move down a level and continue
        if lastKey:
            currentDict = currentDict[lastKey]
        if key not in currentDict.keys():
            # If key doesn't exist, create a dict there
            currentDict[key] = dict()
        lastKey = key
    currentDict[lastKey] = value

# Deletes a key from a nested dict using list of keys
def nestedDictDeleter(dictionary,*keylist):
    currentDict = dictionary
    lastKey = ''
    # Iterate down the stack to end key
    for key in keylist:
        if not key:
            # If the current key is blank, the list terminated early
            del currentDict[lastKey]
            return
        # Otherwise move down a level and continue
        if lastKey:
            currentDict = currentDict[lastKey]
        if key not in currentDict.keys():
            # If key doesn't exist, return
            return
        lastKey = key
    del currentDict[lastKey]
