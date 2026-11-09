import pytest
from pathlib import Path
from trading_platform.metadata import (Network, ABI, Contract, Token, Asset, TradingPair, TradingVenue, Market, FeeMetadata, MetadataError, RelationshipError, DuplicateError, NotFoundError)
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
    assert store.schema_version()==2
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
    with pytest.raises(MetadataError): svc.add(TradingPair(base_asset_id="missing",quote_asset_id="also-missing"))
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

def test_cli_metadata_commands_are_ready():
    project_root = Path(__file__).resolve().parents[1]
    from trading_platform.catalog import build_command_specs
    from trading_platform.core import CommandRegistry, ReadinessChecker, ReadinessStatus
    registry=CommandRegistry(build_command_specs())
    checker=ReadinessChecker(project_root,{})
    for command in registry.all():
        if command.handler_key=="metadata_dispatch":
            assert checker.check(command).status is ReadinessStatus.READY

def test_public_metadata_rejects_secrets():
    with pytest.raises(MetadataError):
        Network(name="Unsafe",chain_id=999,metadata={"rpc":{"api_key":"never-store"}}).validate()

def test_rpc_config_is_reference_not_url():
    with pytest.raises(MetadataError):
        Network(name="Unsafe",chain_id=1000,rpc_config_ref="https://user:pass@example.invalid").validate()

def test_model_round_trip():
    n=Network(name="Ethereum",chain_id=1)
    assert Network.from_dict(n.to_dict())==n

def test_asset_and_abi_search(tmp_path):
    store,svc=setup(tmp_path)
    asset=svc.add(Asset(name="Bitcoin",symbol="BTC"))
    abi=svc.add(ABI(name="ERC20",version="2",definition=[]))
    assert svc.find_assets(symbol="btc")[0].id==asset.id
    assert svc.find_abis(name="erc20",version="2")[0].id==abi.id
    store.close()

def test_update_and_delete_crud(tmp_path):
    store,svc=setup(tmp_path)
    item=svc.add(Network(name="Initial",chain_id=15555))
    item.name="Updated"
    saved=svc.update(item)
    assert saved.name=="Updated"
    assert saved.updated_at>=saved.created_at
    svc.delete("network",saved.id)
    with pytest.raises(MetadataError): svc.get("network",saved.id)
    store.close()

def test_storage_status_and_integrity(tmp_path):
    store,svc=setup(tmp_path)
    status=store.status()
    assert status["schema_version"]==2
    assert status["foreign_keys"] is True
    assert status["integrity"]==["ok"]
    store.close()


def test_evm_address_is_checksum_canonical_and_duplicate_identity(tmp_path):
    store,svc=setup(tmp_path)
    n=svc.add(Network(name="Ethereum",chain_id=1))
    lower="0x"+"a"*40
    first=svc.add(Contract(name="lower",network_id=n.id,address=lower))
    assert first.address.startswith("0x")
    assert first.address != lower
    with pytest.raises(DuplicateError):
        svc.add(Contract(name="upper",network_id=n.id,address="0x"+"A"*40))
    store.close()

def test_abi_structure_is_validated_and_checksum_recomputed_on_update(tmp_path):
    store,svc=setup(tmp_path)
    with pytest.raises(MetadataError):
        svc.add(ABI(name="bad",definition=[{"type":"function","inputs":[{"name":"x"}]}]))
    item=svc.add(ABI(name="good",definition=[{"type":"function","name":"f","inputs":[]}]))
    old=item.checksum
    item.definition=[{"type":"function","name":"g","inputs":[]}]
    updated=svc.update(item)
    assert updated.checksum != old
    store.close()

def test_metadata_secret_key_normalization_and_string_types():
    for key in ("api-key","Authorization","client_secret","private-key","accessToken"):
        with pytest.raises(MetadataError):
            Asset(name="A",symbol="A",metadata={key:"sensitive"}).validate()
    with pytest.raises(MetadataError):
        Network(name=123,chain_id=1).validate()
    with pytest.raises(MetadataError):
        Contract(name="contract",network_id="net",address=123).validate()

def test_sqlite_trigger_rejects_cross_network_token_contract_direct_store(tmp_path):
    store,svc=setup(tmp_path)
    n1=svc.add(Network(name="one",chain_id=1))
    n2=svc.add(Network(name="two",chain_id=2))
    c=svc.add(Contract(name="contract",network_id=n1.id,address="0x"+"b"*40))
    with pytest.raises(RelationshipError):
        store.create(Token(name="bad",symbol="BAD",network_id=n2.id,contract_id=c.id,standard="ERC20"))
    store.close()

def test_schema_v1_to_v2_migration_is_idempotent_and_preserves_records(tmp_path):
    store,svc=setup(tmp_path)
    network=svc.add(Network(name="saved",chain_id=987))
    store.db.execute("DROP TRIGGER IF EXISTS tokens_contract_network_insert")
    store.db.execute("DROP TRIGGER IF EXISTS tokens_contract_network_update")
    store.db.execute("DROP TRIGGER IF EXISTS markets_pool_network_insert")
    store.db.execute("DROP TRIGGER IF EXISTS markets_pool_network_update")
    store.db.execute("UPDATE schema_version SET version=1")
    store.db.commit()
    store.close()
    store=SQLiteStore(tmp_path/"metadata.sqlite3")
    assert store.schema_version()==2
    assert store.get("network",network.id).name=="saved"
    assert store.integrity_check()==["ok"]
    store.close()
    store=SQLiteStore(tmp_path/"metadata.sqlite3")
    assert store.schema_version()==2
    store.close()


def test_evm_contract_address_is_canonicalized_on_update(tmp_path):
    store,svc=setup(tmp_path)
    n=svc.add(Network(name="Ethereum",chain_id=1))
    contract=svc.add(Contract(name="C",network_id=n.id,address="0x"+"b"*40))
    contract.address="0x"+"C"*40
    updated=svc.update(contract)
    from eth_utils import to_checksum_address
    assert updated.address==to_checksum_address("0x"+"C"*40)
    store.close()


def test_model_rejects_invalid_optional_and_enum_field_types():
    with pytest.raises(MetadataError):
        ABI(name="ABI",format=123).validate()
    with pytest.raises(MetadataError):
        Network(name="net",chain_id=1,status=[]).validate()
    with pytest.raises(MetadataError):
        Network(name="net",chain_id=1,rpc_config_ref=[]).validate()
    with pytest.raises(MetadataError):
        Contract(name="C",network_id="n",address="0x"+"a"*40,contract_type=[]).validate()
    with pytest.raises(MetadataError):
        Asset(name="A",symbol="A",description=[]).validate()
    with pytest.raises(MetadataError):
        Market(name="M",venue_id="v",pair_id="p",market_type=None).validate()


def test_delete_restrictions_cover_all_metadata_relationships(tmp_path):
    store,svc=setup(tmp_path)
    network=svc.add(Network(name="Network",chain_id=1))
    contract=svc.add(Contract(name="Pool",network_id=network.id,address="0x"+"d"*40))
    token=svc.add(Token(name="Token",symbol="TOK",network_id=network.id,contract_id=contract.id,standard="ERC20"))
    base=svc.add(Asset(name="Base",symbol="B"))
    quote=svc.add(Asset(name="Quote",symbol="Q"))
    pair=svc.add(TradingPair(base_asset_id=base.id,quote_asset_id=quote.id))
    venue=svc.add(TradingVenue(name="DEX",venue_type="dex"))
    market=svc.add(Market(name="B-Q",venue_id=venue.id,pair_id=pair.id,network_id=network.id,pool_contract_id=contract.id))
    fee=svc.add(FeeMetadata(market_id=market.id,dex_pool_fee=.003))
    for kind,entity_id in (("network",network.id),("contract",contract.id),("asset",base.id),
                           ("venue",venue.id),("pair",pair.id)):
        with pytest.raises(RelationshipError):
            svc.delete(kind,entity_id)
    svc.delete("market",market.id)
    assert store.list("fees")==[]  # Market deletion cascades its fee record.
    store.close()

def test_network_scoped_relationships_are_checked_on_update_and_direct_store(tmp_path):
    store,svc=setup(tmp_path)
    n1=svc.add(Network(name="one",chain_id=1))
    n2=svc.add(Network(name="two",chain_id=2))
    contract=svc.add(Contract(name="pool",network_id=n1.id,address="0x"+"e"*40))
    token=svc.add(Token(name="T",symbol="T",network_id=n1.id,contract_id=contract.id,standard="ERC20"))
    asset1=svc.add(Asset(name="A",symbol="A")); asset2=svc.add(Asset(name="B",symbol="B"))
    pair=svc.add(TradingPair(base_asset_id=asset1.id,quote_asset_id=asset2.id))
    venue=svc.add(TradingVenue(name="DEX",venue_type="dex"))
    market=svc.add(Market(name="A-B",venue_id=venue.id,pair_id=pair.id,network_id=n1.id,pool_contract_id=contract.id))
    token.network_id=n2.id
    with pytest.raises(RelationshipError): svc.update(token)
    market.network_id=n2.id
    with pytest.raises(RelationshipError): store.update(market)
    store.close()

def test_metadata_cli_crud_confirmation_and_json_error(tmp_path):
    from trading_platform.metadata_cli import MetadataCLI
    inputs=iter(['{"name":"CLI Network","chain_id":777}', 'not-json'])
    output=[]
    adapter=MetadataCLI(tmp_path,{"storage":{"data_dir":"data"}},
                        input_fn=lambda prompt: next(inputs),output_fn=output.append)
    item=adapter.execute("network.add")
    assert adapter.service.get("network",item.id).name=="CLI Network"
    assert any("Created network" in line for line in output)
    with pytest.raises(MetadataError):
        adapter.execute("network.add")  # Malformed JSON is surfaced as a domain validation error.
    adapter.close()

def test_metadata_cli_delete_cancel_then_confirm(tmp_path):
    from trading_platform.metadata_cli import MetadataCLI
    adapter=MetadataCLI(tmp_path,{"storage":{"data_dir":"data"}},input_fn=lambda _: "",output_fn=lambda _: None)
    item=adapter.service.add(Network(name="CLI",chain_id=778))
    inputs=iter([item.id,"NO"])
    adapter.input=lambda prompt: next(inputs)
    adapter.execute("network.delete")
    assert adapter.service.get("network",item.id).name=="CLI"
    inputs=iter([item.id,"DELETE"])
    adapter.input=lambda prompt: next(inputs)
    adapter.execute("network.delete")
    with pytest.raises(NotFoundError): adapter.service.get("network",item.id)
    adapter.close()
