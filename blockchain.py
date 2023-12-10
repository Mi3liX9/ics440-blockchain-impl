import base64
import sys

import hashlib
import json
import rsa

from time import time
from uuid import uuid4


from flask import Flask, jsonify, request

# -------------------------------
import requests
from urllib.parse import urlparse
# -------------------------------

class Blockchain(object):
    
    difficulty_target = "0000"
    difficulty = 0.1
    def encrypt_amount(self, amount, key):
        # Encrypts the amount using additive shift cipher
        encrypted_amount = (amount + key) % 1000000 
        return encrypted_amount

    def decrypt_amount(self, encrypted_amount, key):
        # Decrypts the amount
        decrypted_amount = (encrypted_amount - key) % 1000000  # Ensure the amount wraps around
        return decrypted_amount

    def hash_block(self, block):        
        # encode the block into bytes and then hashes it; 
        # ensure that the dictionary is sorted, or you'll have inconsistent hashes
        block_encoded = json.dumps(block, sort_keys=True).encode()        
        return hashlib.sha256(block_encoded).hexdigest()

    def __init__(self):
        # stores all the blocks in the entire blockchain
        self.chain = []

        # temporarily stores the transactions for the current block
        self.current_transactions = []
                
        # create the genesis block with a specific fixed hash of previous block
        # genesis block starts with index 0
        genesis_hash = self.hash_block("genesis_block") 
        self.append_block(
            hash_of_previous_block = genesis_hash, 
            nonce = self.proof_of_work(0, genesis_hash, [])
        )
        #------------
        self.nodes = set()
        #------------


    def encrypt_rail_fence(self, text, key):
        rail = [['\n' for i in range(len(text))]
                    for j in range(key)]
        
        # to find the direction
        dir_down = False
        row, col = 0, 0
        
        for i in range(len(text)):
            if (row == 0) or (row == key - 1):
                dir_down = not dir_down
            
            # fill the corresponding alphabet
            rail[row][col] = text[i]
            col += 1
            
            # find the next row using
            # direction flag
            if dir_down:
                row += 1
            else:
                row -= 1
    
        result = []
        for i in range(key):
            for j in range(len(text)):
                if rail[i][j] != '\n':
                    result.append(rail[i][j])
        return("" . join(result))

    def decryptRailFence(self, cipher, key):
     
        rail = [['\n' for i in range(len(cipher))]
                    for j in range(key)]
        
        # to find the direction
        dir_down = None
        row, col = 0, 0
        
        # mark the places with '*'
        for i in range(len(cipher)):
            if row == 0:
                dir_down = True
            if row == key - 1:
                dir_down = False
            
            # place the marker
            rail[row][col] = '*'
            col += 1
            
            # find the next row
            # using direction flag
            if dir_down:
                row += 1
            else:
                row -= 1
                
        # now we can construct the
        # fill the rail matrix
        index = 0
        for i in range(key):
            for j in range(len(cipher)):
                if ((rail[i][j] == '*') and
                (index < len(cipher))):
                    rail[i][j] = cipher[index]
                    index += 1
            
        # now read the matrix in
        # zig-zag manner to construct
        # the resultant text
        result = []
        row, col = 0, 0
        for i in range(len(cipher)):
            
            # check the direction of flow
            if row == 0:
                dir_down = True
            if row == key-1:
                dir_down = False
                
            # place the marker
            if (rail[row][col] != '*'):
                result.append(rail[row][col])
                col += 1
                
            # find the next row using
            # direction flag
            if dir_down:
                row += 1
            else:
                row -= 1
        return("".join(result))

    # use PoW to find the nonce for the current block
    def proof_of_work(self, index, hash_of_previous_block, transactions):
        # try with nonce = 0
        nonce = 0

        # try hashing the nonce together with the hash of the previous block 
        # until it is valid
        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1

        return nonce

    # check if the block's hash meets the difficulty target    
    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):

        # create a string containing the hash of the previous block 
        # and the block content, including the nonce
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()        

        # hash using sha256
        content_hash = hashlib.sha256(content).hexdigest()

        # check if the hash meets the difficulty target
        # return content_hash[:len(self.difficulty_target)] == self.difficulty_target
        # convert hash to a large integer
        content_hash_int = int(content_hash, 16)

        # calculate the maximum value from the difficulty level
        max_value = int(1 / self.difficulty)

        # check if the hash integer is less than the max value
        return content_hash_int < max_value

    # creates a new block and adds it to the blockchain
    def append_block(self, nonce, hash_of_previous_block):
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }

        # reset the current list of transactions
        self.current_transactions = []

        # add the new block to the blockchain
        self.chain.append(block)
        return block

    def add_transaction(self, sender, recipient, amount, key):
        # adds a new transaction to the current list of transactions
        encrypted_amount = self.encrypt_amount(amount, key)

        self.current_transactions.append({
            'amount': encrypted_amount,            
            'recipient': recipient,
            'sender': sender,
        })
        # get the index of the last block in the blockchain and add one to it
        # this will be the block that the current transaction will be added to
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # returns the last block in the blockchain
        return self.chain[-1]

    # --------------------
    # add a new node to the list of nodes e.g. 'http://192.168.0.5:5000'
    def add_node(self, address, key):        
        parsed_url = urlparse(address)
        node = (parsed_url.netloc, key)
        self.nodes.add(node)

    # determine if a given blockchain is valid      
    def valid_chain(self, chain):

        last_block = chain[0]   # the genesis block
        current_index = 1       # starts with the second block

        while current_index < len(chain):
            # get the current block 
            block = chain[current_index]  

            # check that the hash of the previous block is correct by 
            # hashing the previous block and then comparing it with the one 
            # recorded in the current block
            if block['hash_of_previous_block'] != self.hash_block(last_block):                 
                return False

            # check that the nonce is correct by hashing the hash of the 
            # previous block together with the nonce and see if it matches
            # the target
            if not self.valid_proof(
                current_index, 
                block['hash_of_previous_block'], 
                block['transactions'], 
                block['nonce']):                
                return False

            # move on to the next block on the chain
            last_block = block
            current_index += 1

        # the chain is valid
        return True

    def update_blockchain(self):
        # get the nodes around us that has been registered
        neighbours = self.nodes
        new_chain = None

        # for simplicity, look for chains longer than ours
        max_length = len(self.chain)

        # grab and verify the chains from all the nodes in our network
        for node in neighbours:            
            # get the blockchain from the other nodes
            response = requests.get(f'http://{node[0]}/blockchain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # replace our chain if we discovered a new, valid chain longer than 
        # ours
        if new_chain:
            self.chain = new_chain
            return True

        return False


    def getConnectedNodes(self):
        return self.nodes

    #this method gets all transactions in the blockchain
    def show_transactions(self):

        transactions = []

        for block in self.chain:
            transactions.extend(block['transactions'])

        return transactions

    def verify(self, data, sign, pubKey):
        sign = base64.b64decode(sign)
        result = False
        try:
            rsa.verify(data.encode(), sign, pubKey)
        except rsa.pkcs1.VerificationError:
            result = False
        else:
            result = True
        return result    

    def getLastTransaction(self):
        amount = self.current_transactions[0]['amount']
        return amount


    # --------------------

app = Flask(__name__)

key = 5

# generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# instantiate the Blockchain
blockchain = Blockchain()

# generate random public and private keys
public, private = rsa.newkeys(1024)
public_key = rsa.PublicKey.load_pkcs1(public.save_pkcs1("PEM"))  #public.save_pkcs1("PEM")
__private_key__ = rsa.PrivateKey.load_pkcs1(private.save_pkcs1("PEM"))  #private.save_pkcs1("PEM")

# return the entire blockchain
@app.route('/blockchain', methods=['GET'])
def full_chain():    
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/mine', methods=['GET'])
def mine_block():

    # get the last transaction under the assumption that only one transaction per block
    last_transaction_amount = f'{blockchain.getLastTransaction()}'.split(',')
    # decrypt the amount using rail fence
    decrypted_amount = blockchain.decryptRailFence(last_transaction_amount[0], 2)
    # print(last_transaction_amount[0])

    # the miner now receive 10% of the only transaction in the block.
    blockchain.add_transaction(
        sender="0",
        recipient=node_identifier,
        amount= float(decrypted_amount)*0.1,
        key=key
    )

    # obtain the hash of last block in the blockchain 
    last_block_hash = blockchain.hash_block(blockchain.last_block)

    # using PoW, get the nonce for the new block to be added to the blockchain
    index = len(blockchain.chain) 
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transactions)

    # add the new block to the blockchain using the last block hash and the 
    # current nonce
    block = blockchain.append_block(nonce, last_block_hash)

    nodes = blockchain.getConnectedNodes()

    urls = []
    for node in nodes:
        urls.append(node[0])

    currentUrl = {"nodes": [f'http://{request.host}']}
    print(currentUrl)

    for url in urls:
        requests.post(f'http://{url}/nodes/add_nodes', json= currentUrl)
        requests.get(f'http://{url}/nodes/sync')

    response = {
        'message': "New Block Mined",
        'index': block['index'],                
        'hash_of_previous_block': block['hash_of_previous_block'], 
        'nonce': block['nonce'],
        'transactions': block['transactions'],        
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # get the value passed in from the client 
    values = request.get_json()

    # check that the required fields are in the POST'ed data
    required_fields = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required_fields):
        return ('Missing fields', 400)

    # print(values["amount"])
    rail_fence_amount = blockchain.encrypt_rail_fence(f'{values["amount"]}', 2)
    signature = rsa.sign(f'{values["amount"]}'.encode(), __private_key__, "SHA-256")
    str_signature = base64.b64encode(signature).decode('utf8')

    # print(rail_fence_amount)
    # print(str_signature)
    newAmount = f'{rail_fence_amount}'+","+f'{str_signature}'

    # create a new transaction
    index = blockchain.add_transaction(
        values['sender'], 
        values['recipient'], 
        newAmount,
        key=key
    )

    response = {'message': f'Transaction will be added to Block {index}'}
    return (jsonify(response), 201)

# --------------
@app.route('/nodes/add_nodes', methods=['POST'])
def add_nodes():
    # get the nodes passed in from the client 
    values = request.get_json()    
    nodes = values.get('nodes')  

    if nodes is None:
        return "Error: Missing node(s) info", 400

    for node in nodes:
        value = requests.get(f'{node}/getPublicKey')
        public_k = value.json()["public_key"]

        if public_k:
            blockchain.add_node(node, public_k)
    
    print(list(blockchain.nodes))    

    response = {
        'message': 'New nodes added',
        'nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route('/nodes/get_nodes', methods=['GET'])
def get_nodes():
    # get the nodes 
    if list(blockchain.nodes).count == 0 :
        response = {
            'message': 'No Nodes',
            'nodes': list(blockchain.nodes),
        }
    else :
        response = {
        'message': 'Current nodes',
        'nodes': list(blockchain.nodes),
        }

    return jsonify(response), 201


@app.route('/nodes/sync', methods=['GET'])
def sync():
    updated = blockchain.update_blockchain()
    if updated:
        response = {
            'message': 'The blockchain has been updated to the latest',
            'blockchain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our blockchain is the latest',
            'blockchain': blockchain.chain
        }
    return jsonify(response), 200

@app.route('/getPublicKey', methods=['GET'])
def getPublicKey():
    return jsonify({"public_key": public_key.__str__()}), 200

@app.route("/transactions/get_transactions", methods=['GET'])
def getTransactions():
    transactions = blockchain.show_transactions()
    newTr = []

    for transaction in transactions:
        # Split the amount and the signature
        encrypted_amount, signature = str(transaction['amount']).split(',')

        # Decrypt the amount
        decrypted_amount = blockchain.decrypt_amount(int(encrypted_amount), key) 

        # Verify the decrypted amount
        is_verified = blockchain.verify(str(decrypted_amount), signature, public_key)

        # Construct a new transaction object with decrypted and verified amount
        new_transaction = {
            'amount': f"{decrypted_amount}, verified: {is_verified}",
            'recipient': transaction['recipient'],
            'sender': transaction['sender']
        }
        newTr.append(new_transaction)

    return jsonify(newTr), 200


# --------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(sys.argv[1]))
