import argparse
import sys
import time
import json
from mcpi.minecraft import Minecraft

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
        description='プレイヤーの現在位置を取得します。',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 位置タイプを定義（通常の位置またはタイル位置）
    parser.add_argument('--tile', action='store_true', help='Get tile position instead of exact position')
    
    try:
        # 引数のパース
        args = parser.parse_args()
        
        # Minecraftサーバーに接続
        mc = connect_to_minecraft()
        
        # プレイヤーの位置を取得
        if args.tile:
            pos = mc.player.getTilePos()
        else:
            pos = mc.player.getPos()
        
        # 結果をJSON形式で標準出力に出力
        result = {
            "x": pos.x,
            "y": pos.y,
            "z": pos.z
        }
        print(json.dumps(result))
        return 0
              
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
