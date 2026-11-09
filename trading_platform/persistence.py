"""Repository protocol and versioned SQLite persistence adapter."""
from pathlib import Path
from typing import Protocol, Any
import sqlite3, json
from trading_platform.metadata import *

SCHEMA_VERSION=1
SCHEMAS={
"network":("networks",Network,("name","chain_id","network_type","native_currency","rpc_config_ref","status","metadata"),"name TEXT NOT NULL,chain_id INTEGER NOT NULL UNIQUE,network_type TEXT NOT NULL,native_currency TEXT NOT NULL,rpc_config_ref TEXT,status TEXT NOT NULL,metadata TEXT NOT NULL"),
"abi":("abis",ABI,("name","version","format","definition","checksum","metadata"),"name TEXT NOT NULL,version TEXT NOT NULL,format TEXT NOT NULL,definition TEXT NOT NULL,checksum TEXT,metadata TEXT NOT NULL"),
"contract":("contracts",Contract,("name","network_id","address","contract_type","abi_id","metadata"),"name TEXT NOT NULL,network_id TEXT NOT NULL REFERENCES networks(id) ON DELETE RESTRICT,address TEXT NOT NULL,contract_type TEXT NOT NULL,abi_id TEXT REFERENCES abis(id) ON DELETE RESTRICT,metadata TEXT NOT NULL,UNIQUE(network_id,address)"),
"token":("tokens",Token,("name","symbol","network_id","contract_id","decimals","standard","metadata"),"name TEXT NOT NULL,symbol TEXT NOT NULL,network_id TEXT NOT NULL REFERENCES networks(id) ON DELETE RESTRICT,contract_id TEXT REFERENCES contracts(id) ON DELETE RESTRICT,decimals INTEGER NOT NULL,standard TEXT NOT NULL,metadata TEXT NOT NULL"),
"asset":("assets",Asset,("name","symbol","asset_type","description","metadata"),"name TEXT NOT NULL,symbol TEXT NOT NULL,asset_type TEXT NOT NULL,description TEXT,metadata TEXT NOT NULL"),
"pair":("trading_pairs",TradingPair,("base_asset_id","quote_asset_id","symbol","metadata"),"base_asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE RESTRICT,quote_asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE RESTRICT,symbol TEXT,metadata TEXT NOT NULL,UNIQUE(base_asset_id,quote_asset_id)"),
"venue":("venues",TradingVenue,("name","venue_type","provider","status","metadata"),"name TEXT NOT NULL,venue_type TEXT NOT NULL,provider TEXT,status TEXT NOT NULL,metadata TEXT NOT NULL"),
"market":("markets",Market,("name","venue_id","pair_id","market_type","provider_market_id","network_id","liquidity_pool","pool_contract_id","pool_fee_tier","constraints","metadata"),"name TEXT NOT NULL,venue_id TEXT NOT NULL REFERENCES venues(id) ON DELETE RESTRICT,pair_id TEXT NOT NULL REFERENCES trading_pairs(id) ON DELETE RESTRICT,market_type TEXT NOT NULL,provider_market_id TEXT,network_id TEXT REFERENCES networks(id) ON DELETE RESTRICT,liquidity_pool TEXT,pool_contract_id TEXT REFERENCES contracts(id) ON DELETE RESTRICT,pool_fee_tier REAL,constraints TEXT NOT NULL,metadata TEXT NOT NULL,UNIQUE(venue_id,pair_id)"),
"fees":("fee_metadata",FeeMetadata,("market_id","cex_maker_fee","cex_taker_fee","dex_pool_fee","network_gas_cost"),"market_id TEXT NOT NULL UNIQUE REFERENCES markets(id) ON DELETE CASCADE,cex_maker_fee REAL,cex_taker_fee REAL,dex_pool_fee REAL,network_gas_cost TEXT")}
JSON_FIELDS={"metadata","definition","constraints"}

class MetadataStore(Protocol):
    def create(self,model:Model)->Model: ...
    def get(self,kind:str,entity_id:str)->Model: ...
    def list(self,kind:str)->list[Model]: ...
    def update(self,model:Model)->Model: ...
    def delete(self,kind:str,entity_id:str)->None: ...

class SQLiteStore:
    def __init__(self,path:str|Path):
        self.path=Path(path).expanduser().resolve(); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(self.path),timeout=10); self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON"); self.db.execute("PRAGMA busy_timeout=10000"); self.db.execute("PRAGMA journal_mode=WAL")
        self.initialize()
    def initialize(self):
        with self.db:
            self.db.execute("CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL)")
            row=self.db.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if row is None: self.db.execute("INSERT INTO schema_version VALUES(0)"); version=0
            else: version=row[0]
            if version>SCHEMA_VERSION: raise MetadataError("Database schema is newer than this application")
            if version<1:
                for kind,(table,cls,fields,definition) in SCHEMAS.items():
                    self.db.execute(f"CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,{definition})")
                self.db.execute("CREATE TABLE IF NOT EXISTS asset_tokens(asset_id TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,token_id TEXT NOT NULL REFERENCES tokens(id) ON DELETE CASCADE,PRIMARY KEY(asset_id,token_id))")
                self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_native_token ON tokens(network_id,symbol) WHERE contract_id IS NULL")
                self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_contract_token ON tokens(network_id,symbol,contract_id) WHERE contract_id IS NOT NULL")
                self.db.execute("UPDATE schema_version SET version=1")
    def schema_version(self): return int(self.db.execute("SELECT version FROM schema_version").fetchone()[0])
    def _json(self,k,v): return json.dumps(v,sort_keys=True,separators=(",",":")) if k in JSON_FIELDS else v
    def _row(self,kind,row):
        table,cls,fields,definition=SCHEMAS[kind]
        d={k:row[k] for k in ("id","created_at","updated_at")}
        for k in fields: d[k]=json.loads(row[k]) if k in JSON_FIELDS else row[k]
        return cls(**d)
    def create(self,model):
        model.validate(); kind=model.kind
        if kind not in SCHEMAS: raise MetadataError("Unsupported entity "+kind)
        table,cls,fields,definition=SCHEMAS[kind]; names=("id","created_at","updated_at")+fields
        values=[self._json(k,getattr(model,k)) for k in names]
        try:
            with self.db: self.db.execute(f"INSERT INTO {table}({','.join(names)}) VALUES({','.join('?' for _ in names)})",values)
        except sqlite3.IntegrityError as e: raise self._error(e) from e
        return self.get(kind,model.id)
    def get(self,kind,entity_id):
        if kind not in SCHEMAS: raise MetadataError("Unknown entity "+kind)
        row=self.db.execute(f"SELECT * FROM {SCHEMAS[kind][0]} WHERE id=?",(entity_id,)).fetchone()
        if row is None: raise NotFoundError(f"{kind} not found: {entity_id}")
        return self._row(kind,row)
    def list(self,kind):
        if kind not in SCHEMAS: raise MetadataError("Unknown entity "+kind)
        return [self._row(kind,r) for r in self.db.execute(f"SELECT * FROM {SCHEMAS[kind][0]} ORDER BY created_at,id")]
    def update(self,model):
        model.validate(); kind=model.kind; table,cls,fields,definition=SCHEMAS[kind]; model.updated_at=timestamp()
        names=("updated_at",)+fields; vals=[self._json(k,getattr(model,k)) for k in names]
        try:
            with self.db:
                cur=self.db.execute(f"UPDATE {table} SET "+",".join(k+"=?" for k in names)+" WHERE id=?",vals+[model.id])
                if not cur.rowcount: raise NotFoundError(f"{kind} not found: {model.id}")
        except sqlite3.IntegrityError as e: raise self._error(e) from e
        return self.get(kind,model.id)
    def delete(self,kind,entity_id):
        if kind not in SCHEMAS: raise MetadataError("Unknown entity "+kind)
        try:
            with self.db:
                cur=self.db.execute(f"DELETE FROM {SCHEMAS[kind][0]} WHERE id=?",(entity_id,))
                if not cur.rowcount: raise NotFoundError(f"{kind} not found: {entity_id}")
        except sqlite3.IntegrityError as e: raise self._error(e) from e
    def link_asset_token(self,asset_id,token_id):
        try:
            with self.db: self.db.execute("INSERT INTO asset_tokens VALUES(?,?)",(asset_id,token_id))
        except sqlite3.IntegrityError as e: raise self._error(e) from e
    def tokens_for_asset(self,asset_id):
        return [self.get("token",r[0]) for r in self.db.execute("SELECT token_id FROM asset_tokens WHERE asset_id=?",(asset_id,))]
    def status(self):
        counts={k:self.db.execute(f"SELECT COUNT(*) FROM {v[0]}").fetchone()[0] for k,v in SCHEMAS.items()}
        return {"database":str(self.path),"schema_version":self.schema_version(),"foreign_keys":bool(self.db.execute("PRAGMA foreign_keys").fetchone()[0]),"counts":counts,"integrity":self.integrity_check()}
    def integrity_check(self):
        result=[r[0] for r in self.db.execute("PRAGMA integrity_check")]
        result += ["foreign key violation: "+str(tuple(r)) for r in self.db.execute("PRAGMA foreign_key_check")]
        return result
    @staticmethod
    def _error(e):
        msg=str(e)
        if "FOREIGN KEY" in msg: return RelationshipError("Referenced record is missing or still in use")
        if "UNIQUE" in msg or "PRIMARY KEY" in msg: return DuplicateError("Duplicate entity identity")
        return MetadataError("Database integrity error: "+msg)
    def close(self): self.db.close()
