import argparse
import sys
import time
from mcpi.minecraft import Minecraft

def validate_args(args):
    """引数の検証を行う"""
    # 座標の範囲チェック（Minecraftの世界の制限に基づく）
    # 一般的なMinecraftの座標範囲は-30,000,000から30,000,000程度
    coord_limit = 30000000
    for name, value in [('x', args.x), ('y', args.y), ('z', args.z)]:
        if abs(value) > coord_limit:
            raise ValueError(f"{name}の値が範囲外です。-{coord_limit}から{coord_limit}の間である必要があります。指定値: {value}")
    
    # y座標は通常0-255の範囲
    if args.y < 0 or args.y > 255:
        raise ValueError(f"yの値が範囲外です。0から255の間である必要があります。指定値: {args.y}")

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
        description='指定された座標のブロックタイプを取得します。',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 座標を定義
    parser.add_argument('--x', type=int, required=True, help='X coordinate')
    parser.add_argument('--y', type=int, required=True, help='Y coordinate')
    parser.add_argument('--z', type=int, required=True, help='Z coordinate')
    
    try:
        # 引数のパース
        args = parser.parse_args()
        
        # 引数の検証
        validate_args(args)
        
        # Minecraftサーバーに接続
        mc = connect_to_minecraft()
        
        # ブロックタイプを取得
        block_type = mc.getBlock(args.x, args.y, args.z)
        
        # 結果を標準出力に出力
        print(block_type)
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
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 4

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
