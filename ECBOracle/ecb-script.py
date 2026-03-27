from Crypto.Cipher import AES
from bs4 import BeautifulSoup
import binascii
import requests

### Variables ###

URL = "http://10.114.169.248:5000/oracle"

BLOCK_SIZE = 0

### Oracle Interface ###

def chat_to_oracle(username):
    r = requests.post(URL, data = {'username' : username})
    #Parse the response
    soup = BeautifulSoup(r.text, 'html.parser')
    #Find the encrypted text
    value = str(soup.find(id='encrypted-result').find('strong'))
    #Extract the value
    value = value.replace('<strong>', '').replace('</strong>', '')

    return value

### Calculate Block Size ###

def calculate_block_size():
    #To calculate the block size, we need to keep sending a large username value until the ciphertext length grows twice

    #Get the initial ciphertext length
    username = "A"
    original_length = len(chat_to_oracle(username))

    #Now grow the username until the length becomes larger, keeping count
    first_change_len = 1
    while (len(chat_to_oracle(username)) == original_length):
        username += "A"
        first_change_len += 1

    print ("First growth was at position: " + str(first_change_len))

    #Get the new length
    new_length = len(chat_to_oracle(username))

    #Now grow the username a second time
    second_change_len = first_change_len
    while (len(chat_to_oracle(username)) == new_length):
         username += "A"
         second_change_len += 1

    print ("Second growth was at position: " + str(second_change_len))

    #With these two values, we can now determine the block size:
    BLOCK_SIZE = second_change_len - first_change_len

    print ("BLOCK_SIZE is: " + str(BLOCK_SIZE))

    return BLOCK_SIZE

def split_ciphertext(ciphertext, block_size):
    #This helper function will take the ciphertext and split it into blocks of the known block size
    #Times two since we have two hex for each char
    block_size = block_size * 2
    chunks = [ ciphertext[i:i+block_size] for i in range(0, len(ciphertext), block_size) ]
    return chunks

### Calculate the Offset ###

def calculate_offset(block_size):
    #To calculate the offset, we will send known text for double the block size and then gradually grow the text until we get two blocks that are the same

    #Create the initial double block size buffer
    initial_text = ""
    for x in range(block_size * 2):
        initial_text += "A"

    #Send this buffer to get the initial ciphertext
    ciphertext = chat_to_oracle(initial_text)

    chunks = split_ciphertext(ciphertext, block_size)

    #Ensure that there are no duplicates already, since this would indicate that there is no offet

    if (len(chunks) != len(set(chunks))):
        print ("No offset found!")
        offset = 0
        return offset

    #If we got here, there is an offet. We will slowly add more text to the start of the username until we get a duplicate
    offset = 0
    while (len(chunks) == len(set(chunks))):
        offset += 1
        #Increment the text by one
        initial_text = "B" + initial_text

        ciphertext = chat_to_oracle(initial_text)
        chunks = split_ciphertext(ciphertext, block_size)

    #Once we exit the loop, it means we have a duplicate chunk and have determined the offset

    print ("Offset is: " + str(offset))

    return offset

### Extract information from the Oracle ###
def brute_forcer(reference_chunk, initial_text, block_size, offset):
    #Character list can be adapted if we expect other characters as well. We could have done the full 0x00 - 0xFF range, but will stay with ASCII for this attack
    charlist = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    actual_char = ''
    found = False

    for char in charlist:
        print ('Testing character: ' + str(char))
        test_text = initial_text + char

        ciphertext = chat_to_oracle(test_text)
        chunks = split_ciphertext(ciphertext, block_size)

        #Test to see if our chunk matches the reference chunk
        if (reference_chunk == chunks[1]):
            print ("Found the char: " + char)
            actual_char = char
            found = True
            break

    if found:
        return char
    else:
        return None

def extract_first_byte(block_size, offset):
    #Now that we have both the block_size and the offset, we are ready to stage our attack. We will showcase how to do this for a single bit. Then the process has to repeat.

    #To start, we will craft our initial text.
    initial_text = ""

    #First we need to take care of the offset
    for x in range(offset):
        initial_text += "B"

    #Now we want to populate the rest of the text up to the block size except for the last byte
    for x in range(block_size - 3):
        initial_text += "A"

    #Now let's chat to the oracle and get our reference chunk
    ciphertext = chat_to_oracle(initial_text)
    chunks = split_ciphertext(ciphertext, block_size)

    #Our reference chunk will be the second chunk since we have an offset
    reference_chunk = chunks[1]

    print ("Reference chunk is: " + str(reference_chunk))
    initial_text += "Or"
    print(initial_text)	
    #Now we can start the brute force
    char = brute_forcer(reference_chunk, initial_text, block_size, offset)
    return char

if __name__ == '__main__':

    #Send a message to the oracle and print the ciphertest
    print ("Testing the oracle")
    ciphertext = chat_to_oracle("SuperUser")
    print("Ciphertext for the username of SuperUser is: " + ciphertext)

    #Calculate the block size from the oracle
    print ("Calculating the block size")
    size = calculate_block_size()
    print ("Block size is: " + str(size))

    #Calculate the offset from the oracle
    print ("Calculating the offset")
    offset = calculate_offset(size)
    print ("Offset is: " + str(offset))

    #Brute force the first char
    print ("Brute forcing a single character")
    char = extract_first_byte(size, offset)








