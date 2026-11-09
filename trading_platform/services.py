"""Application services and relationship validation."""
import hashlib
import json
from trading_platform.metadata import *
from trading_platform.persistence import MetadataStore
from eth_utils import is_address, to_checksum_address

EVM_NETWORK_TYPES = {"evm", "ethereum", "evm-compatible"}

def abi_checksum(definition):
    return hashlib.sha256(json.dumps(definition, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class MetadataService:
    def __init__(self, store: MetadataStore):
        self.store = store

    def add(self, model):
        self._validate(model)
        if isinstance(model, Contract):
            network = self.store.get("network", model.network_id)
            if network.network_type.lower() in EVM_NETWORK_TYPES:
                model.address = to_checksum_address(model.address)
        if isinstance(model, ABI):
            model.checksum = abi_checksum(model.definition)
        return self.store.create(model)

    def get(self, kind, entity_id): return self.store.get(kind, entity_id)
    def list(self, kind): return self.store.list(kind)

    def update(self, model):
        self._validate(model)
        if isinstance(model, Contract):
            network = self.store.get("network", model.network_id)
            if network.network_type.lower() in EVM_NETWORK_TYPES:
                model.address = to_checksum_address(model.address)
        if isinstance(model, ABI):
            model.checksum = abi_checksum(model.definition)
        return self.store.update(model)

    def delete(self, kind, entity_id): self.store.delete(kind, entity_id)

    def _validate(self, model):
        model.validate()
        if isinstance(model, (Token, Contract)):
            network = self.store.get("network", model.network_id)
            if isinstance(model, Contract) and network.network_type.lower() in EVM_NETWORK_TYPES:
                if not is_address(model.address):
                    raise MetadataError("Invalid EVM address; expected a 20-byte hexadecimal address")
        if isinstance(model, Token) and model.contract_id:
            contract = self.store.get("contract", model.contract_id)
            if contract.network_id != model.network_id:
                raise RelationshipError("Token and Contract must belong to the same Network")
        if isinstance(model, Contract) and model.abi_id:
            self.store.get("abi", model.abi_id)
        if isinstance(model, TradingPair):
            self.store.get("asset", model.base_asset_id)
            self.store.get("asset", model.quote_asset_id)
        if isinstance(model, Market):
            venue = self.store.get("venue", model.venue_id)
            self.store.get("pair", model.pair_id)
            if model.network_id: self.store.get("network", model.network_id)
            if venue.venue_type.lower() == "dex" and not model.network_id:
                raise MetadataError("DEX markets require network_id")
            if venue.venue_type.lower() == "cex" and (model.liquidity_pool or model.pool_contract_id or model.pool_fee_tier is not None):
                raise MetadataError("CEX markets cannot define DEX pool fields")
            if model.pool_contract_id:
                contract = self.store.get("contract", model.pool_contract_id)
                if not model.network_id or contract.network_id != model.network_id:
                    raise RelationshipError("Pool contract must match market network")
        if isinstance(model, FeeMetadata):
            market = self.store.get("market", model.market_id)
            venue = self.store.get("venue", market.venue_id)
            if venue.venue_type.lower() == "cex" and model.dex_pool_fee is not None:
                raise MetadataError("CEX fee records cannot set DEX pool fee")
            if venue.venue_type.lower() == "dex" and (model.cex_maker_fee is not None or model.cex_taker_fee is not None):
                raise MetadataError("DEX fee records cannot set CEX maker/taker fees")

    def find_assets(self, name=None, symbol=None):
        return [x for x in self.list("asset") if (name is None or x.name.casefold()==name.casefold()) and (symbol is None or x.symbol.casefold()==symbol.casefold())]
    def find_abis(self, name=None, version=None):
        return [x for x in self.list("abi") if (name is None or x.name.casefold()==name.casefold()) and (version is None or x.version==version)]
    def find_network_by_chain_id(self, chain_id): return next((x for x in self.list("network") if x.chain_id==chain_id), None)
    def find_tokens(self, network_id=None, symbol=None):
        return [x for x in self.list("token") if (network_id is None or x.network_id==network_id) and (symbol is None or x.symbol.casefold()==symbol.casefold())]
    def find_contracts_by_network(self, network_id): return [x for x in self.list("contract") if x.network_id==network_id]
    def find_markets_by_venue(self, venue_id): return [x for x in self.list("market") if x.venue_id==venue_id]
    def find_markets_by_pair(self, pair_id): return [x for x in self.list("market") if x.pair_id==pair_id]
    def link_asset_token(self, asset_id, token_id):
        self.store.get("asset", asset_id); self.store.get("token", token_id); self.store.link_asset_token(asset_id, token_id)
    def tokens_for_asset(self, asset_id):
        self.store.get("asset", asset_id); return self.store.tokens_for_asset(asset_id)
