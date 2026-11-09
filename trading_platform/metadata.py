"""Typed domain models for blockchain and trading metadata."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import uuid4
import json

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
        if not isinstance(self.id,str) or not self.id.strip(): raise MetadataError("id is required")
        if hasattr(self,"metadata"):
            metadata=getattr(self,"metadata")
            if not isinstance(metadata,dict): raise MetadataError("metadata must be an object")
            forbidden={"password","secret","private_key","privatekey","api_key","apikey","access_token","credential"}
            def inspect(value):
                if isinstance(value,dict):
                    for key,item in value.items():
                        if str(key).casefold() in forbidden: raise MetadataError("Do not store credentials or secrets in metadata; use a secure external reference")
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
        if not self.name.strip() or not self.native_currency.strip(): raise MetadataError("network name and native currency are required")
        if type(self.chain_id) is not int or self.chain_id <= 0: raise MetadataError("chain_id must be a positive integer")
        if self.status not in {"active","inactive","testnet","deprecated"}: raise MetadataError("invalid network status")
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
        if not self.name.strip() or not self.version.strip(): raise MetadataError("ABI name and version are required")
        if self.format.lower() != "json" or not isinstance(self.definition,list): raise MetadataError("ABI must use a JSON array definition")
        try: json.dumps(self.definition)
        except (TypeError,ValueError) as e: raise MetadataError("ABI definition must be JSON serializable") from e

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
        if not self.name.strip() or not self.network_id or not self.address.strip(): raise MetadataError("contract name, network_id and address are required")

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
        if not self.name.strip() or not self.symbol.strip() or not self.network_id: raise MetadataError("token name, symbol and network_id are required")
        if type(self.decimals) is not int or not 0 <= self.decimals <= 255: raise MetadataError("decimals must be an integer from 0 to 255")
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
        if not self.name.strip() or not self.symbol.strip(): raise MetadataError("asset name and symbol are required")

@dataclass
class TradingPair(Model):
    base_asset_id: str = ""
    quote_asset_id: str = ""
    symbol: str|None = None
    metadata: dict[str,Any] = field(default_factory=dict)
    kind: ClassVar[str] = "pair"
    def validate(self):
        super().validate()
        if not self.base_asset_id or not self.quote_asset_id or self.base_asset_id == self.quote_asset_id: raise MetadataError("pair requires distinct base and quote assets")

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
        if not self.name.strip() or self.venue_type.lower() not in {"cex","dex"}: raise MetadataError("venue requires a name and type cex or dex")

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
        if not self.name.strip() or not self.venue_id or not self.pair_id: raise MetadataError("market name, venue_id and pair_id are required")
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
        if not self.market_id: raise MetadataError("market_id is required")
        for v in (self.cex_maker_fee,self.cex_taker_fee,self.dex_pool_fee):
            if v is not None and (not isinstance(v,(int,float)) or isinstance(v,bool) or not 0 <= v <= 1): raise MetadataError("fee rates must be fractions between 0 and 1")
