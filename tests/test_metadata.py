import pytest
from trading_platform.metadata import (Network, ABI, Contract, Token, Asset, TradingPair, TradingVenue, Market, FeeMetadata, MetadataError, RelationshipError, DuplicateError)
from trading_platform.persistence import SQLiteStore
from trading_platform.services import MetadataService

def setup(tmp_path):
    store=SQLiteStore(tmp_path/"metadata.sqlite3")
    return store,MetadataService(store)

def test_complete_metadata_workflow_and_restart(tmp_path):
    store,svc=setup(tmp_path)
    network=svc.add(Network(name="Ethereum",chain_id=1,native_currency="ETH"))
    abi=svc.add(ABI(name="ERC20",definition=[{"type":"function","name":"transfer"}]))
    contract=svc.add(Contract(name="USDC",network_id=network.id,address="0x"+"a"*40,abi_id=abi.id))
    token=svc.add(Token(name="USD Coin",symbol="USDC",network_id=network.id,contract_id=contract.id,decimals=6,standard="ERC20"))
    usd=svc.add(Asset(name="US Dollar Coin",symbol="USDC"))
    eth=svc.add(Asset(name="Ether",symbol="ETH"))
    pair=svc.add(TradingPair(base_asset_id=usd.id,quote_asset_id=eth.id))
    venue=svc.add(TradingVenue(name="Example DEX",venue_type="dex"))
    market=svc.add(Market(name="USDC-ETH",venue_id=venue.id,pair_id=pair.id,network_id=network.id,pool_fee_tier=.003))
    svc.add(FeeMetadata(market_id=market.id,dex_pool_fee=.003,network_gas_cost="variable"))
    svc.link_asset_token(usd.id,token.id)
    assert svc.find_network_by_chain_id(1).id==network.id
    assert len(svc.find_contracts_by_network(network.id))==1
    assert len(svc.find_markets_by_venue(venue.id))==1
    assert len(svc.tokens_for_asset(usd.id))==1
    store.close()
    store,svc=setup(tmp_path)
    assert svc.get("market",market.id).venue_id==venue.id
    assert store.integrity_check()==["ok"]
    assert store.schema_version()==1
    store.close()

def test_network_chain_id_is_unique(tmp_path):
    store,svc=setup(tmp_path)
    svc.add(Network(name="Ethereum",chain_id=1))
    with pytest.raises(DuplicateError): svc.add(Network(name="Duplicate",chain_id=1))
    store.close()

def test_contract_identity_is_network_scoped(tmp_path):
    store,svc=setup(tmp_path)
    n1=svc.add(Network(name="One",chain_id=1))
    n2=svc.add(Network(name="Two",chain_id=2))
    address="0x"+"b"*40
    c1=svc.add(Contract(name="C1",network_id=n1.id,address=address))
    c2=svc.add(Contract(name="C2",network_id=n2.id,address=address))
    assert c1.id!=c2.id
    store.close()

def test_token_contract_must_share_network(tmp_path):
    store,svc=setup(tmp_path)
    n1=svc.add(Network(name="One",chain_id=1))
    n2=svc.add(Network(name="Two",chain_id=2))
    c=svc.add(Contract(name="Token",network_id=n1.id,address="0x"+"c"*40))
    with pytest.raises(RelationshipError):
        svc.add(Token(name="Wrong",symbol="WRG",network_id=n2.id,contract_id=c.id,standard="ERC20"))
    store.close()

def test_evm_address_validation(tmp_path):
    store,svc=setup(tmp_path)
    n=svc.add(Network(name="Ethereum",chain_id=1))
    with pytest.raises(MetadataError): svc.add(Contract(name="Bad",network_id=n.id,address="not-an-address"))
    store.close()

def test_pair_requires_distinct_existing_assets(tmp_path):
    store,svc=setup(tmp_path)
    a=svc.add(Asset(name="Bitcoin",symbol="BTC"))
    with pytest.raises(MetadataError): svc.add(TradingPair(base_asset_id=a.id,quote_asset_id=a.id))
    with pytest.raises(RelationshipError): svc.add(TradingPair(base_asset_id="missing",quote_asset_id="also-missing"))
    store.close()

def test_dex_market_requires_network_and_cex_rejects_pool_fields(tmp_path):
    store,svc=setup(tmp_path)
    n=svc.add(Network(name="Ethereum",chain_id=1))
    a=svc.add(Asset(name="A",symbol="A")); b=svc.add(Asset(name="B",symbol="B"))
    p=svc.add(TradingPair(base_asset_id=a.id,quote_asset_id=b.id))
    dex=svc.add(TradingVenue(name="DEX",venue_type="dex"))
    cex=svc.add(TradingVenue(name="CEX",venue_type="cex"))
    with pytest.raises(MetadataError): svc.add(Market(name="bad dex",venue_id=dex.id,pair_id=p.id))
    with pytest.raises(MetadataError): svc.add(Market(name="bad cex",venue_id=cex.id,pair_id=p.id,network_id=n.id,liquidity_pool="pool"))
    store.close()

def test_foreign_key_prevents_deleting_referenced_network(tmp_path):
    store,svc=setup(tmp_path)
    n=svc.add(Network(name="Ethereum",chain_id=1))
    svc.add(Token(name="Ether",symbol="ETH",network_id=n.id))
    with pytest.raises(RelationshipError): svc.delete("network",n.id)
    store.close()

def test_fee_types_remain_distinct(tmp_path):
    store,svc=setup(tmp_path)
    n=svc.add(Network(name="Ethereum",chain_id=1))
    a=svc.add(Asset(name="A",symbol="A")); b=svc.add(Asset(name="B",symbol="B"))
    p=svc.add(TradingPair(base_asset_id=a.id,quote_asset_id=b.id))
    v=svc.add(TradingVenue(name="DEX",venue_type="dex"))
    m=svc.add(Market(name="A-B",venue_id=v.id,pair_id=p.id,network_id=n.id))
    with pytest.raises(MetadataError): svc.add(FeeMetadata(market_id=m.id,cex_maker_fee=.001))
    store.close()

def test_abi_checksum_is_generated(tmp_path):
    store,svc=setup(tmp_path)
    abi=svc.add(ABI(name="ABI",definition=[]))
    assert len(abi.checksum)==64
    store.close()

def test_cli_metadata_commands_are_ready(project_root):
    from trading_platform.catalog import build_command_specs
    from trading_platform.core import CommandRegistry, ReadinessChecker, ReadinessStatus
    registry=CommandRegistry(build_command_specs())
    checker=ReadinessChecker(project_root,{})
    for command in registry.all():
        if command.handler_key=="metadata_dispatch":
            assert checker.check(command).status is ReadinessStatus.READY
