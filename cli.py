import click
import os
from config import ConfigManager
from client import KiwoomClient

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

@click.group()
@click.option("--config-dir", default=None, help="Directory path containing config.json")
@click.option("--user", "-u", required=True, help="User ID to query")
@click.pass_context
def main(ctx, config_dir, user):
    """Kiwoom REST API CLI Tool"""
    # config manager 초기화 및 context 전달
    cm = ConfigManager(base_dir=config_dir)
    ctx.obj = {
        "user_id": user,
        "config_manager": cm
    }

@main.command()
@click.pass_context
def accounts(ctx):
    """Enquire accounts connected to the user token"""
    user_id = ctx.obj["user_id"]
    cm = ctx.obj["config_manager"]
    client = KiwoomClient(user_id=user_id, config_manager=cm)
    
    try:
        accts = client.get_accounts()
        click.echo(f"=== [{user_id}] 계좌 목록 ===")
        for idx, acct in enumerate(accts, 1):
            click.echo(f" {idx}. 계좌번호: {acct}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)

@main.command()
@click.option("--acct", default=None, help="Specific account number to query")
@click.pass_context
def balance(ctx, acct):
    """Enquire portfolio balance and details of the account"""
    user_id = ctx.obj["user_id"]
    cm = ctx.obj["config_manager"]
    client = KiwoomClient(user_id=user_id, config_manager=cm)

    try:
        # 계좌 지정이 안되었으면 첫 계좌 자동 선택
        if not acct:
            accts = client.get_accounts()
            if not accts:
                click.echo("Error: 연결된 계좌가 없습니다.", err=True)
                return
            acct = accts[0]

        res = client.get_balance(acct)
        
        click.echo("\n" + "=" * 50)
        click.echo(f"  [{user_id}] 계좌 평가 현황")
        click.echo("=" * 50)
        click.echo(f"계좌 번호   : {acct}")
        click.echo(f"추정예탁자산 : {format_currency(res.get('prsm_dpst_aset_amt'))} 원")
        click.echo(f"총 매입금액  : {format_currency(res.get('tot_pur_amt'))} 원")
        click.echo(f"총 평가금액  : {format_currency(res.get('tot_evlt_amt'))} 원")
        click.echo(f"총 평가손익  : {format_currency(res.get('tot_evlt_pl'))} 원")
        click.echo(f"총 수익률    : {format_percent(res.get('tot_prft_rt'))}")
        click.echo("=" * 50)

        holdings = res.get("stk_cntr_remn", [])
        if not holdings:
            click.echo("\n보유 주식이 없습니다.")
            return

        click.echo("\n" + "=" * 90)
        click.echo(f"  [{user_id}] 보유 종목 현황")
        click.echo("=" * 90)
        # 테이블 헤더 포맷팅
        click.echo(f"{'종목코드':<8} | {'종목명':<16} | {'보유수량':<8} | {'매입단가':<10} | {'현재가':<10} | {'평가손익':<12} | {'수익률':<8}")
        click.echo("-" * 90)
        
        for stock in holdings:
            code = stock.get("stk_cd", "").replace("A", "") # 접두사 'A' 제거하여 표시
            name = stock.get("stk_nm", "")
            qty = f"{int(float(stock.get('rmnd_qty', 0)))} 주"
            pur_uv = f"{format_currency(stock.get('pur_pric'))} 원"
            cur_prc = f"{format_currency(stock.get('cur_prc'))} 원"
            pl_amt = format_currency(stock.get('evltv_prft'))
            pl_amt_str = f"+{pl_amt}" if float(stock.get('evltv_prft', 0)) > 0 else pl_amt
            pl_rt = format_percent(stock.get('pl_rt'))
            
            click.echo(f"{code:<8} | {name:<16} | {qty:<8} | {pur_uv:<10} | {cur_prc:<10} | {pl_amt_str:>12} | {pl_rt:>8}")
        click.echo("=" * 90)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)

if __name__ == "__main__":
    main()
