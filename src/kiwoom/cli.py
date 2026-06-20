import click
import json
import os
from kiwoom.config import ConfigManager
from kiwoom.client import KiwoomClient

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
@click.option("--account", "-a", required=True, help="Account alias to query (defined in config.json)")
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
@click.pass_context
def account(ctx):
    """Enquire the actual account number of the alias"""
    account_alias = ctx.obj["account"]
    cm = ctx.obj["config_manager"]
    fmt = ctx.obj.get("format", "text")
    client = KiwoomClient(account=account_alias, config_manager=cm)

    try:
        accts = client.get_accounts()
        if not accts:
            handle_error(ctx, "연결된 실제 계좌가 없습니다.", fmt)
        if fmt == "json":
            click.echo(json.dumps({"account_alias": account_alias, "accounts": accts}, ensure_ascii=False))
        else:
            click.echo(f"=== [{account_alias}] 실제 계좌 목록 ===")
            for idx, acct in enumerate(accts, 1):
                click.echo(f" {idx}. 계좌번호: {acct}")
    except Exception as e:
        handle_error(ctx, str(e), fmt)

@main.command()
@click.option("--acct", default=None, help="Specific actual account number to query")
@click.pass_context
def balance(ctx, acct):
    """Enquire portfolio balance and details of the account"""
    account_alias = ctx.obj["account"]
    cm = ctx.obj["config_manager"]
    fmt = ctx.obj.get("format", "text")
    client = KiwoomClient(account=account_alias, config_manager=cm)

    try:
        res = client.get_balance(acct_no=acct)
        real_acct = res.get("acct_no", account_alias)
        
        if fmt == "json":
            out = {
                "account": account_alias,
                "acct_no": real_acct,
                "balance": res
            }
            click.echo(json.dumps(out, ensure_ascii=False))
            return

        click.echo("\n" + "=" * 50)
        click.echo(f"  [{real_acct}] 계좌 평가 현황")
        click.echo("=" * 50)
        click.echo(f"계좌 번호   : {real_acct}")
        click.echo(f"추정예탁자산 : {format_currency(res.get('prsm_dpst_aset_amt'))} 원")
        click.echo(f"총 매입금액  : {format_currency(res.get('tot_pur_amt'))} 원")
        click.echo(f"총 평가금액  : {format_currency(res.get('tot_evlt_amt'))} 원")
        click.echo(f"총 평가손익  : {format_currency(res.get('tot_evlt_pl'))} 원")
        click.echo(f"총 수익률    : {format_percent(res.get('tot_prft_rt'))}")
        click.echo("=" * 50)

        holdings = res.get("acnt_evlt_remn_indv_tot", [])
        if not holdings:
            click.echo("\n보유 주식이 없습니다.")
            return

        click.echo("\n" + "=" * 90)
        click.echo(f"  [{real_acct}] 보유 종목 현황")
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

    except Exception as e:
        handle_error(ctx, str(e), fmt)

if __name__ == "__main__":
    main()

