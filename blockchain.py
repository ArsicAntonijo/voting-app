# Python programm to create Blockchain

# For timestamp
import datetime

# Calculating the hash
# in order to add digital
# fingerprints to the blocks
import hashlib

# To store data
# in our blockchain
import json

# Flask is for creating the web
# app and jsonify is for
# displaying the blockchain
from flask import Flask, jsonify
from werkzeug.wrappers import response


class Blockchain:
	
	# This function is created
	# to create the very first
	# block and set it's hash to "0"
	def __init__(self):
		self.chain = []
		self.create_block(proof=1, previous_hash='0', chosen='nulti izbor')

	# This function is created
	# to add further blocks
	# into the chain
	def create_block(self, proof, previous_hash, chosen):
        
		block = {'index': len(self.chain) + 1,
				'timestamp': str(datetime.datetime.now().strftime('%x')),
				'proof': proof,
				'previous_hash': previous_hash,
                'chosen':chosen}
		self.chain.append(block)
		return block
		
	# This function is created
	# to display the previous block
	def print_previous_block(self):
		return self.chain[-1]
		
	# This is the function for proof of work
	# and used to successfully mine the block
	def valid_id(self, chain, id):
		block_index = 1
		
		while block_index < len(chain):
			block = chain[block_index]
			if block['proof'] == id:
				return False				
			
			block_index += 1
		
		return True

	def hash(self, block):
		encoded_block = json.dumps(block, sort_keys=True).encode()
		return hashlib.sha256(encoded_block).hexdigest()

	def chain_valid(self, chain):
		previous_block = chain[0]
		block_index = 1
		
		while block_index < len(chain):
			block = chain[block_index]
			if block['previous_hash'] != self.hash(previous_block):
				return False				
			
			previous_block = block
			block_index += 1
		
		return True