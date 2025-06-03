import sys, os
# 親ディレクトリをパスに追加して、logger.pyをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
from logger import Logger
import json
import argparse
from strands.tools.mcp import MCPClient
from strands import Agent
from contextlib import ExitStack
from mcp import stdio_client, StdioServerParameters
from tools import capture
from strands_tools import image_reader
import traceback

# ロガーの初期化 - クライアント用のログディレクトリを指定
logger = Logger("mcp_client", logging.INFO, "client/logs")

def parse_arguments():
    """コマンドライン引数を解析する"""
    parser = argparse.ArgumentParser(description="Minecraft Agent Client")
    parser.add_argument('--mcp', type=str, help='mcp.json のパス')
    
    # 引数が指定されていない場合のヘルプ表示
    if len(sys.argv) == 1:
        parser.print_help()
        logger.warning("コマンドライン引数が指定されていません。--mcp オプションが必要です。")
        sys.exit(1)
        
    args = parser.parse_args()
    logger.debug(f"コマンドライン引数: mcp={args.mcp}")
    return args

def load_mcp_clients():
    """MCP設定ファイルからクライアントを読み込む"""
    args = parse_arguments()
    
    # MCPファイルパスが指定されていない場合のエラーハンドリング
    if args.mcp is None:
        logger.error("MCP設定ファイルが指定されていません。--mcp オプションを使用してください")
        raise ValueError("MCP設定ファイルが指定されていません。--mcp オプションを使用してください")
    
    logger.info(f"MCP設定ファイル '{args.mcp}' を読み込み中...")
    
    try:
        with open(args.mcp, 'r') as f:
            mcp_json = json.load(f)
            
        # mcpServersキーの存在確認
        if "mcpServers" not in mcp_json:
            logger.error("MCP設定ファイルに 'mcpServers' キーがありません")
            raise KeyError("MCP設定ファイルに 'mcpServers' キーがありません")
            
        mcp_settings = mcp_json["mcpServers"]
        
        # サーバー設定が空の場合のエラーハンドリング
        if not mcp_settings:
            logger.error("MCP設定ファイルにサーバー設定がありません")
            raise ValueError("MCP設定ファイルにサーバー設定がありません")
        
        logger.debug(f"MCP設定: {len(mcp_settings)} サーバーが見つかりました")
        
        mcp_clients = []
        for key in mcp_settings.keys():
            logger.debug(f"MCPクライアント '{key}' を初期化中...")
            
            # 必要なキーの存在確認
            if "command" not in mcp_settings[key]:
                logger.error(f"サーバー '{key}' に 'command' キーがありません")
                raise KeyError(f"サーバー '{key}' に 'command' キーがありません")
                
            if "args" not in mcp_settings[key]:
                logger.error(f"サーバー '{key}' に 'args' キーがありません")
                raise KeyError(f"サーバー '{key}' に 'args' キーがありません")
            
            try:
                mcp_client = MCPClient(
                    lambda key=key: stdio_client(
                        StdioServerParameters(
                            command=mcp_settings[key]["command"], 
                            args=mcp_settings[key]["args"]
                        )
                    )
                )
                mcp_clients.append(mcp_client)
                logger.debug(f"MCPクライアント '{key}' の初期化完了")
            except Exception as e:
                logger.error(f"MCPクライアント '{key}' の初期化中にエラーが発生しました: {e}")
                raise RuntimeError(f"MCPクライアント '{key}' の初期化に失敗しました: {e}")
        
        # クライアントが1つも初期化できなかった場合のエラーハンドリング
        if not mcp_clients:
            logger.error("有効なMCPクライアントが初期化できませんでした")
            raise RuntimeError("有効なMCPクライアントが初期化できませんでした")
            
        logger.info(f"{len(mcp_clients)}個のMCPクライアントを読み込みました")
        return mcp_clients
    except FileNotFoundError:
        logger.error(f"MCP設定ファイル '{args.mcp}' が見つかりません")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"MCP設定ファイル '{args.mcp}' の解析に失敗しました: {e}")
        raise
    except KeyError as e:
        logger.error(f"MCP設定ファイルに必要なキー '{e}' がありません")
        raise
    except Exception as e:
        logger.error(f"MCP設定ファイルの読み込み中に予期せぬエラーが発生しました: {e}")
        raise

def strands_callback_handler(**kwargs):
    """Strandsからのコールバックを処理する"""
    if "data" in kwargs:
        # 生成されたテキストをリアルタイムで表示（ログには記録するが、重複表示はしない）
        print(kwargs['data'], end='', flush=True)
        logger.debug(f"Strands出力: {kwargs['data']}")
    elif "current_tool_use" in kwargs:
        tool = kwargs["current_tool_use"]
        tool_name = tool.get('name', 'unknown')
        # ツール名が変わった場合のみ表示する
        if not hasattr(strands_callback_handler, 'last_tool') or strands_callback_handler.last_tool != tool_name:
            print(f"\n[ツール使用中: {tool_name}]", flush=True)
            strands_callback_handler.last_tool = tool_name
            logger.debug(f"Strandsツール使用: {tool_name}")


def main():
    """メイン処理"""
    try:
        logger.info("MCPクライアントを読み込み中...")
        mcp_clients = load_mcp_clients()
        
        with ExitStack() as stack:
            logger.info("クライアントコンテキストを設定中...")
            clients = []
            
            # クライアントコンテキストの設定とエラーハンドリング
            for i, mcp_client in enumerate(mcp_clients):
                try:
                    client = stack.enter_context(mcp_client)
                    clients.append(client)
                    logger.debug(f"クライアント {i+1}/{len(mcp_clients)} のコンテキスト設定完了")
                except Exception as e:
                    logger.error(f"クライアント {i+1}/{len(mcp_clients)} のコンテキスト設定に失敗しました: {e}")
            
            # クライアントが1つも設定できなかった場合はエラー
            if not clients:
                logger.critical("有効なクライアントが設定できませんでした")
                raise RuntimeError("有効なクライアントが設定できませんでした")
            
            logger.info("ツールを準備中...")
            tools = [capture, image_reader]
            
            # クライアントからツールを取得
            for i, client in enumerate(clients):
                try:
                    logger.debug(f"クライアント {i+1}/{len(clients)} からツールを取得中...")
                    client_tools = client.list_tools_sync()
                    tools.extend(client_tools)
                    logger.debug(f"{len(client_tools)}個のツールを追加しました")
                except Exception as e:
                    logger.error(f"クライアント {i+1}/{len(clients)} からツールの取得に失敗しました: {e}")
            
            # ツールが取得できなかった場合の警告
            if len(tools) <= 2:  # capture と image_reader だけの場合
                logger.warning("Minecraftツールが取得できませんでした。基本ツールのみで実行します。")
            
            logger.info(f"合計{len(tools)}個のツールを使用可能")
            
            try:
                logger.info("Agentを初期化中...")
                agent = Agent(
                    system_prompt = """
You are a professional at creating structures in Minecraft. Please use the given tools to meet user requests.
However, user requests may be rough and lack information. In such cases, proceed by assuming what the user wants as a professional.
Before starting work, during work, and at the end, please use the capture tool and image_reader, setPlayerPos tools to understand the situation in the Minecraft field.
Since the player's perspective is fixed in a bird's-eye view, it is important to check if everything looks appropriate from above. 
Frequent checks improve the accuracy of your work, so they need to be done often.
""",
                    tools = tools,
                    callback_handler=strands_callback_handler
                )
                
                # インタラクティブチャットループを開始
                print("\n=== Minecraft Builder /w Strands Agents チャットを開始します ===")
                print("終了するには 'exit' または 'quit' と入力してください\n")
                
                # ツール使用状態をリセット
                if hasattr(strands_callback_handler, 'last_tool'):
                    delattr(strands_callback_handler, 'last_tool')
                
                while True:
                    # ユーザー入力を受け取る
                    message = input("\n> ")
                    
                    # 終了コマンドのチェック
                    if message.lower() in ['exit', 'quit']:
                        print("チャットを終了します。")
                        break
                    
                    if not message.strip():
                        print("入力が空です。何か指示を入力してください。")
                        continue
                    
                    logger.info("ユーザーリクエストを処理中...")
                    logger.debug(f"リクエスト内容: {message.strip()}")
                    
                    # 各リクエスト開始時にツール使用状態をリセット
                    if hasattr(strands_callback_handler, 'last_tool'):
                        delattr(strands_callback_handler, 'last_tool')
                    
                    # エージェントの実行とエラーハンドリング
                    try:
                        print("\n処理中...")
                        # response.message は表示しない（コールバックハンドラーで既に表示されている）
                        response = agent(message)
                        print("\n処理が完了しました")
                        logger.info("処理が完了しました")
                    except Exception as e:
                        logger.error(f"エージェントの実行中にエラーが発生しました: {e}")
                        print(f"エラーが発生しました: {e}")
                
                return "チャットセッションが終了しました"
            except Exception as e:
                logger.error(f"Agentの初期化に失敗しました: {e}")
                raise
    except Exception as e:
        logger.critical(f"メイン処理でエラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    logger.info("Minecraft Agent 開始...")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("ユーザーによって処理が中断されました")
        print("\nプログラムが中断されました。終了します...")
        sys.exit(130)
    except FileNotFoundError as e:
        logger.critical(f"ファイルが見つかりません: {e}")
        print(f"エラー: ファイルが見つかりません - {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.critical(f"JSONの解析に失敗しました: {e}")
        print(f"エラー: JSONの解析に失敗しました - {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"値が無効です: {e}")
        print(f"エラー: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.critical(f"必要なキーがありません: {e}")
        print(f"エラー: 設定ファイルに必要なキーがありません - {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.critical(f"実行時エラー: {e}")
        print(f"エラー: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"予期せぬエラーが発生しました: {e}")
        print(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
