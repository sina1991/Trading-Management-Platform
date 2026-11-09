"""Typed domain models for blockchain and trading metadata."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import uuid4
import json
import re


def _validate_abi_definition(definition):
    allowed={"function","event","error","constructor","fallback","receive"}
    def parameters(value, label):
        if not isinstance(value,list): raise MetadataError(f"ABI {label} must be an array")
        for item in value:
            if not isinstance(item,dict) or not isinstance(item.get("type"),str) or not item["type"].strip():
                raise MetadataError(f"ABI {label} entries require a string type")
            if "name" in item and not isinstance(item["name"],str): raise MetadataError(f"ABI {label} name must be a string")
            if "components" in item: parameters(item["components"], label+" components")
    for entry in definition:
        if not isinstance(entry,dict): raise MetadataError("ABI entries must be objects")
        kind=entry.get("type","function")
        if not isinstance(kind,str) or kind not in allowed: raise MetadataError("Unsupported ABI entry type")
        if kind in {"function","event","error"} and (not isinstance(entry.get("name"),str) or not entry["name"].strip()):
            raise MetadataError(f"ABI {kind} entries require a name")
        if kind in {"function","event","error","constructor"}: parameters(entry.get("inputs",[]),"inputs")
        if kind=="function": parameters(entry.get("outputs",[]),"outputs")
        if "stateMutability" in entry and entry["stateMutability"] not in {"pure","view","nonpayable","payable"}:
            raise MetadataError("Invalid ABI stateMutability")
        if kind=="event" and "anonymous" in entry and not isinstance(entry["anonymous"],bool):
            raise MetadataError("ABI event anonymous must be boolean")

def timestamp(): return datetime.now(timezone.utc).isoformat()
def identifier(): return str(uuid4())

class MetadataError(ValueError): pass
class NotFoundError(MetadataError): pass
class DuplicateError(MetadataError): pass
class RelationshipError(MetadataError): pass

@dataclass
class Model:
    id: str = field(default_factory=identifier)
    created_at: str = field(default_factory=timestamp)
    updated_at: str = field(default_factory=timestamp)
    kind: ClassVar[str] = "model"
    def validate(self):
        if not isinstance(self.id,str) or not self.id.strip(): raise MetadataError("id must be a non-empty string")
        if not isinstance(self.created_at,str) or not isinstance(self.updated_at,str): raise MetadataError("timestamps must be strings")
        if hasattr(self,"metadata"):
            metadata=getattr(self,"metadata")
            if not isinstance(metadata,dict): raise MetadataError("metadata must be an object")
            forbidden={"password","secret","privatekey","apikey","accesstoken","credential","authorization","bearer","clientsecret","seedphrase","mnemonic","token"}
            def inspect(value):
                if isinstance(value,dict):
                    for key,item in value.items():
                        normalized=re.sub(r"[^a-z0-9]","",str(key).casefold())
                        if normalized in forbidden or normalized.endswith(("apikey","privatekey","clientsecret","accesstoken")): raise MetadataError("Do not store credentials or secrets in metadata; use a secure external reference")
                        inspect(item)
                elif isinstance(value,list):
                    for item in value: inspect(item)
            inspect(metadata)
    def to_dict(self): return asdict(self)
    @classmethod
    def from_dict(cls,value): return cls(**value)

@dataclass
class Network(Model):
    name: str = ""
    chain_id: int = 0
    network_type: str = "evm"
    native_currency: str = "ETH"
    rpc_config_ref: str|None = None
    status: str = "active"
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "network"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not isinstance(self.native_currency,str) or not self.name.strip() or not self.native_currency.strip(): raise MetadataError("network name and native currency must be non-empty strings")
        if type(self.chain_id) is not int or self.chain_id <= 0: raise MetadataError("chain_id must be a positive integer")
        if not isinstance(self.status,str) or self.status not in {"active","inactive","testnet","deprecated"}: raise MetadataError("invalid network status")
        if not isinstance(self.network_type,str) or not self.network_type.strip(): raise MetadataError("network_type must be a non-empty string")
        if self.rpc_config_ref is not None and not isinstance(self.rpc_config_ref,str): raise MetadataError("rpc_config_ref must be a string or null")
        if self.rpc_config_ref and self.rpc_config_ref.lower().startswith(("http://","https://")): raise MetadataError("rpc_config_ref must be a configuration reference, not a URL or credential")
        if not isinstance(self.metadata,dict): raise MetadataError("metadata must be an object")

@dataclass
class ABI(Model):
    name: str = ""
    version: str = "1"
    format: str = "json"
    definition: list[Any] = field(default_factory=list)
    checksum: str|None = None
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "abi"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not isinstance(self.version,str) or not self.name.strip() or not self.version.strip(): raise MetadataError("ABI name and version must be non-empty strings")
        if not isinstance(self.format,str) or self.format.lower() != "json" or not isinstance(self.definition,list): raise MetadataError("ABI format must be json and definition must be an array")
        if self.checksum is not None and not isinstance(self.checksum,str): raise MetadataError("ABI checksum must be a string or null")
        try: json.dumps(self.definition)
        except (TypeError,ValueError) as e: raise MetadataError("ABI definition must be JSON serializable") from e
        _validate_abi_definition(self.definition)

@dataclass
class Contract(Model):
    name: str = ""
    network_id: str = ""
    address: str = ""
    contract_type: str = "generic"
    abi_id: str|None = None
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "contract"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.network_id,str) or not self.network_id or not isinstance(self.address,str) or not self.address.strip(): raise MetadataError("contract name, network_id and address must be non-empty strings")
        if not isinstance(self.contract_type,str) or not self.contract_type.strip() or (self.abi_id is not None and not isinstance(self.abi_id,str)): raise MetadataError("contract_type must be a non-empty string and abi_id a string or null")

@dataclass
class Token(Model):
    name: str = ""
    symbol: str = ""
    network_id: str = ""
    contract_id: str|None = None
    decimals: int = 18
    standard: str = "native"
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "token"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.symbol,str) or not self.symbol.strip() or not isinstance(self.network_id,str) or not self.network_id: raise MetadataError("token name, symbol and network_id must be non-empty strings")
        if type(self.decimals) is not int or not 0 <= self.decimals <= 255: raise MetadataError("decimals must be an integer from 0 to 255")
        if not isinstance(self.standard,str) or not self.standard.strip() or (self.contract_id is not None and not isinstance(self.contract_id,str)): raise MetadataError("standard must be a non-empty string and contract_id a string or null")
        if self.standard == "native" and self.contract_id: raise MetadataError("native token cannot reference a contract")
        if self.standard != "native" and not self.contract_id: raise MetadataError("contract token requires contract_id")

@dataclass
class Asset(Model):
    name: str = ""
    symbol: str = ""
    asset_type: str = "crypto"
    description: str|None = None
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "asset"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.symbol,str) or not self.symbol.strip(): raise MetadataError("asset name and symbol must be non-empty strings")
        if not isinstance(self.asset_type,str) or not self.asset_type.strip() or (self.description is not None and not isinstance(self.description,str)): raise MetadataError("asset_type must be a non-empty string and description a string or null")

@dataclass
class TradingPair(Model):
    base_asset_id: str = ""
    quote_asset_id: str = ""
    symbol: str|None = None
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "pair"
    def validate(self):
        super().validate()
        if not isinstance(self.base_asset_id,str) or not self.base_asset_id or not isinstance(self.quote_asset_id,str) or not self.quote_asset_id or self.base_asset_id == self.quote_asset_id: raise MetadataError("pair requires distinct non-empty string asset IDs")
        if self.symbol is not None and not isinstance(self.symbol,str): raise MetadataError("pair symbol must be a string or null")

@dataclass
class TradingVenue(Model):
    name: str = ""
    venue_type: str = "cex"
    provider: str|None = None
    status: str = "active"
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "venue"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.venue_type,str) or self.venue_type.lower() not in {"cex","dex"}: raise MetadataError("venue requires a non-empty name and type cex or dex")
        if not isinstance(self.status,str) or not self.status.strip() or (self.provider is not None and not isinstance(self.provider,str)): raise MetadataError("venue status must be a non-empty string and provider a string or null")

@dataclass
class Market(Model):
    name: str = ""
    venue_id: str = ""
    pair_id: str = ""
    market_type: str = "spot"
    provider_market_id: str|None = None
    network_id: str|None = None
    liquidity_pool: str|None = None
    pool_contract_id: str|None = None
    pool_fee_tier: float|None = None
    constraints: dict[str,Any] = field(default_factory=dict)
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "market"
    def validate(self):
        super().validate()
        if not isinstance(self.name,str) or not self.name.strip() or not isinstance(self.venue_id,str) or not self.venue_id or not isinstance(self.pair_id,str) or not self.pair_id: raise MetadataError("market name, venue_id and pair_id must be non-empty strings")
        for field_name in ("market_type","provider_market_id","network_id","liquidity_pool","pool_contract_id"):
            value=getattr(self,field_name)
            if value is not None and (not isinstance(value,str) or (field_name=="market_type" and not value.strip())): raise MetadataError(f"{field_name} must be a string"+(" and non-empty" if field_name=="market_type" else "")+" or null")
        if self.pool_fee_tier is not None and not 0 <= self.pool_fee_tier <= 1: raise MetadataError("pool fee must be between 0 and 1")

@dataclass
class FeeMetadata(Model):
    market_id: str = ""
    cex_maker_fee: float|None = None
    cex_taker_fee: float|None = None
    dex_pool_fee: float|None = None
    network_gas_cost: str|None = None
    kind: ClassVar[str] = "fees"
    def validate(self):
        super().validate()
        if not isinstance(self.market_id,str) or not self.market_id: raise MetadataError("market_id must be a non-empty string")
        if self.network_gas_cost is not None and not isinstance(self.network_gas_cost,str): raise MetadataError("network_gas_cost must be a string or null")
        for v in (self.cex_maker_fee,self.cex_taker_fee,self.dex_pool_fee):
            if v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or not 0 <= v <= 1): raise MetadataError("fee rates must be fractions between 0 and 1")
