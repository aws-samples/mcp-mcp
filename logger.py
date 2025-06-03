import logging
import os
import datetime
import pathlib


class Logger:
    """
    ロギング機能を提供するクラス
    """
    
    def __init__(self, name="app", log_level=logging.INFO, log_dir=None):
        """
        ロガーをセットアップするコンストラクタ
        
        Args:
            name: ロガーの名前
            log_level: ログレベル (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
            log_dir: ログファイルを保存するディレクトリのパス (省略時はデフォルトの ./logs/ を使用)
        """
        self.logger = self._setup_logger(name, log_level, log_dir)
    
    def _setup_logger(self, name, log_level, log_dir=None):
        """
        ロガーをセットアップする内部メソッド
        
        Args:
            name: ロガーの名前
            log_level: ログレベル
            log_dir: ログファイルを保存するディレクトリのパス
        
        Returns:
            設定されたロガー
        """
        # このファイルのディレクトリパスを取得
        this_file_path = os.path.abspath(__file__)
        this_file_dir = os.path.dirname(this_file_path)
        
        # ログディレクトリの設定
        if log_dir is None:
            # デフォルトのログディレクトリ
            logs_dir = os.path.join(this_file_dir, "logs")
        else:
            # 指定されたログディレクトリ
            # 相対パスの場合は、このファイルからの相対パスとして解釈
            if not os.path.isabs(log_dir):
                logs_dir = os.path.join(this_file_dir, log_dir)
            else:
                logs_dir = log_dir
        
        # ログディレクトリが存在しない場合は作成
        pathlib.Path(logs_dir).mkdir(parents=True, exist_ok=True)
        
        # 今日の日付をファイル名に使用
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(logs_dir, f"{today}.log")
        
        # ロガーの設定
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # 既存のハンドラがある場合は削除（二重登録防止）
        if logger.handlers:
            logger.handlers.clear()
        
        # ファイルハンドラ（追記モード）
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(log_level)
        
        # コンソールハンドラ
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # フォーマッタ
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # ハンドラをロガーに追加
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    # 以下、標準的なロギングメソッドの委譲
    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        self.logger.exception(msg, *args, **kwargs)
    
    def log(self, level, msg, *args, **kwargs):
        self.logger.log(level, msg, *args, **kwargs)
    
    # ロガーインスタンスを直接取得するメソッド
    def get_logger(self):
        return self.logger


# 使用例
if __name__ == "__main__":
    # デフォルトのINFOレベルでロガーを作成
    logger = Logger("test_logger").get_logger()
    logger.info("This is a test log message")
    
    # または直接メソッドを使用
    log = Logger("direct_logger")
    log.info("This is a direct log message")
    log.debug("This debug message won't show with default INFO level")
    
    # DEBUGレベルでロガーを作成
    debug_logger = Logger("debug_logger", logging.DEBUG)
    debug_logger.debug("This debug message will show")
    
    # カスタムログディレクトリを指定
    custom_logger = Logger("custom_dir_logger", logging.INFO, "custom_logs")
    custom_logger.info("This log goes to ./custom_logs/ directory")
