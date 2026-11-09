"""Interactive metadata CLI adapter; validation and persistence live below this layer."""
import json
from dataclasses import fields
from pathlib import Path
from trading_platform.metadata import *
from trading_platform.persistence import SQLiteStore
from trading_platform.services import MetadataService

MODELS={"network":Network,"token":Token,"contract":Contract,"abi":ABI,"asset":Asset,"pair":TradingPair,"venue":TradingVenue,"market":Market,"fees":FeeMetadata}
class MetadataCLI:
    def __init__(self,root,config,input_fn=input,output_fn=print):
        self.input=input_fn; self.output=output_fn
        folder=Path(config.get("storage",{}).get("data_dir","data"))
        if not folder.is_absolute(): folder=Path(root)/folder
        self.store=SQLiteStore(folder/"metadata.sqlite3"); self.service=MetadataService(self.store)
    def execute(self,command):
        if command.startswith("storage."): return self.storage(command)
        if command=="abi.link":
            c=self.service.get("contract",self.input("Contract ID: ").strip()); c.abi_id=self.input("ABI ID: ").strip()
            self.service.update(c); self.output("ABI linked to Contract."); return c
        if command=="asset.link_token":
            self.service.link_asset_token(self.input("Asset ID: ").strip(),self.input("Token ID: ").strip())
            self.output("Token linked to Asset."); return
        if command=="asset.tokens":
            return self.show_many(self.service.tokens_for_asset(self.input("Asset ID: ").strip()))
        if command=="market.fees.configure": return self.create("fees")
        kind=command.split(".")[0]
        op=command.split(".")[-1]
        if command=="market.asset.add": kind,op="asset","add"
        if command=="market.pair.add": kind,op="pair","add"
        if kind not in MODELS: raise MetadataError("Unsupported metadata command: "+command)
        if command.endswith("find_chain"):
            item=self.service.find_network_by_chain_id(int(self.input("Chain ID: ")))
            self.output(json.dumps(item.to_dict(),ensure_ascii=False) if item else "No network found"); return item
        if command.endswith("find_network"): return self.show_many(self.service.find_contracts_by_network(self.input("Network ID: ").strip()))
        if command.endswith("find_venue"): return self.show_many(self.service.find_markets_by_venue(self.input("Venue ID: ").strip()))
        if command.endswith("find_pair"): return self.show_many(self.service.find_markets_by_pair(self.input("Trading Pair ID: ").strip()))
        if op=="find": return self.show_many(self.service.find_tokens(self.input("Network ID (blank for any): ").strip() or None,self.input("Symbol (blank for any): ").strip() or None))
        if op=="add": return self.create(kind)
        if op=="list": return self.show_many(self.service.list(kind))
        if op in {"get","view"}:
            x=self.service.get(kind,self.input(kind+" ID: ").strip()); self.output(json.dumps(x.to_dict(),ensure_ascii=False)); return x
        if op=="update":
            x=self.service.get(kind,self.input(kind+" ID: ").strip())
            patch=self.read_json("Fields to update (JSON object): ")
            allowed={f.name for f in fields(x)}-{"id","created_at"}
            if set(patch)-allowed: raise MetadataError("Unknown or immutable fields: "+", ".join(set(patch)-allowed))
            for k,v in patch.items(): setattr(x,k,v)
            x=self.service.update(x); self.output("Updated "+x.id); return x
        if op=="delete":
            entity_id=self.input(kind+" ID: ").strip()
            if self.input("Type DELETE to confirm: ").strip()!="DELETE": self.output("Cancelled"); return
            self.service.delete(kind,entity_id); self.output("Deleted "+entity_id); return
        if op=="validate":
            x=MODELS[kind](**self.read_json("Metadata JSON object: ")); x.validate(); self.service._validate(x)
            self.output(kind+" metadata is valid"); return x
        raise MetadataError("Unsupported command "+command)
    def read_json(self,prompt):
        try: value=json.loads(self.input(prompt))
        except json.JSONDecodeError as e: raise MetadataError("Invalid JSON: "+e.msg) from e
        if not isinstance(value,dict): raise MetadataError("Expected a JSON object")
        return value
    def create(self,kind):
        x=MODELS[kind](**self.read_json("Enter "+kind+" fields as JSON: "))
        x=self.service.add(x); self.output("Created "+kind+": "+x.id); return x
    def show_many(self,items):
        for x in items: self.output(json.dumps(x.to_dict(),ensure_ascii=False))
        self.output(str(len(items))+" record(s)"); return items
    def storage(self,command):
        status=self.store.status()
        if command=="storage.schema": self.output("Schema version: "+str(status["schema_version"]))
        elif command=="storage.integrity":
            for x in status["integrity"]: self.output(x)
        else: self.output(json.dumps(status,ensure_ascii=False,indent=2))
        return status
    def close(self): self.store.close()
