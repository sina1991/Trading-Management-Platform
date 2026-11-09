"""Application services and relationship validation."""
import hashlib, json, re
from trading_platform.metadata import *
from trading_platform.persistence import MetadataStore

EVM=re.compile(r"^0x[a-fA-F0-9]{40}$")
class MetadataService:
    def __init__(self,store:MetadataStore): self.store=store
    def add(self,model):
        self._validate(model)
        if isinstance(model,ABI) and not model.checksum:
            model.checksum=hashlib.sha256(json.dumps(model.definition,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        return self.store.create(model)
    def get(self,kind,entity_id): return self.store.get(kind,entity_id)
    def list(self,kind): return self.store.list(kind)
    def update(self,model): self._validate(model); return self.store.update(model)
    def delete(self,kind,entity_id): self.store.delete(kind,entity_id)
    def _validate(self,m):
        if isinstance(m,(Token,Contract)):
            net=self.store.get("network",m.network_id)
            if isinstance(m,Contract) and net.network_type.lower() in {"evm","ethereum","evm-compatible"} and not EVM.fullmatch(m.address):
                raise MetadataError("Invalid EVM address; expected 0x plus 40 hexadecimal characters")
        if isinstance(m,Token) and m.contract_id:
            c=self.store.get("contract",m.contract_id)
            if c.network_id!=m.network_id: raise RelationshipError("Token and Contract must belong to the same Network")
        if isinstance(m,Contract) and m.abi_id: self.store.get("abi",m.abi_id)
        if isinstance(m,TradingPair):
            self.store.get("asset",m.base_asset_id); self.store.get("asset",m.quote_asset_id)
        if isinstance(m,Market):
            v=self.store.get("venue",m.venue_id); self.store.get("pair",m.pair_id)
            if m.network_id: self.store.get("network",m.network_id)
            if v.venue_type.lower()=="dex" and not m.network_id: raise MetadataError("DEX markets require network_id")
            if v.venue_type.lower()=="cex" and (m.liquidity_pool or m.pool_contract_id or m.pool_fee_tier is not None): raise MetadataError("CEX markets cannot define DEX pool fields")
            if m.pool_contract_id:
                c=self.store.get("contract",m.pool_contract_id)
                if m.network_id and c.network_id!=m.network_id: raise RelationshipError("Pool contract must match market network")
        if isinstance(m,FeeMetadata):
            market=self.store.get("market",m.market_id); venue=self.store.get("venue",market.venue_id)
            if venue.venue_type=="cex" and m.dex_pool_fee is not None: raise MetadataError("CEX fee records cannot set DEX pool fee")
            if venue.venue_type=="dex" and (m.cex_maker_fee is not None or m.cex_taker_fee is not None): raise MetadataError("DEX fee records cannot set CEX maker/taker fees")
    def find_network_by_chain_id(self,chain_id): return next((x for x in self.list("network") if x.chain_id==chain_id),None)
    def find_tokens(self,network_id=None,symbol=None):
        return [x for x in self.list("token") if (network_id is None or x.network_id==network_id) and (symbol is None or x.symbol.casefold()==symbol.casefold())]
    def find_contracts_by_network(self,network_id): return [x for x in self.list("contract") if x.network_id==network_id]
    def find_markets_by_venue(self,venue_id): return [x for x in self.list("market") if x.venue_id==venue_id]
    def find_markets_by_pair(self,pair_id): return [x for x in self.list("market") if x.pair_id==pair_id]
    def link_asset_token(self,asset_id,token_id):
        self.store.get("asset",asset_id); self.store.get("token",token_id); self.store.link_asset_token(asset_id,token_id)
    def tokens_for_asset(self,asset_id):
        self.store.get("asset",asset_id); return self.store.tokens_for_asset(asset_id)
