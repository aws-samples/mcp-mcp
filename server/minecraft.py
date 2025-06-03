from mcp.server.fastmcp import FastMCP
import subprocess
import os
import logging
import sys
import pathlib
import time
import json
import shlex

# 親ディレクトリをパスに追加して、logger.pyをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import Logger

# ロガーの初期化（デフォルトはINFO）
# ログレベルは必要に応じて変更可能: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = Logger("minecraft_tools", logging.INFO, "server/logs")

# MCP サーバーの初期化
try:
    mcp = FastMCP("minecraft")
    logger.info("FastMCP server initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize FastMCP server: {str(e)}")
    sys.exit(1)

# ファイルパスの設定
this_file_path = os.path.abspath(__file__)
this_file_dir = os.path.dirname(this_file_path)

# ツールスクリプトディレクトリの存在確認
tools_dir = os.path.join(this_file_dir, "tools")
if not os.path.exists(tools_dir):
    logger.critical(f"Tools directory not found: {tools_dir}")
    sys.exit(1)


@mcp.tool()
def capture():
    """
    This function takes a screenshot of Minecraft and returns the image file path.

    Args:
        None
    Returns:
        Screenshot file path
    """
    script_path = os.path.join(this_file_dir, "tools/capture.py")
    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = ["uv", "run", script_name]
    logger.info(f"Executing command: {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=script_dir,
        capture_output=True,
        text=True,
        timeout=30,  # 30秒のタイムアウト
    )
    logger.info(result.stderr)
    logger.info(result.stdout.strip())
    return result.stdout.strip()


@mcp.tool()
def getBlock(x: int, y: int, z: int) -> int:
    """
    Get the block type at the specified coordinates.

    Args:
        x: x coordinate, required, int
        y: y coordinate, required, int
        z: z coordinate, required, int

    Returns:
        Block type ID as an integer
    """
    # 入力値の検証
    try:
        # 整数型の検証
        for param_name, param_value in [("x", x), ("y", y), ("z", z)]:
            if not isinstance(param_value, int):
                error_msg = f"Parameter {param_name} must be an integer, got {type(param_value).__name__}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

        # y座標の範囲検証
        if y < 0 or y > 255:
            error_msg = f"y must be between 0 and 255, got {y}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/getBlock.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = ["uv", "run", script_name, "--x", str(x), "--y", str(y), "--z", str(z)]

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            try:
                return int(result.stdout.strip())
            except ValueError:
                return result.stdout.strip()
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return f"Error: {error_detail} - {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
def setBlock(x: int, y: int, z: int, blockType: int, blockData: int = None) -> str:
    """
    Set a block at the specified coordinates.

    Args:
        x: x coordinate, required, int
        y: y coordinate, required, int
        z: z coordinate, required, int
        blockType: type of block to set (0-255), required, int
        blockData: data value for the block (0-15), optional, int

    Returns:
        Result message
    """
    # 入力値の検証
    try:
        # 整数型の検証
        for param_name, param_value in [
            ("x", x),
            ("y", y),
            ("z", z),
            ("blockType", blockType),
        ]:
            if not isinstance(param_value, int):
                error_msg = f"Parameter {param_name} must be an integer, got {type(param_value).__name__}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

        # blockDataが指定されている場合は整数型の検証
        if blockData is not None and not isinstance(blockData, int):
            error_msg = f"Parameter blockData must be an integer, got {type(blockData).__name__}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        # blockType の範囲検証
        if blockType < 0 or blockType > 255:
            error_msg = f"blockType must be between 0 and 255, got {blockType}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        # blockData の範囲検証（指定されている場合）
        if blockData is not None and (blockData < 0 or blockData > 15):
            error_msg = f"blockData must be between 0 and 15, got {blockData}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        # y座標の範囲検証
        if y < 0 or y > 255:
            error_msg = f"y must be between 0 and 255, got {y}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/setBlock.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = [
        "uv",
        "run",
        script_name,
        "--x",
        str(x),
        "--y",
        str(y),
        "--z",
        str(z),
        "--blockType",
        str(blockType),
    ]
    if blockData is not None:
        command.extend(["--blockData", str(blockData)])

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return f"Error: {error_detail} - {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
def getPlayerPos(tile: bool = False) -> dict:
    """
    Get the player's current position.

    Args:
        tile: If True, get tile position instead of exact position, optional, bool

    Returns:
        Dictionary containing x, y, z coordinates
    """
    # 入力値の検証
    try:
        if not isinstance(tile, bool):
            error_msg = f"Parameter tile must be a boolean, got {type(tile).__name__}"
            logger.error(error_msg)
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/getPlayerPos.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return {"error": error_msg}

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = ["uv", "run", script_name]
    if tile:
        command.append("--tile")

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                error_msg = f"Failed to parse JSON response: {result.stdout.strip()}"
                logger.error(error_msg)
                return {"error": error_msg}
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return {"error": f"{error_detail} - {result.stderr.strip()}"}

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return {"error": error_msg}
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return {"error": error_msg}
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}


@mcp.tool()
def setBlocks(
    x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, blockType: int
) -> str:
    """
    A function that places Blocks within the range of a 3D bounding box specified by arguments (defined by coordinates 1(x,y,z) and 2(x,y,z)) in Minecraft.

    Args:
        x0: x value of coordinate 0, required , int
        y0: y value of coordinate 0, required , int
        z0: z value of coordinate 0, required , int
        x1: x value of coordinate 1, required , int
        y1: y value of coordinate 1, required , int
        z1: z value of coordinate 1, required , int
        BlockType: required
            Air is 0
            Stone is 1
            Grass is 2
            Dirt is 3
            Cobblestone is 4
            Oak Wood Plank is 5
            Oak Sapling is 6
            Bedrock is 7
            Flowing Water is 8
            Still Water is 9
            Flowing Lava is 10
            Still Lava is 11
            Sand is 12
            Gravel is 13
            Gold Ore is 14
            Iron Ore is 15
            Coal Ore is 16
            Oak Wood is 17
            Sponge is 19
            Glass is 20
            Lapis Lazuli Ore is 21
            Lapis Lazuli Block is 22
            Dispenser is 23
            Sandstone is 24
            Note Block is 25
            Bed is 26
            Powered Rail is 27
            Detector Rail is 28
            Sticky Piston is 29
            Cobweb is 30
            Dead Shrub is 31
            Dead Bush is 32
            Piston is 33
            Piston Head is 34
            White Wool is 35
            Dandelion is 37
            Poppy is 38
            Brown Mushroom is 39
            Red Mushroom is 40
            Gold Block is 41
            Iron Block is 42
            Double Stone Slab is 43
            Stone Slab is 44
            Bricks is 45
            TNT is 46
            Bookshelf is 47
            Moss Stone is 48
            Obsidian is 49
            Torch is 50
            Fire is 51
            Monster Spawner is 52
            Oak Wood Stairs is 53
            Chest is 54
            Redstone Wire is 55
            Diamond Ore is 56
            Diamond Block is 57
            Crafting Table is 58
            Wheat Crops is 59
            Farmland is 60
            Furnace is 61
            Burning Furnace is 62
            Standing Sign Block is 63
            Oak Door Block is 64
            Ladder is 65
            Rail is 66
            Cobblestone Stairs is 67
            Wallmounted Sign Block is 68
            Lever is 69
            Stone Pressure Plate is 70
            Iron Door Block is 71
            Wooden Pressure Plate is 72
            Redstone Ore is 73
            Glowing Redstone Ore is 74
            Redstone Torch Off is 75
            Redstone Torch On is 76
            Stone Button is 77
            Snow is 78
            Ice is 79
            Snow Block is 80
            Cactus is 81
            Clay is 82
            Sugar Canes is 83
            Jukebox is 84
            Oak Fence is 85
            Pumpkin is 86
            Netherrack is 87
            Soul Sand is 88
            Glowstone is 89
            Nether Portal is 90
            Jack O'Lantern is 91
            Cake Block is 92
            Redstone Repeater Block Off is 93
            Redstone Repeater Block On is 94
            White Stained Glass is 95
            Wooden Trapdoor is 96
            Stone Monster Egg is 97
            Stone Bricks is 98
            Brown Mushroom Block is 99
            Red Mushroom Block is 100
            Iron Bars is 101
            Glass Pane is 102
            Melon Block is 103
            Pumpkin Stem is 104
            Melon Stem is 105
            Vines is 106
            Oak Fence Gate is 107
            Brick Stairs is 108
            Stone Brick Stairs is 109
            Mycelium is 110
            Lily Pad is 111
            Nether Brick is 112
            Nether Brick Fence is 113
            Nether Brick Stairs is 114
            Nether Wart is 115
            Enchantment Table is 116
            Brewing Stand is 117
            Cauldron is 118
            End Portal is 119
            End Portal Frame is 120
            End Stone is 121
            Dragon Egg is 122
            Redstone Lamp Inactive is 123
            Redstone Lamp Active is 124
            Double Oak Wood Slab is 125
            Oak Wood Slab is 126
            Cocoa is 127
            Sandstone Stairs is 128
            Emerald Ore is 129
            Ender Chest is 130
            Tripwire Hook is 131
            Tripwire is 132
            Emerald Block is 133
            Spruce Wood Stairs is 134
            Birch Wood Stairs is 135
            Jungle Wood Stairs is 136
            Command Block is 137
            Beacon is 138
            Cobblestone Wall is 139
            Flower Pot is 140
            Carrots is 141
            Potatoes is 142
            Wooden Button is 143
            Mob Head is 144
            Anvil is 145
            Trapped Chest is 146
            Weighted Pressure Plate Light is 147
            Weighted Pressure Plate Heavy is 148
            Redstone Comparator Inactive is 149
            Redstone Comparator Active is 150
            Daylight Sensor is 151
            Redstone Block is 152
            Nether Quartz Ore is 153
            Hopper is 154
            Quartz Block is 155
            Quartz Stairs is 156
            Activator Rail is 157
            Dropper is 158
            White Hardened Clay is 159
            White Stained Glass Pane is 160
            Acacia Leaves is 161
            Acacia Wood is 162
            Acacia Wood Stairs is 163
            Dark Oak Wood Stairs is 164
            Slime Block is 165
            Barrier is 166
            Iron Trapdoor is 167
            Prismarine is 168
            Sea Lantern is 169
            Hay Bale is 170
            White Carpet is 171
            Hardened Clay is 172
            Block of Coal is 173
            Packed Ice is 174
            Sunflower is 175
            Freestanding Banner is 176
            Wallmounted Banner is 177
            Inverted Daylight Sensor is 178
            Red Sandstone is 179
            Red Sandstone Stairs is 180
            Double Red Sandstone Slab is 181
            Red Sandstone Slab is 182
            Spruce Fence Gate is 183
            Birch Fence Gate is 184
            Jungle Fence Gate is 185
            Dark Oak Fence Gate is 186
            Acacia Fence Gate is 187
            Spruce Fence is 188
            Birch Fence is 189
            Jungle Fence is 190
            Dark Oak Fence is 191
            Acacia Fence is 192
            Spruce Door Block is 193
            Birch Door Block is 194
            Jungle Door Block is 195
            Acacia Door Block is 196
            Dark Oak Door Block is 197
            End Rod is 198
            Chorus Plant is 199
            Chorus Flower is 200
            Purpur Block is 201
            Purpur Pillar is 202
            Purpur Stairs is 203
            Purpur Double Slab is 204
            Purpur Slab is 205
            End Stone Bricks is 206
            Beetroot Block is 207
            Grass Path is 208
            End Gateway is 209
            Repeating Command Block is 210
            Chain Command Block is 211
            Frosted Ice is 212
            Magma Block is 213
            Nether Wart Block is 214
            Red Nether Brick is 215
            Bone Block is 216
            Structure Void is 217
            Observer is 218
            White Shulker Box is 219
            Orange Shulker Box is 220
            Magenta Shulker Box is 221
            Light Blue Shulker Box is 222
            Yellow Shulker Box is 223
            Lime Shulker Box is 224
            Pink Shulker Box is 225
            Gray Shulker Box is 226
            Light Gray Shulker Box is 227
            Cyan Shulker Box is 228
            Purple Shulker Box is 229
            Blue Shulker Box is 230
            Brown Shulker Box is 231
            Green Shulker Box is 232
            Red Shulker Box is 233
            Black Shulker Box is 234
            White Glazed Terracotta is 235
            Orange Glazed Terracotta is 236
            Magenta Glazed Terracotta is 237
            Light Blue Glazed Terracotta is 238
            Yellow Glazed Terracotta is 239
            Lime Glazed Terracotta is 240
            Pink Glazed Terracotta is 241
            Gray Glazed Terracotta is 242
            Light Gray Glazed Terracotta is 243
            Cyan Glazed Terracotta is 244
            Purple Glazed Terracotta is 245
            Blue Glazed Terracotta is 246
            Brown Glazed Terracotta is 247
            Green Glazed Terracotta is 248
            Red Glazed Terracotta is 249
            Black Glazed Terracotta is 250
            White Concrete is 251
            White Concrete Powder is 252
            Structure Block is 255

    Returns:
        result text
    """
    # 入力値の検証
    try:
        # 整数型の検証
        for param_name, param_value in [
            ("x0", x0),
            ("y0", y0),
            ("z0", z0),
            ("x1", x1),
            ("y1", y1),
            ("z1", z1),
            ("blockType", blockType),
        ]:
            if not isinstance(param_value, int):
                error_msg = f"Parameter {param_name} must be an integer, got {type(param_value).__name__}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

        # blockType の範囲検証
        if blockType < 0 or blockType > 255:
            error_msg = f"blockType must be between 0 and 255, got {blockType}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/setBlocks.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = [
        "uv",
        "run",
        script_name,
        "--x0",
        str(x0),
        "--y0",
        str(y0),
        "--z0",
        str(z0),
        "--x1",
        str(x1),
        "--y1",
        str(y1),
        "--z1",
        str(z1),
        "--blockType",
        str(blockType),
    ]

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return f"Error: {error_detail} - {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


# サーバー起動時の健全性チェック
def check_environment():
    """環境の健全性をチェックする"""
    try:
        # uvコマンドが利用可能かチェック
        result = subprocess.run(["which", "uv"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(
                "uv command not found. Make sure it's installed and in PATH."
            )
            print(
                "Warning: uv command not found. Make sure it's installed and in PATH."
            )

        # ツールスクリプトの存在確認
        tools_path = os.path.join(this_file_dir, "tools")
        if not os.path.exists(tools_path):
            logger.error(f"Tools directory not found: {tools_path}")
            print(f"Error: Tools directory not found: {tools_path}")
            return False

        setblocks_path = os.path.join(tools_path, "setBlocks.py")
        if not os.path.exists(setblocks_path):
            logger.error(f"setBlocks.py script not found: {setblocks_path}")
            print(f"Error: setBlocks.py script not found: {setblocks_path}")
            return False

        # mcpiライブラリが利用可能かチェック
        try:
            import importlib.util

            if importlib.util.find_spec("mcpi") is None:
                logger.warning("mcpi library not found. Make sure it's installed.")
                print("Warning: mcpi library not found. Make sure it's installed.")
        except ImportError:
            logger.warning("Could not check for mcpi library.")
            print("Warning: Could not check for mcpi library.")

        return True
    except Exception as e:
        logger.error(f"Error during environment check: {str(e)}")
        print(f"Error during environment check: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        # 環境チェック
        if not check_environment():
            logger.critical(
                "Environment check failed. Some features may not work correctly."
            )
            print(
                "Critical: Environment check failed. Some features may not work correctly."
            )

        logger.info("Starting Minecraft Tool Server")
        print("Starting Minecraft Tool Server...")

        # サーバー起動
        mcp.run(transport="stdio")

        logger.info("Minecraft Tool Server stopped")
        print("Minecraft Tool Server stopped")
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
        print("\nServer stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Critical error in server: {str(e)}")
        print(f"Critical error: {str(e)}")
        import traceback

        logger.critical(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


@mcp.tool()
def setPlayerPos(x: float, y: float, z: float, tile: bool = False) -> str:
    """
    Set the player's position.

    Args:
        x: x coordinate, required, float
        y: y coordinate, required, float
        z: z coordinate, required, float
        tile: If True, set tile position instead of exact position, optional, bool

    Returns:
        Result message
    """
    # 入力値の検証
    try:
        # 数値型の検証
        for param_name, param_value in [("x", x), ("y", y), ("z", z)]:
            if not isinstance(param_value, (int, float)):
                error_msg = f"Parameter {param_name} must be a number, got {type(param_value).__name__}"
                logger.error(error_msg)
                return f"Error: {error_msg}"

        # tile パラメータの検証
        if not isinstance(tile, bool):
            error_msg = f"Parameter tile must be a boolean, got {type(tile).__name__}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

        # y座標の範囲検証
        if y < 0 or y > 255:
            error_msg = f"y must be between 0 and 255, got {y}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/setPlayerPos.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = ["uv", "run", script_name, "--x", str(x), "--y", str(y), "--z", str(z)]
    if tile:
        command.append("--tile")

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return f"Error: {error_detail} - {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
def postToChat(message: str) -> str:
    """
    Post a message to the Minecraft chat.

    Args:
        message: Message to post to chat, required, str

    Returns:
        Result message
    """
    # 入力値の検証
    try:
        if not isinstance(message, str):
            error_msg = (
                f"Parameter message must be a string, got {type(message).__name__}"
            )
            logger.error(error_msg)
            return f"Error: {error_msg}"

        if not message:
            error_msg = "Message cannot be empty"
            logger.error(error_msg)
            return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/postToChat.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = ["uv", "run", script_name, "--message", message]

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(repr(arg) for arg in command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            return result.stdout.strip()
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return f"Error: {error_detail} - {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"


@mcp.tool()
def getHeight(x: int, z: int) -> int:
    """
    Get the height of the highest non-air block at the specified x,z coordinates.

    Args:
        x: x coordinate, required, int
        z: z coordinate, required, int

    Returns:
        Height (y-coordinate) as an integer
    """
    # 入力値の検証
    try:
        # 整数型の検証
        for param_name, param_value in [("x", x), ("z", z)]:
            if not isinstance(param_value, int):
                error_msg = f"Parameter {param_name} must be an integer, got {type(param_value).__name__}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
    except Exception as e:
        error_msg = f"Parameter validation error: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    # スクリプトパスの設定と検証
    script_path = os.path.join(this_file_dir, "tools/getHeight.py")
    if not os.path.exists(script_path):
        error_msg = f"Script not found: {script_path}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

    script_dir = os.path.dirname(script_path)
    script_name = os.path.basename(script_path)

    # コマンドの構築
    command = ["uv", "run", script_name, "--x", str(x), "--z", str(z)]

    # コマンドの実行をログに記録
    logger.info(f"Executing command: {' '.join(command)}")

    # コマンド実行とエラーハンドリング
    try:
        # タイムアウト設定付きでコマンド実行
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 30秒のタイムアウト
        )

        # 実行結果の処理
        if result.returncode == 0:
            logger.info(f"Command executed successfully: {result.stdout.strip()}")
            try:
                return int(result.stdout.strip())
            except ValueError:
                return result.stdout.strip()
        else:
            error_msg = f"Command failed with return code {result.returncode}: {result.stderr.strip()}"
            logger.error(error_msg)

            # エラーコードに基づいた詳細なエラーメッセージ
            error_details = {
                1: "Invalid value provided",
                2: "Connection error to Minecraft server",
                3: "Invalid argument",
                4: "Unexpected error in script execution",
            }

            error_detail = error_details.get(result.returncode, "Unknown error")
            return f"Error: {error_detail} - {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        error_msg = "Command execution timed out after 30 seconds"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except FileNotFoundError:
        error_msg = f"Command not found: {command.split()[0]}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except PermissionError:
        error_msg = "Permission denied when executing the command"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    except Exception as e:
        # その他の例外が発生した場合はエラーログを記録
        error_msg = f"Exception occurred while executing command: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
