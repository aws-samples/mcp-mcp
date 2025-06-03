import argparse
import sys
import time
from mcpi.minecraft import Minecraft

def validate_args(args):
    """引数の検証を行う"""
    # blockTypeの範囲チェック
    if args.blockType < 0 or args.blockType > 255:
        raise ValueError(f"blockTypeは0以上255以下の整数である必要があります。指定値: {args.blockType}")
    
    # 座標の範囲チェック（Minecraftの世界の制限に基づく）
    # 一般的なMinecraftの座標範囲は-30,000,000から30,000,000程度
    coord_limit = 30000000
    for name, value in [
        ('x0', args.x0), ('y0', args.y0), ('z0', args.z0),
        ('x1', args.x1), ('y1', args.y1), ('z1', args.z1)
    ]:
        if abs(value) > coord_limit:
            raise ValueError(f"{name}の値が範囲外です。-{coord_limit}から{coord_limit}の間である必要があります。指定値: {value}")
    
    # y座標は通常0-255の範囲
    for name, value in [('y0', args.y0), ('y1', args.y1)]:
        if value < 0 or value > 255:
            raise ValueError(f"{name}の値が範囲外です。0から255の間である必要があります。指定値: {value}")

def connect_to_minecraft(max_retries=3, retry_delay=2):
    """Minecraftサーバーへの接続を試みる（リトライ機能付き）"""
    for attempt in range(max_retries):
        try:
            mc = Minecraft.create()
            return mc
        except ConnectionRefusedError:
            if attempt < max_retries - 1:
                print(f"接続が拒否されました。{retry_delay}秒後に再試行します... ({attempt+1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                raise ConnectionError("Minecraftサーバーへの接続が拒否されました。サーバーが起動しているか確認してください。")
        except Exception as e:
            raise ConnectionError(f"Minecraftサーバーへの接続中にエラーが発生しました: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='指定された3D範囲にブロックを設置します。',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 座標の開始点を定義
    parser.add_argument('--x0', type=int, required=True, help='X coordinate of the starting point')
    parser.add_argument('--y0', type=int, required=True, help='Y coordinate of the starting point')
    parser.add_argument('--z0', type=int, required=True, help='Z coordinate of the starting point')
    
    # 座標の終了点を定義
    parser.add_argument('--x1', type=int, required=True, help='X coordinate of the ending point')
    parser.add_argument('--y1', type=int, required=True, help='Y coordinate of the ending point')
    parser.add_argument('--z1', type=int, required=True, help='Z coordinate of the ending point')
    
    # ブロックタイプを定義
    parser.add_argument('--blockType', type=int, required=True, help='Type of block to set (0-255)')
    
    try:
        # 引数のパース
        args = parser.parse_args()
        
        # 引数の検証
        validate_args(args)
        
        # Minecraftサーバーに接続
        mc = connect_to_minecraft()
        
        # ブロックを設置
        mc.setBlocks(args.x0, args.y0, args.z0, args.x1, args.y1, args.z1, args.blockType)
        
        # 成功メッセージを標準出力に出力
        success_msg = f"ブロック(ID: {args.blockType})を ({args.x0},{args.y0},{args.z0}) から ({args.x1},{args.y1},{args.z1}) の範囲に設置しました"
        print(success_msg)
        return 0
              
    except ValueError as e:
        print(f"エラー: 値が無効です - {e}", file=sys.stderr)
        return 1
    except ConnectionError as e:
        print(f"接続エラー: {e}", file=sys.stderr)
        return 2
    except argparse.ArgumentError as e:
        print(f"引数エラー: {e}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("処理が中断されました", file=sys.stderr)
        return 130
    except MemoryError:
        print("メモリ不足エラー: 処理範囲が大きすぎる可能性があります", file=sys.stderr)
        return 137
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 4

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
