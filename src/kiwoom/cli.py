import click
import json
import os
from kiwoom.config import ConfigManager
from kiwoom.client import KiwoomClient

def get_8_digit_acct_no(acct_no):
    if isinstance(acct_no, str) and len(acct_no) == 10 and acct_no.isdigit():
        return acct_no[:8]
    return acct_no

def format_currency(val):
    try:
        return f"{int(float(val)):,}"
    except (ValueError, TypeError):
        return val

def format_percent(val):
    try:
        val_float = float(val)
        sign = "+" if val_float > 0 else ""
        return f"{sign}{val_float:.2f}%"
    except (ValueError, TypeError):
        return val

def handle_error(ctx, error_msg, output_format):
    if output_format == "json":
        click.echo(json.dumps({"error": error_msg}, ensure_ascii=False), err=True)
    else:
        click.echo(f"Error: {error_msg}", err=True)
    ctx.exit(1)

@click.group()
@click.option("--config-dir", default=None, help="Directory path containing config.json")
@click.option("--account", "-a", required=False, help="Account alias to query (defined in config.json)")
@click.option("--format", "-f", default="text", type=click.Choice(["text", "json"]), help="Output format")
@click.pass_context
def main(ctx, config_dir, account, format):
    """Kiwoom REST API CLI Tool"""
    cm = ConfigManager(base_dir=config_dir)
    ctx.obj = {
        "account": account,
        "config_manager": cm,
        "format": format
    }

@main.command()
@click.option("--format", "-f", default=None, type=click.Choice(["text", "json"]), help="Output format override")
@click.pass_context
def info(ctx, format):
    """Enquire detailed account information of the alias(es)"""
    account_alias = ctx.obj.get("account")
    cm = ctx.obj["config_manager"]
    fmt = format if format is not None else ctx.obj.get("format", "text")

    aliases = [account_alias] if account_alias else cm.get_all_account_aliases()
    if not aliases:
        handle_error(ctx, "설정된 계좌 별칭이 없거나 config.json을 찾을 수 없습니다.", fmt)

    results = []
    for alias in aliases:
        try:
            client = KiwoomClient(account=alias, config_manager=cm)
            info_data = client.get_account_info()
            acct_no = info_data.get("acctNo")
            if acct_no and len(acct_no) == 10 and acct_no.isdigit():
                info_data["acctNo"] = get_8_digit_acct_no(acct_no)
            results.append((alias, info_data))
        except Exception as e:
            if account_alias:
                handle_error(ctx, str(e), fmt)
            results.append((alias, {"error": str(e)}))

    if fmt == "json":
        out_list = []
        for alias, data in results:
            out_list.append({
                "account_alias": alias,
                "account_info": data
            })
        if account_alias:
            click.echo(json.dumps(out_list[0], ensure_ascii=False))
        else:
            click.echo(json.dumps(out_list, ensure_ascii=False))
        return

    for idx, (alias, data) in enumerate(results):
        if idx > 0:
            click.echo("\n" + "-" * 50)
        if "error" in data:
            click.echo(f"=== [{alias}] 계좌 정보 조회 실패 ===")
            click.echo(f" 에러: {data['error']}")
            continue

        acct_no = data.get("acctNo")
        if not acct_no:
            click.echo(f"=== [{alias}] 계좌 정보 없음 ===")
            continue

        click.echo(f"=== [{alias}] 계좌 정보 ===")
        click.echo(f" 계좌번호: {acct_no}")
        
        acct_nm = data.get("acctNm")
        if acct_nm:
            click.echo(f" 계좌명: {acct_nm}")
            
        acct_tp_nm = data.get("acctTpNm")
        if acct_tp_nm:
            click.echo(f" 상품구분: {acct_tp_nm}")

@main.command()
@click.option("--format", "-f", default=None, type=click.Choice(["text", "json"]), help="Output format override")
@click.pass_context
def accounts(ctx, format):
    """List all registered account aliases and their actual account numbers"""
    account_alias = ctx.obj.get("account")
    cm = ctx.obj["config_manager"]
    fmt = format if format is not None else ctx.obj.get("format", "text")

    aliases = [account_alias] if account_alias else cm.get_all_account_aliases()
    if not aliases:
        handle_error(ctx, "설정된 계좌 별칭이 없거나 config.json을 찾을 수 없습니다.", fmt)

    results = []
    for alias in aliases:
        try:
            client = KiwoomClient(account=alias, config_manager=cm)
            accts = client.get_accounts()
            accts_8 = [get_8_digit_acct_no(a) for a in accts]
            results.append((alias, accts_8))
        except Exception as e:
            if account_alias:
                handle_error(ctx, str(e), fmt)
            results.append((alias, {"error": str(e)}))

    if fmt == "json":
        out_list = []
        for alias, data in results:
            if isinstance(data, dict) and "error" in data:
                out_list.append({
                    "account_alias": alias,
                    "error": data["error"]
                })
            else:
                acct_val = data[0] if data else ""
                out_list.append({
                    "account_alias": alias,
                    "acct_no": acct_val
                })
        if account_alias:
            click.echo(json.dumps(out_list[0], ensure_ascii=False))
        else:
            click.echo(json.dumps(out_list, ensure_ascii=False))
        return

    click.echo("=== 등록된 계좌 목록 ===")
    for idx, (alias, data) in enumerate(results, 1):
        if isinstance(data, dict) and "error" in data:
            click.echo(f" {idx}. 별칭: {alias:<12} | 에러: {data['error']}")
        else:
            acct_val = data[0] if data else "연결된 계좌 없음"
            click.echo(f" {idx}. 별칭: {alias:<12} | 계좌번호: {acct_val}")

@main.command()
@click.option("--acct", default=None, help="Specific actual account number to query")
@click.option("--format", "-f", default=None, type=click.Choice(["text", "json"]), help="Output format override")
@click.pass_context
def balances(ctx, acct, format):
    """Enquire portfolio balance and details of the account(s)"""
    account_alias = ctx.obj.get("account")
    cm = ctx.obj["config_manager"]
    fmt = format if format is not None else ctx.obj.get("format", "text")

    aliases = [account_alias] if account_alias else cm.get_all_account_aliases()
    if not aliases:
        handle_error(ctx, "설정된 계좌 별칭이 없거나 config.json을 찾을 수 없습니다.", fmt)

    results = []
    for alias in aliases:
        try:
            client = KiwoomClient(account=alias, config_manager=cm)
            res = client.get_balance(acct_no=acct)
            results.append((alias, res))
        except Exception as e:
            if account_alias:
                handle_error(ctx, str(e), fmt)
            results.append((alias, {"error": str(e)}))

    if fmt == "json":
        out_list = []
        for alias, res in results:
            if "error" in res:
                out_list.append({
                    "account": alias,
                    "acct_no": alias,
                    "balance": {"error": res["error"]}
                })
            else:
                out_list.append({
                    "account": alias,
                    "acct_no": res.get("acct_no", alias),
                    "balance": res
                })
        if account_alias:
            click.echo(json.dumps(out_list[0], ensure_ascii=False))
        else:
            click.echo(json.dumps(out_list, ensure_ascii=False))
        return

    for idx, (alias, res) in enumerate(results):
        if idx > 0:
            click.echo("\n" + "=" * 90)
        if "error" in res:
            click.echo(f"\n[{alias}] 계좌 잔고 조회 실패: {res['error']}")
            continue

        real_acct = res.get("acct_no", alias)
        acct_8 = get_8_digit_acct_no(real_acct)
        click.echo("\n" + "=" * 50)
        click.echo(f"  [{acct_8}] 계좌 평가 현황")
        click.echo("=" * 50)
        click.echo(f"계좌 번호   : {acct_8}")
        click.echo(f"추정예탁자산 : {format_currency(res.get('prsm_dpst_aset_amt'))} 원")
        click.echo(f"총 매입금액  : {format_currency(res.get('tot_pur_amt'))} 원")
        click.echo(f"총 평가금액  : {format_currency(res.get('tot_evlt_amt'))} 원")
        click.echo(f"총 평가손익  : {format_currency(res.get('tot_evlt_pl'))} 원")
        click.echo(f"총 수익률    : {format_percent(res.get('tot_prft_rt'))}")
        click.echo("=" * 50)

        holdings = res.get("acnt_evlt_remn_indv_tot", [])
        if not holdings:
            click.echo("\n보유 주식이 없습니다.")
            continue

        click.echo("\n" + "=" * 90)
        click.echo(f"  [{acct_8}] 보유 종목 현황")
        click.echo("=" * 90)
        click.echo(f"{'종목코드':<8} | {'종목명':<16} | {'보유수량':<8} | {'매입단가':<10} | {'현재가':<10} | {'평가손익':<12} | {'수익률':<8}")
        click.echo("-" * 90)
        
        for stock in holdings:
            code = stock.get("stk_cd", "").replace("A", "")
            name = stock.get("stk_nm", "")
            qty = f"{int(float(stock.get('rmnd_qty', 0)))} 주"
            pur_uv = f"{format_currency(stock.get('pur_pric'))} 원"
            cur_prc = f"{format_currency(stock.get('cur_prc'))} 원"
            pl_amt = format_currency(stock.get('evltv_prft'))
            pl_amt_str = f"+{pl_amt}" if float(stock.get('evltv_prft', 0)) > 0 else pl_amt
            pl_rt = format_percent(stock.get('prft_rt'))
            
            click.echo(f"{code:<8} | {name:<16} | {qty:<8} | {pur_uv:<10} | {cur_prc:<10} | {pl_amt_str:>12} | {pl_rt:>8}")
        click.echo("=" * 90)

if __name__ == "__main__":
    main()

