import hashlib
import psycopg2
from typing import List, Dict, Optional
from bisect import bisect_right

DEBUG = True

class SimpleHashShardRouter:
    def __init__(self, shard_configs: List[Dict[str, str]]):
        self.shards = shard_configs
        self.num_shards = len(shard_configs)
        self.connections = {}
        print(f"✅ Router iniciado con {self.num_shards} shards")
    
    def _get_shard_index(self, key: str) -> int:
        hash_value = int(hashlib.md5(key.encode()).hexdigest(), 16)
        return hash_value % self.num_shards
    
    def get_connection(self, key: str, is_write: bool = False):
        shard_idx = self._get_shard_index(key)
        shard_config = self.shards[shard_idx]
        conn_key = f"{shard_idx}-{'w' if is_write else 'r'}"
        
        if conn_key not in self.connections:
            host = shard_config['host']
            port = shard_config['port']
            try:
                self.connections[conn_key] = psycopg2.connect(
                    host=host, port=port, database=shard_config['database'],
                    user=shard_config['user'], password=shard_config['password']
                )
            except Exception as e:
                print(f"❌ Error conectando a shard {shard_idx}: {e}")
                raise
        return self.connections[conn_key]
    
    def insert_user(self, user_id: str, name: str, email: str) -> bool:
        shard_idx = self._get_shard_index(user_id)
        try:
            conn = self.get_connection(user_id, is_write=True)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (user_id, name, email) VALUES (%s, %s, %s)", (user_id, name, email))
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"❌ Error insertando usuario {user_id}: {e}")
            return False

    def get_shard_distribution(self, user_ids: List[str]) -> Dict[int, int]:
        distribution = {i: 0 for i in range(self.num_shards)}
        for user_id in user_ids:
            shard_idx = self._get_shard_index(user_id)
            distribution[shard_idx] += 1
        return distribution

    def simulate_rebalance(self, user_ids: List[str], new_num_shards: int) -> int:
        moves = 0
        for user_id in user_ids:
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            if (hash_val % self.num_shards) != (hash_val % new_num_shards):
                moves += 1
        return moves
        
    def close_all(self):
        for conn in self.connections.values(): conn.close()

class ConsistentHashRouter:
    def __init__(self, shard_configs: List[Dict[str, str]], virtual_nodes=150):
        self.shards = shard_configs
        self.virtual_nodes = virtual_nodes
        self.ring = []
        self.ring_map = {}
        self._build_ring()

    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def _build_ring(self):
        for shard_idx, shard in enumerate(self.shards):
            for vnode in range(self.virtual_nodes):
                key = f"{shard['host']}:{shard['port']}:vnode{vnode}"
                h = self._hash(key)
                self.ring.append(h)
                self.ring_map[h] = shard_idx
        self.ring.sort()
    
    def _get_shard_index(self, key: str) -> int:
        if not self.ring: return 0
        h = self._hash(key)
        idx = bisect_right(self.ring, h)
        if idx == len(self.ring): idx = 0
        return self.ring_map[self.ring[idx]]

    def get_shard_distribution(self, user_ids: List[str]) -> Dict[int, int]:
        distribution = {i: 0 for i in range(len(self.shards))}
        for user_id in user_ids:
            shard_idx = self._get_shard_index(user_id)
            distribution[shard_idx] += 1
        return distribution

    def simulate_add_shard(self, user_ids: List[str]) -> int:
        new_configs = self.shards + [{'host': 'new', 'port': 0}]
        new_router = ConsistentHashRouter(new_configs, self.virtual_nodes)
        moves = 0
        for user_id in user_ids:
            if self._get_shard_index(user_id) != new_router._get_shard_index(user_id):
                moves += 1
        return moves
