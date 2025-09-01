#!/usr/bin/env python3
"""
Voting Management System on a Simple Blockchain (Menu-driven Console App)

Features:
- Add Candidate (unique candidate_id)
- Add Voter (unique voter_id)
- Cast Vote (one vote per voter, to any candidate)
- Print Blockchain (blocks, transactions, hashes)
- Validate Chain (integrity + PoW)
- Exit

Implementation notes:
- Each vote is recorded as a single-transaction block, mined with simple proof-of-work.
- Duplicate IDs and double-voting are prevented.
- Clean, readable CLI with basic input validation.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import hashlib
import json
import time
from datetime import datetime

# =============== Domain Entities ===============
@dataclass
class Voter:
    voter_id: str
    name: str
    has_voted: bool = False

@dataclass
class Candidate:
    candidate_id: str
    name: str

@dataclass
class Transaction:
    voter_id: str
    candidate_id: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "candidate_id": self.candidate_id,
            "timestamp": self.timestamp,
        }

# =============== Blockchain ===============
@dataclass
class Block:
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        # Use a stable JSON representation for hashing
        block_dict = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [t.to_dict() for t in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self, difficulty: int = 3):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self) -> None:
        genesis = Block(index=0, timestamp=time.time(), transactions=[], previous_hash="0")
        # Mine genesis for consistency
        self.mine_block(genesis)
        self.chain.append(genesis)

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block) -> None:
        block.previous_hash = self.last_block.hash
        self.mine_block(block)
        self.chain.append(block)

    def mine_block(self, block: Block) -> None:
        prefix = "0" * self.difficulty
        # Iterate nonce until hash satisfies difficulty
        while True:
            computed_hash = block.compute_hash()
            if computed_hash.startswith(prefix):
                block.hash = computed_hash
                return
            block.nonce += 1

    def is_chain_valid(self) -> bool:
        prefix = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            # Validate linkage
            if current.previous_hash != previous.hash:
                return False
            # Validate hash
            if current.compute_hash() != current.hash:
                return False
            # Validate PoW
            if not current.hash.startswith(prefix):
                return False
        # Optional: validate genesis too
        genesis = self.chain[0]
        if genesis.compute_hash() != genesis.hash or not genesis.hash.startswith(prefix):
            return False
        return True

# =============== Application (Menu-driven) ===============
class VotingApp:
    def __init__(self):
        self.voters: Dict[str, Voter] = {}
        self.candidates: Dict[str, Candidate] = {}
        self.blockchain = Blockchain(difficulty=3)

    # ---- Helpers ----
    @staticmethod
    def clean_id(id_str: str) -> str:
        return id_str.strip()

    @staticmethod
    def now_ts() -> float:
        return time.time()

    @staticmethod
    def fmt_ts(ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    def add_candidate(self) -> None:
        print("\n=== Add Candidate ===")
        candidate_id = self.clean_id(input("Enter candidate ID: "))
        if not candidate_id:
            print("! Candidate ID cannot be empty.")
            return
        if candidate_id in self.candidates:
            print("! Duplicate candidate ID. Choose another.")
            return
        name = input("Enter candidate name: ").strip()
        if not name:
            print("! Candidate name cannot be empty.")
            return
        self.candidates[candidate_id] = Candidate(candidate_id, name)
        print(f"✓ Candidate added: {candidate_id} — {name}")

    def add_voter(self) -> None:
        print("\n=== Add Voter ===")
        voter_id = self.clean_id(input("Enter voter ID: "))
        if not voter_id:
            print("! Voter ID cannot be empty.")
            return
        if voter_id in self.voters:
            print("! Duplicate voter ID. Choose another.")
            return
        name = input("Enter voter name: ").strip()
        if not name:
            print("! Voter name cannot be empty.")
            return
        self.voters[voter_id] = Voter(voter_id, name, has_voted=False)
        print(f"✓ Voter added: {voter_id} — {name}")

    def cast_vote(self) -> None:
        print("\n=== Cast Vote ===")
        if not self.voters:
            print("! No voters registered. Add voters first.")
            return
        if not self.candidates:
            print("! No candidates registered. Add candidates first.")
            return

        voter_id = self.clean_id(input("Enter your voter ID: "))
        if voter_id not in self.voters:
            print("! Voter not found.")
            return
        voter = self.voters[voter_id]
        if voter.has_voted:
            print("! This voter has already voted. Double-voting is not allowed.")
            return

        print("Available candidates:")
        for cid, c in self.candidates.items():
            print(f"  - {cid}: {c.name}")
        candidate_id = self.clean_id(input("Enter candidate ID to vote for: "))
        if candidate_id not in self.candidates:
            print("! Candidate not found.")
            return

        # Create transaction and mine as a new block
        tx = Transaction(voter_id=voter_id, candidate_id=candidate_id, timestamp=self.now_ts())
        new_block = Block(
            index=len(self.blockchain.chain),
            timestamp=self.now_ts(),
            transactions=[tx],
            previous_hash=self.blockchain.last_block.hash,
        )
        self.blockchain.add_block(new_block)
        voter.has_voted = True
        print(f"✓ Vote cast: {voter.name} -> {self.candidates[candidate_id].name}")
        print(f"  Block #{new_block.index} mined with hash: {new_block.hash}")

    def print_blockchain(self) -> None:
        print("\n=== Blockchain Contents ===")
        for block in self.blockchain.chain:
            ts = self.fmt_ts(block.timestamp)
            print(f"\nBlock #{block.index}")
            print(f"Timestamp     : {ts}")
            print(f"Previous Hash : {block.previous_hash}")
            print(f"Nonce         : {block.nonce}")
            print(f"Hash          : {block.hash}")
            if block.transactions:
                print("Transactions:")
                for t in block.transactions:
                    print(f"  - voter_id={t.voter_id}, candidate_id={t.candidate_id}, time={self.fmt_ts(t.timestamp)}")
            else:
                print("Transactions: (none – genesis block)")

    def validate_chain(self) -> None:
        print("\n=== Validate Chain ===")
        if self.blockchain.is_chain_valid():
            print("✓ Blockchain is VALID.")
        else:
            print("✗ Blockchain is INVALID!")

    def menu(self) -> None:
        while True:
            print("\n============================")
            print(" Voting Management System ")
            print("============================")
            print("1. Add Candidate")
            print("2. Add Voter")
            print("3. Cast Vote")
            print("4. Print Blockchain")
            print("5. Validate Chain")
            print("6. Exit")
            choice = input("Choose an option (1-6): ").strip()

            if choice == "1":
                self.add_candidate()
            elif choice == "2":
                self.add_voter()
            elif choice == "3":
                self.cast_vote()
            elif choice == "4":
                self.print_blockchain()
            elif choice == "5":
                self.validate_chain()
            elif choice == "6":
                print("Goodbye!")
                break
            else:
                print("! Invalid choice. Please enter a number between 1 and 6.")


def main():
    app = VotingApp()
    app.menu()

if __name__ == "__main__":
    main()
